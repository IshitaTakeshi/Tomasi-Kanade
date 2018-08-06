import numpy as np

from affine_correction import AffineCorrection


class TomasiKanade(object):
    """
    The main process of the Tomasi-Kanade method

    Args:
        X_eval (np.ndarray): 3D point cloud which will be used to evaluate
            the reconstructed model
        learning_rate (float): Hyperparameter used in the affine correction
            which run in the reconstruction process
    """

    def __init__(self, X_eval=None, learning_rate=4e-3):
        self.affine_correction = AffineCorrection(X_eval, learning_rate)
        self.image_points = []

    def add_image_points(self, image_points: np.ndarray):
        """
        Add 2D image points to form a measurement matrix

        Args:
            image_points: Image points of shape (n_points, 2)
        """

        mean = np.mean(image_points, axis=0, keepdims=True)
        image_points = image_points - mean
        self.image_points.append(image_points.T)

    @property
    def measurement_matrix(self):
        """Measurement matrix of shape (2 * n_views, n_points)"""
        return np.vstack(self.image_points)

    def run(self):
        """
        Run reconstruction

        Returns:
            tuple: containing 2 elements:

                - M: Motion matrix of shape (2m, 3) where `m` is
                  the number of viewpoints
                - X: Reconstructed 3D points of shape (n, 3) where `n` is
                  the number of points in the reconstructed point cloud
        """
        W = self.measurement_matrix
        u, s, vh = np.linalg.svd(W, full_matrices=True)

        u = u[:, 0:3]
        s = s[0:3]
        vh = vh[0:3, :]

        M = u * s
        X = vh

        # normalize the matrix entries to make
        # the affine correction optimization stable
        k = np.linalg.norm(M, axis=1).mean()
        M = M / k
        X = X * k

        self.affine_correction.optimize(M, X.T)

        return self.affine_correction(M, X.T)
