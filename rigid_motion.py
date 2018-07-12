from numpy.testing import assert_array_almost_equal
import numpy as np


def calculate_rotation(X, Y):
    S = np.dot(X.T, Y)

    U, _, VT = np.linalg.svd(S)  # S = U * Sigma * VT
    V = VT.T
    return np.dot(V, U.T)


def calculate_scaling(X, Y, R):
    n = np.sum(np.dot(np.dot(y, R), x) for x, y in zip(X, Y))
    d = np.sum(X * X)  # equivalent to sum([dot(x, x) for x in X])
    return n / d


def calculate_translation(s, R, p, q):
    return q - s * np.dot(R, p)


class LeastSquaresRigidMotion(object):
    """
    For each element in :math:`P = \{\mathbf{p}_i\}`
    and the corresponding element in :math:`Q = \{\mathbf{q}_i\}`,
    calculate the transformation which minimizes the error

    .. math::
        E(P, Q) = \sum_{i} ||s R \mathbf{p}_i + \mathbf{t} - \mathbf{q}_i||^2

    where :math:`s`, :math:`R`, :math:`\mathbf{t}` are scaling factor,
    rotation matrix and translation vector respectively.

    Examples:

    >>> s, R, t = LeastSquaresRigidMotion(P, Q).solve()
    >>> P = np.array([transform(s, R, t, p) for p in P])

    """

    def __init__(self, P: np.ndarray, Q: np.ndarray):
        """
        Args:
            P: Set of points of shape (n_image_points, n_channels)
                to be transformed
            Q: Set of points of shape (n_image_points, n_channels)
                to be used as a reference
        """
        if P.shape != Q.shape:
            raise ValueError("P and Q must be the same shape")

        self.n_features = P.shape[1]
        self.P = P
        self.Q = Q

    def solve(self):
        """
        Calculate (:math:`s`, :math:`R`, :math:`\mathbf{t}`)

        Returns:
            tuple: (s, R, t) where
                :math:`s`
                    Scaling coefficient
                :math:`R`
                    Rotation matrix
                :math:`\mathbf{t}`
                    translation vector
        """

        mean_p = np.mean(self.P, axis=0)
        mean_q = np.mean(self.Q, axis=0)

        X = self.P - mean_p
        Y = self.Q - mean_q

        R = calculate_rotation(X, Y)
        s = calculate_scaling(X, Y, R)
        t = calculate_translation(s, R, mean_p, mean_q)

        return s, R, t


def transform(s: float, R: np.ndarray,
              t: np.ndarray, p: np.ndarray) -> np.ndarray:
    """
    Transform a given point :math:`\mathbf{p}` into
    :math:`\mathbf{q} = sR\mathbf{p} + \mathbf{t}` where

    :math:`s`
        Scaling factor
    :math:`R`
        Rotation matrix
    :math:`\mathbf{t}`
        Translation vector

    Args:
        s: Scaling factor
        R: Rotation matrix
        t: Translation vector
        p: Point to be transformed

    Returns:
        Transformed vector
    """
    return s * np.dot(R, p) + t
