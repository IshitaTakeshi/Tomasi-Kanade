import sys

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from plyfile import PlyData


# camera intrinsic parameter

K = np.array([
    [1, 0, 0],
    [0, 1, 0]
])


def random_rotation_matrix_3d():
    A = np.random.uniform(-1, 1, (3, 3))
    Q = np.dot(A, A.T)
    R = np.linalg.svd(Q)[0]
    return R


def read_object(filename):
    ply = PlyData.read(filename)

    vertex = ply['vertex']

    x, y, z = [vertex[t] for t in ('x', 'y', 'z')]

    return np.vstack((x, y, z))


def motion_matrix(K, R):
    return np.dot(K, R)


def plot3d(X):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(X[0], X[1], X[2], '.')
    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_zlabel('z axis')
    ax.view_init(elev=135, azim=90)
    ax.legend()
    ax.set_aspect('equal', 'datalim')
    plt.show()


def motion_matrix(n_views):
    M = []
    for i in range(n_views):
        R = random_rotation_matrix_3d()
        M_i = motion_matrix(K, R)
        M.append(M_i)
    return np.vstack(M)


def measurement_matrix(M, X):
    return np.dot(M, X)


class Camera(object):
    def __init__(self):
        self.image_points = []

    def observe(self, image_points):
        self.image_points.append(image_points)

    @property
    def measurement_matrix(self):
        return np.vstack(self.image_points)


class TargetObject(object):
    def __init__(self, points):
        self.X = points

    @property
    def n_points(self):
        return self.X.shape[1]

    def observed(self, camera_rotation, camera_translation):
        """
        Return points with respect to a camera coordinate
        """
        R = camera_rotation
        t = camera_translation
        return np.dot(R, self.X) + np.outer(t, np.ones(self.n_points))


def tomasi_kanade(W):
    u, s, vh = np.linalg.svd(W, full_matrices=True)

    u = u[:, 0:3]
    s = s[0:3]
    vh = vh[0:3, :]
    M = u * s
    S = vh

    k = np.linalg.norm(M, axis=1).mean()
    M = M / k
    S = S * k
    return M, S


def take_picture(target_object, camera, camera_rotation, camera_translation):
    # Y: points seen from the camera coordinate
    Y = target_object.observed(camera_rotation, camera_translation)
    K = camera.intrinsic
    image_points = np.dot(K, Y)  # project onto the image plane

    noise = np.random.normal(0, noise_std, size=image_points.shape)

    camera.observe(image_points + noise)
    return camera


def main():
    filename = sys.argv[1]
    noise_std = 0.05

    X_true = read_object(filename)

    print(X_true)
    print(X_true.shape)

    N = X_true.shape[0]
    indices = np.arange(0, N, 100)
    # plot3d(X_true[indices])

    n_views = 20
    M_true = motion_matrix(n_views)

    W_true = measurement_matrix(M_true, X_true)
    noise = np.random.normal(0, noise_std, size=W_true.shape)
    W = W_true + noise

    W = camera.measurement_matrix

    M, X = tk.run()

    op = OrthographicProjection(
        learning_rate=1e-2,
        n_epochs=200,
        alpha=0.0,
        regularization=None
    )
    M, X = op.remove_affine_ambiguity(M, X)


main()
