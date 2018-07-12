import sys

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from plyfile import PlyData

from tomasi_kanade import TomasiKanade


def read_object(filename):
    ply = PlyData.read(filename)

    vertex = ply['vertex']

    x, y, z = [vertex[t] for t in ('x', 'y', 'z')]

    return np.vstack((x, y, z))


def plot2d(X):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(X[0], X[1], '.')
    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_aspect('equal', 'datalim')
    plt.show()


def plot3d(*points):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for i, P in enumerate(points):
        ax.plot(P[0], P[1], P[2], '.', label=str(i))
        ax.set_xlabel('x axis')
        ax.set_ylabel('y axis')
        ax.set_zlabel('z axis')
        ax.legend()

    ax.view_init(elev=135, azim=90)
    ax.set_aspect('equal', 'datalim')
    plt.show()


def random_rotation_matrix_3d():
    A = np.random.uniform(-1, 1, (3, 3))
    Q = np.dot(A, A.T)
    R = np.linalg.svd(Q)[0]
    return R


def measurement_matrix(M, X):
    return np.dot(M, X)


class Camera(object):
    def __init__(self, intrinsic_parameters):
        self.intrinsic_parameters = intrinsic_parameters
        self.rotation = np.eye(3)
        self.translation = np.zeros(3)

    def set_pose(self, rotation, translation):
        self.rotation = rotation
        self.translation = translation


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


def take_picture(target_object, camera, noise_std=0.0):

    # Y: points seen from the camera coordinate
    Y = target_object.observed(camera.rotation, camera.translation)
    K = camera.intrinsic_parameters

    image_points = np.dot(K, Y)  # project onto the image plane

    if noise_std == 0.0:
        return image_points

    noise = np.random.normal(0, noise_std, size=image_points.shape)
    return image_points + noise


def random_vector_3d(scale=1.0):
    v = np.random.uniform(-1, 1, size=3)
    v = v / np.linalg.norm(v)
    return scale * v


def normalize_object_size(X):
    return X / np.linalg.norm(X, axis=0).mean()


def main():
    np.random.seed(1234)

    filename = sys.argv[1]

    intrinsic_parameters = np.array([
        [1, 0, 0],
        [0, 1, 0]
    ])

    # standard deviation of noise
    noise_std = 0.0

    X_true = read_object(filename)
    X_true = normalize_object_size(X_true)

    indices = np.arange(0, X_true.shape[1], 100)
    X_true = X_true[:, indices]

    target_object = TargetObject(X_true)

    print(X_true.shape)

    n_views = 50

    camera = Camera(intrinsic_parameters)

    tomasi_kanade = TomasiKanade()

    for i in range(n_views):
        R = random_rotation_matrix_3d()
        t = random_vector_3d()

        camera.set_pose(R, t)

        image_points = take_picture(target_object, camera, noise_std)
        plot2d(image_points)
        tomasi_kanade.add_image_points(image_points)

    M, X = tomasi_kanade.run()

    from rigid_motion import LeastSquaresRigidMotion, transform
    s, R, t = LeastSquaresRigidMotion(X_true.T, X.T).solve()
    X_true = np.array([transform(s, R, t, x) for x in X_true.T]).T

    print("Error: {}".format(np.power(X_true - X, 2).sum(axis=0).mean()))

    plot3d(X, X_true)

main()
