import numpy as np

import chainer
from chainer import cuda
from chainer import initializers
from chainer import iterators
from chainer import optimizers
from chainer import variable
from chainer.training import extensions
from chainer.training import StandardUpdater

from rigid_motion import LeastSquaresRigidMotion, transform


class AffineTransformation(chainer.Chain):
    """
    A Chain class which defines the affine transformation
    """
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
        Returns a function which calculates the reprojection error defined as:

        .. math::
            \\frac{1}{F}
            \\sum_{f=1}^{F} ||\hat{M}_{f}\hat{M}_{f}^{\\top} - I||^{2}_{F}

        where :math:`||\cdot||_F` denotes the Frobenious norm and
        :math:`\hat{M}_{f}` is an estimated motion matrix corresponding to
        the :math:`f`-th view.

        Args:
            M: Stacked motion matrix of shape (2 * n_views, 3)
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
    """
    Geneate a motion matrix :math:`M_{i}` corresponding to the i-th view

    Args:
        M: Stacked motion matrix of shape (2 * n_views, 3)
    """
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
    """
    Generate the same 3D point clould everytime regardless of the index
    """
    def __init__(self, X):
        self.X = X

    def __len__(self):
        return 1

    def get_example(self, i):
        return self.X


def frobenious_norm_squared(X):
    """Calculate :math:`||X||_{F}^{2}`"""
    return np.power(X, 2).sum()


class AffineCorrection:
    """
    The main optimization process to find the best affine transformation

    Args:
        X_eval (np.ndarray): Matrix of the shape as the 3D point cloud, used to
            evaluate the reconstruction quality
        learning_rate (float): Learning rate
        epoch (int): Number of epochs
        batchsize (int): Batch size during training
    """

    def __init__(self, X_eval=None, learning_rate=4e-3, epoch=8, batchsize=2):
        self.model = AffineTransformation()

        self.X_eval = X_eval
        self.epoch = epoch
        self.batchsize = batchsize
        self.learning_rate = learning_rate

        Q = self.model.Q
        self.xp = cuda.get_array_module(Q.data)

    def optimize(self, M: np.ndarray, X: np.ndarray):
        """
        Find the optimal affine transformation which minimizes the loss defined
        in :py:func:`AffineTransformation.get_loss_func`.

        Args:
            M: Stacked motion matrix of shape (2 * n_views, 3)
            X: 3D point cloud of shape (n_points, 3)
        """
        data_iter = iterators.SerialIterator(MotionMatrices(M), self.batchsize)
        object_iter = iterators.SerialIterator(
            Objects(X),
            1,
            repeat=False
        )

        optimizer = optimizers.MomentumSGD(lr=self.learning_rate)
        optimizer.setup(self.model)
        updater = StandardUpdater(data_iter, optimizer,
                                  loss_func=self.model.get_loss_func())

        log_interval = (1, 'epoch')

        trainer = chainer.training.Trainer(updater, (self.epoch, 'epoch'))

        if self.X_eval is not None:
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
        return self.xp.dot(M, Q.data)

    def transform_x(self, X, Q):
        xp = self.xp
        X = xp.dot(xp.linalg.inv(Q.data), X.T)
        return X.T

    def __call__(self, M, X):
        """
        Calculate :math:`MQ` and :math:`Q^{-1}X^{\top}` where Q is a matrix
        which represents an affine transformation
        """
        Q = self.model.Q
        M = self.transform_m(M, Q)
        X = self.transform_x(X, Q)
        return M, X

    def get_recornstruction_error_func(self):
        """
        Returns a function which calculates the reconstruction error
        defined as:

        .. math::

            E(\hat{X})
            = \sum_{i} ||s R \hat{\mathbf{x}}_i + \mathbf{t} - \mathbf{x}_i||^2

        where

        .. math::

            (s, R, \\mathbf{t})
            = \\underset{s, R, \\mathbf{t}}{\\arg\\min}\,E(\\hat{X})
        """
        def reconstruction_error(X):
            X = self.transform_x(X[0], self.model.Q)

            s, R, t = LeastSquaresRigidMotion(X, self.X_eval).solve()
            X = transform(s, R, t, X)

            error = frobenious_norm_squared(X - self.X_eval)

            chainer.report({'reconstruction_error': error})
            return error
        return reconstruction_error
