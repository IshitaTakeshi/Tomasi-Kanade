from numpy.linalg import inv
import numpy as np


class OrthographicProjection(object):
    """
    Remove affine ambiguity by multiplying an affine matrix :math:`Q` and its
    inverse :math:`Q^{-1}` to the output :math:`(\widetilde{M}, \widetilde{S})`
    respectively under the assumption that the projection is orthographic,
    where :math:`\widetilde{M}` is a motion matrix and :math:`\widetilde{S}`
    is a shape matrix calculated by the Tomasi-Kanade method.
    """
    def __init__(self, learning_rate=1e-3, n_epochs=200):
        """
        Args:
            learning_rate: float
                Learning rate
            n_epochs: int
                Number of epochs to find the optimal transformation
        """
        self.learning_rate = learning_rate
        self.n_epochs = n_epochs

    def gradient(self, M: np.ndarray, Q: np.ndarray) -> np.ndarray:
        """
        Calculate the gradient of the error function :math:`E`
        with respect to matrix :math:`Q`.

        Let :math:`\mathbf{q}_j` be the :math:`j`-th column of :math:`Q`.
        The gradient of with respect to the matrix :math:`Q` is defined as
        the set of gradients over each column.

        .. math::
            \\left[
                \\frac{\partial E}{\partial \mathbf{q}_1},
                \\frac{\partial E}{\partial \mathbf{q}_2},
                \\frac{\partial E}{\partial \mathbf{q}_3}
            \\right]

        Returns:
            The gradient defined above.

        Raises:
            ValueError: if the given regularizer is not recognized
        """

        V = np.dot(M, Q)
        [h0, h1] = np.sum(np.power(V, 2), axis=1) - np.ones(2)
        g = np.sum(V[0] * V[1])

        dh0 = 2 * np.outer(M[0], V[0])
        dg = np.dot(M.T, V[[1, 0]])  # [ dg / dj1, dg / dj2, dg / dj3]
        dh1 = 2 * np.outer(M[1], V[1])

        return h0 * dh0 + g * dg + h1 * dh1

    def _mqqm(self, M: np.ndarray, Q: np.ndarray):
        F = self.n_views(M)

        MQQM = []
        for M_ in np.split(M, F):
            MQ = np.dot(M_, Q)
            MQQM.append(np.dot(MQ, MQ.T))
        return np.array(MQQM)

    def error(self, M: np.ndarray, Q: np.ndarray):
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

        I = np.eye(2)
        return np.mean(
            [np.power(MQQM-I, 2).sum() for MQQM in self._mqqm(M, Q)]
        )

    def n_views(self, M: np.ndarray):
        """
        Returns the number of views.

        Args:
            M: Motion matrix of shape (n_views * 2, n_image_points)
        """

        return M.shape[0] // 2

    def remove_affine_ambiguity(self, M: np.ndarray, S: np.ndarray):
        """
        Remove affine ambiguity from a pair of the motion matrix :math:`M`
        and the shape matrix :math:`S`.

        Args:
            M: Motion matrix of shape (n_views * 2, n_image_points)
            S: Shape matrix of shape (3, n_image_points)

        Returns:
            :math:`M` and :math:`S` that their affine ambiguity is removed.
        """

        assert(M.shape[0] % 2 == 0)

        F = self.n_views(M)

        def epoch(Q):
            for M_ in np.split(M, F):
                gradient = self.gradient(M_, Q)

                if np.isnan(gradient).any():
                    raise ValueError("Observed nan in gradient")

                Q -= gradient * self.learning_rate
            return Q

        Q = np.eye(3)

        for i in range(self.n_epochs):
            Q = epoch(Q)
            print(Q)

        M = np.dot(M, Q)
        S = np.dot(inv(Q), S)
        return M, S
