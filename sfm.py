import numpy as np


class SFM(object):
    """
    Abstract class for Structure from Motion.
    There's one assumption: all image points must be observed from all views
    """
    def __init__(self):
        self.n_image_points = None
        self.W = []

    @property
    def n_views(self) -> int:
        """
        Number of views used to reconstruct the 3d model.
        This value increases as new image points added
        """
        return len(self.W)

    @property
    def measurement_matrix(self):
        """
        Return the measurement matrix of shape (2 * n_views, n_points)
        """
        return np.vstack(self.W)

    def add_image_points(self, image_points: np.ndarray):
        """
        Add images points observed from a single view

        Args:
            image_points: 2D image points of shape (n_points, 2)
                extracted from one view
        """
        if self.n_image_points is None:
            self.n_image_points = image_points.shape[0]

        if image_points.shape[0] != self.n_image_points:
            raise ValueError(
                "The number of image points must be the same as "
                "the ones previously added"
            )

        mean = np.mean(image_points, axis=0, keepdims=True)
        image_points = image_points - mean

        self.W.append(image_points.T)

    def run(self):
        """
        Subclasses must override this method and implement the main processing
        of Structure from Motion.
        """
        raise NotImplementedError("'run' is not implemented")
