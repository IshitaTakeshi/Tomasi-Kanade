from numpy.linalg import inv
import numpy as np

import chainer
from chainer import cuda
from chainer import variable
from chainer import initializers
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
            return loss / F
        return f


class MotionMatrices(chainer.dataset.DatasetMixin):
    def __init__(self, M):
        xp = cuda.get_array_module(M.data)
        F = M.shape[0] // 2
        self.M = xp.split(M, F)

    def __len__(self):
        return len(self.M)

    def get_example(self, i):
        return self.M[i]


class AffineCorrection(object):
    def __init__(self, epoch=40, batchsize=8):
        self.model = AffineTransformation()
        self.batchsize = batchsize
        self.epoch = epoch

    def optimize(self, M, X):
        dataset = MotionMatrices(M)
        data_iter = chainer.iterators.SerialIterator(dataset, self.batchsize)

        optimizer = chainer.optimizers.MomentumSGD()
        optimizer.setup(self.model)
        updater = StandardUpdater(data_iter, optimizer,
                                  loss_func=self.model.get_loss_func())
        trainer = chainer.training.Trainer(updater, (self.epoch, 'epoch'))
        trainer.run()

        I = np.eye(2)
        Q = self.model.Q.data
        for i in range(len(dataset)):
            M = dataset.get_example(i)
            MQ = np.dot(M, Q)
            MQQM = np.dot(MQ, MQ.T)
            print(MQQM)

    def __call__(self, M, X):
        Q = self.model.Q.data  # TODO this can be a cupy array. Allow only numpy
        M = np.dot(M, Q)
        X = np.dot(inv(Q), X)
        return M, X
