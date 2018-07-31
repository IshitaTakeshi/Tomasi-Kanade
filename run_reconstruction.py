import sys

import numpy as np

from plyfile import PlyData

from tomasi_kanade import TomasiKanade


from visualization import plot3d
import rigid_motion


def read_object(filename):
    ply = PlyData.read(filename)

    vertex = ply['vertex']

    x, y, z = [vertex[t] for t in ('x', 'y', 'z')]

    return np.vstack((x, y, z))




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
        return rigid_motion.transform(1, R, t, self.X)



def take_picture(target_object, camera, noise_std=0.0):

    # Y: points seen from the camera coordinate
    Y = target_object.observed(camera.rotation, camera.translation)
    K = camera.intrinsic_parameters

    image_points = np.dot(K, Y)  # project onto the image plane

    if noise_std == 0.0:
        return image_points

    noise = np.random.normal(0, noise_std, size=image_points.shape)
    return image_points + noise




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
