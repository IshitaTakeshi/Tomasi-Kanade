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

    return np.vstack((x, y, z)).T


def normalize_object_size(X):
    return X / np.linalg.norm(X, axis=1).mean()


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


class Object3D(object):
    def __init__(self, points):
        self.X = points

    @property
    def n_points(self):
        """The number of points in the object"""
        return self.X.shape[0]

    def observed(self, camera_rotation: np.ndarray,
                 camera_translation: np.ndarray):
        """
        Return 2D points projected onto the image plane
        Args:
            camera_rotation: Rotation matrix
            which represents the camera rotation
            camera_translation: Translation vector
            which represents the camera position
        """
        R = camera_rotation
        t = camera_translation
        return rigid_motion.transform(1, R, t, self.X)


def take_picture(target_object: Object3D, camera: Camera, noise_std=0.0):
    """
    Project 3D points in 'target_object' onto the image plane defined
    by 'camera'

    Args:
        target_object: Object to be seen from the ``camera``
    """

    # Y: points seen from the camera coordinate
    Y = target_object.observed(camera.rotation, camera.translation)
    K = camera.intrinsic_parameters

    image_points = np.dot(K, Y.T)  # project onto the image plane

    if noise_std == 0.0:
        return image_points

    noise = np.random.normal(0, noise_std, size=image_points.shape)
    return image_points + noise



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
    indices = np.arange(0, X_true.shape[0], 20)
    X_true = X_true[indices]

    color = np.mean(np.abs(X_true), axis=1)
    color = color / np.max(color)

    # plot3d(X_true.T, azim=90, elev=-90, color=color)
    # plot3d(X_true.T, azim=-90, elev=90, color=color)

    n_views = 128

    target_object = TargetObject(X_true)
    camera = Camera(intrinsic_parameters)
    tomasi_kanade = TomasiKanade(X_true)

    for i in range(n_views):
        # set camera pose randomly
        R = rigid_motion.random_rotation_matrix_3d()
        t = rigid_motion.random_vector_3d()
        camera.set_pose(R, t)

        image_points = take_picture(target_object, camera, noise_std)

        tomasi_kanade.add_image_points(image_points)

    M, X = tomasi_kanade.run()

    plot3d(X, azim=0, elev=-90, color=color)
    plot3d(X, azim=180, elev=90, color=color)
    plot3d(X, azim=10, elev=-70, color=color)


if __name__ == '__main__':
    main()
