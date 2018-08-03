import numpy as np

from affine_correction import AffineCorrection


class TomasiKanade(object):
    """
    The main process of the Tomasi-Kanade method

    Args:
        X_eval: 3D point cloud which will be used to evaluate
        the reconstructed model
    """

    def __init__(self, X_eval: np.ndarray = None):
        self.affine_correction = AffineCorrection(X_eval)
        self.image_points = []

    def add_image_points(self, image_points):
        self.image_points.append(image_points)

    @property
    def measurement_matrix(self):
        return np.vstack(self.image_points)

    def run(self):
        """
        Run reconstruction

        Returns:
            M: Motion matrix of shape (2m, 3) where `m` is
            the number of viewpoints
            X: Reconstructed 3D points of shape (n, 3) where `n` is
            the number of points in the reconstructed point cloud
        """
        W = self.measurement_matrix
        u, s, vh = np.linalg.svd(W, full_matrices=True)

        u = u[:, 0:3]
        s = s[0:3]
        vh = vh[0:3, :]

        M = u * s
        X = vh

        k = np.linalg.norm(M, axis=1).mean()
        M = M / k
        X = X * k

        self.affine_correction.optimize(M, X.T)

        return self.affine_correction(M, X.T)
