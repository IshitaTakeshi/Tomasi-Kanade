import numpy as np

import chainer
from chainer import cuda
from chainer import initializers
from chainer import iterators
from chainer import optimizers
from chainer import variable
from chainer.training import extensions
from chainer.training.updaters import StandardUpdater

from rigid_motion import LeastSquaresRigidMotion, transform


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


class Objects(chainer.dataset.DatasetMixin):
    def __init__(self, X):
        self.X = X

    def __len__(self):
        return 1

    def get_example(self, i):
        return self.X


def frobenious_norm_squared(X):
    return np.power(X, 2).sum()


class AffineCorrection(object):
    def __init__(self, X_eval=None, epoch=8, batchsize=2):
        self.model = AffineTransformation()

        self.X_eval = X_eval
        self.epoch = epoch
        self.batchsize = batchsize

        Q = self.model.Q
        self.xp = cuda.get_array_module(Q.data)

    def optimize(self, M, X):
        data_iter = iterators.SerialIterator(MotionMatrices(M), self.batchsize)
        object_iter = iterators.SerialIterator(
            Objects(X),
            1,
            repeat=False
        )

        optimizer = optimizers.MomentumSGD(lr=0.004)
        optimizer.setup(self.model)
        updater = StandardUpdater(data_iter, optimizer,
                                  loss_func=self.model.get_loss_func())

        log_interval = (1, 'epoch')

        trainer = chainer.training.Trainer(updater, (self.epoch, 'epoch'))

        trainer.extend(extensions.Evaluator(
                object_iter,
                self.model,
                eval_func=self.get_recornstruction_error_func()
            ),
            trigger=(1, 'epoch')
        )

        trainer.extend(extensions.LogReport(trigger=log_interval))
        trainer.extend(
            extensions.PrintReport([
                'epoch', 'iteration', 'main/loss',
                'reconstruction_error'
            ]),
            trigger=log_interval
        )

        trainer.run()

    def transform_m(self, M, Q):
        return self.xp.dot(M, Q)

    def transform_x(self, X, Q):
        xp = self.xp
        return xp.dot(xp.linalg.inv(Q.data), X)

    def __call__(self, M, X):
        Q = self.model.Q
        M = self.transform_m(M, Q)
        X = self.transform_x(X, Q)
        return M, X

    def get_recornstruction_error_func(self):
        def reconstruction_error(X):
            X = self.transform_x(X[0], self.model.Q)
            X, X_eval = X.T, self.X_eval.T

            s, R, t = LeastSquaresRigidMotion(X, X_eval).solve()
            X = transform(s, R, t, X)

            error = frobenious_norm_squared(X_eval - X)

            chainer.report({'reconstruction_error': error})
            return error
        return reconstruction_error
