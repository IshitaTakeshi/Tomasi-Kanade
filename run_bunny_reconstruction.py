import sys

import numpy as np

from matplotlib.animation import FuncAnimation
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from plyfile import PlyData

from tomasi_kanade import TomasiKanade


def read_object(filename):
    ply = PlyData.read(filename)

    vertex = ply['vertex']

    x, y, z = [vertex[t] for t in ('x', 'y', 'z')]

    return np.vstack((x, y, z))


def annotate(ax, P, labels=None):
    if labels is None:
        labels = range(len(P))

    font = FontProperties()
    font.set_weight("bold")

    for label, p in zip(labels, P):
        ax.text(*p, label, alpha=0.8, fontproperties=font)


def plot2d(P, do_annotate=False, color=None):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(P[:, 0], P[:, 1], c=color)

    if do_annotate:
        annotate(ax, P, labels=range(0, len(P), 50))

    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_aspect('equal', 'datalim')

    plt.show()


def plot3d(P, do_annotate=False, elev=45, azim=0, color=None):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(P[:, 0], P[:, 1], P[:, 2], c=color)

    if do_annotate:
        annotate(ax, P)

    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_zlabel('z axis')
    ax.view_init(elev, azim)
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

    # too many points in the file
    indices = np.arange(0, X_true.shape[1], 20)
    X_true = X_true[:, indices]
    print("X_true.shape: {}".format(X_true.shape))

    color = np.mean(np.abs(X_true), axis=0)
    color = color / np.max(color)

    # plot3d(X_true.T, azim=90, elev=-90, color=color)
    # plot3d(X_true.T, azim=-90, elev=90, color=color)

    n_views = 128

    target_object = TargetObject(X_true)
    camera = Camera(intrinsic_parameters)
    tomasi_kanade = TomasiKanade(X_true)

    for i in range(n_views):
        # set camera pose randomly
        R = random_rotation_matrix_3d()
        t = random_vector_3d()
        camera.set_pose(R, t)

        image_points = take_picture(target_object, camera, noise_std)

        # plot2d(image_points.T, color=color)
        # plot2d(image_points.T, do_annotate=True)

        tomasi_kanade.add_image_points(image_points)

    M, X = tomasi_kanade.run()

    plot3d(X.T, azim=0, elev=-90, color=color)
    plot3d(X.T, azim=180, elev=90, color=color)
    plot3d(X.T, azim=10, elev=-70, color=color)

main()
