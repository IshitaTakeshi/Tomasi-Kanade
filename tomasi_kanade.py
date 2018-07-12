import numpy as np

from affine_ambiguity import OrthographicProjection
from sfm import SFM


class TomasiKanade(object):
    def __init__(self, learning_rate=1e-2, n_epochs=20):
        self.op = OrthographicProjection(learning_rate, n_epochs)
        self.image_points = []

    def add_image_points(self, image_points):
        self.image_points.append(image_points)

    @property
    def measurement_matrix(self):
        return np.vstack(self.image_points)

    def run(self):
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

        M, X = self.op.remove_affine_ambiguity(M, X)

        return M, X
