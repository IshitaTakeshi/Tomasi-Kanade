import numpy as np

from affine_ambiguity import AffineCorrection
from sfm import SFM


class TomasiKanade(object):
    def __init__(self):
        self.affine_correction = AffineCorrection()
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

        self.affine_correction.optimize(M, X)

        return self.affine_correction(M, X)
