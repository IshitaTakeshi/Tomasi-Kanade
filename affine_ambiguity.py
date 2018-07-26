import chainer
from chainer import cuda
from chainer import variable
from chainer import initializers
from chainer.training import extensions
from chainer.training.updaters import StandardUpdater


class AffineTransformation(chainer.Chain):
    def __init__(self, initialQ=None):
        super(AffineTransformation, self).__init__()
        with self.init_scope():
            Q_initializer = initializers._get_initializer(initialQ)
            self.Q = variable.Parameter(Q_initializer)
            self.Q.initialize((3, 3))

    def __call__(self, M):
        xp = cuda.get_array_module(M.data)
        M = xp.array([xp.dot(M_, self.Q) for M_ in M])
        return variable.Variable(M)

    def get_loss_func(self):
        """
        The reprojection error defined as:

        .. math::
            \\frac{1}{F}
            \\sum_{f=1}^{F} ||M_{f}QQ^{\\top}M^{\\top} - I||^{2}_{F}

        where :math:`||\cdot||_F` denotes the Frobenious norm and
        :math:`M_{f}` is a motion matrix of the :math:`f`-th view.

        Args:
            M: Motion matrix of shape (n_views * 2, n_image_points)
            Q: The affine matrix of shape (3, 3)
        """

        def f(M):
            xp = cuda.get_array_module(M.data)

            # convert \hat{M} to M
            M = self(M)
            F = M.shape[0]

            I = xp.eye(2)

            loss = 0
            for M_ in M.data:
                loss += xp.power(xp.dot(M_, M_.T) - I, 2).sum()

            if loss.data != 0:
                loss = loss / F

            chainer.reporter.report({'loss': loss}, self)

            return loss
        return f


class MotionMatrices(chainer.dataset.DatasetMixin):
    def __init__(self, M):
        assert(M.shape[0] % 2 == 0)
        xp = cuda.get_array_module(M.data)
        F = M.shape[0] // 2
        self.M = xp.split(M, F)

    def __len__(self):
        return len(self.M)

    def get_example(self, i):
        return self.M[i]


class AffineCorrection(object):
    def __init__(self, epoch=8, batchsize=2):
        self.model = AffineTransformation()
        self.batchsize = batchsize
        self.epoch = epoch

    def optimize(self, M, X):
        dataset = MotionMatrices(M)
        data_iter = chainer.iterators.SerialIterator(dataset, self.batchsize)

        optimizer = chainer.optimizers.MomentumSGD(lr=0.005)
        optimizer.setup(self.model)
        updater = StandardUpdater(data_iter, optimizer,
                                  loss_func=self.model.get_loss_func())

        log_interval = (1, 'epoch')

        trainer = chainer.training.Trainer(updater, (self.epoch, 'epoch'))
        trainer.extend(extensions.LogReport(trigger=log_interval))
        trainer.extend(
            extensions.PrintReport(['epoch', 'iteration', 'main/loss']),
            trigger=log_interval
        )

        trainer.run()

    def __call__(self, M, X):
        Q = self.model.Q
        xp = cuda.get_array_module(Q.data)
        M = xp.dot(M, Q)
        X = xp.dot(xp.linalg.inv(Q.data), X)
        return M, X
