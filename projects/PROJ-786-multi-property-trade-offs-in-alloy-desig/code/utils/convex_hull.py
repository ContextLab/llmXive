"""
Convex Hull and Delaunay utilities for alloy design.

This module provides wrappers around scipy.spatial.ConvexHull and Delaunay
to facilitate:
1. Constructing a convex hull from a set of feature vectors (compositions).
2. Testing whether new points (synthetic candidates) lie within the hull
   (i.e., are within the convex span of the training data).
"""

import numpy as np
from typing import Tuple, Optional, List
from scipy.spatial import ConvexHull, Delaunay

from utils.logging_config import log_info_with_context, log_error_with_context


class ConvexHullWrapper:
    """
    A wrapper class for scipy.spatial.ConvexHull and Delaunay.

    This class handles the construction of the hull from a set of points
    and provides methods to test if new points lie within that hull.
    """

    def __init__(self, points: np.ndarray, log_context: Optional[dict] = None):
        """
        Initialize the wrapper by computing the ConvexHull and Delaunay triangulation.

        Args:
            points: A numpy array of shape (n_samples, n_features).
            log_context: Optional dictionary for logging context.
        """
        self.log_context = log_context or {"module": "convex_hull"}

        if points.ndim != 2:
            log_error_with_context(
                f"Points array must be 2D, got shape {points.shape}",
                context=self.log_context
            )
            raise ValueError("Points array must be 2D.")

        if points.shape[0] == 0:
            log_error_with_context(
                "Points array cannot be empty.",
                context=self.log_context
            )
            raise ValueError("Points array cannot be empty.")

        if points.shape[0] < points.shape[1]:
            # Not enough points to form a full-dimensional hull in high dimensions
            # This is a common issue in alloy design where feature space is high-D.
            # We proceed but note that the hull might be degenerate.
            log_info_with_context(
                f"Warning: Number of points ({points.shape[0]}) is less than "
                f"dimensions ({points.shape[1]}). Hull may be degenerate.",
                context=self.log_context
            )

        try:
            self.hull = ConvexHull(points)
            self.delaunay = Delaunay(points)
            self.points = points
            log_info_with_context(
                f"Successfully computed ConvexHull and Delaunay for {points.shape[0]} points "
                f"in {points.shape[1]} dimensions.",
                context=self.log_context
            )
        except Exception as e:
            log_error_with_context(
                f"Failed to compute ConvexHull/Delaunay: {str(e)}",
                context=self.log_context
            )
            raise

    def is_inside(self, new_points: np.ndarray) -> np.ndarray:
        """
        Check if new points lie inside the convex hull.

        Args:
            new_points: A numpy array of shape (m, n_features) or (n_features,).

        Returns:
            A boolean numpy array indicating whether each point is inside the hull.
            Returns False for points if the hull is degenerate in a way that prevents testing.
        """
        if new_points.ndim == 1:
            new_points = new_points.reshape(1, -1)

        if new_points.shape[1] != self.points.shape[1]:
            log_error_with_context(
                f"Dimension mismatch: new_points has {new_points.shape[1]} features, "
                f"expected {self.points.shape[1]}.",
                context=self.log_context
            )
            raise ValueError("Dimension mismatch between hull points and new points.")

        try:
            # Delaunay.find_simplex returns the index of the simplex containing the point,
            # or -1 if the point is outside.
            indices = self.delaunay.find_simplex(new_points)
            return indices != -1
        except Exception as e:
            log_error_with_context(
                f"Error during point-in-hull test: {str(e)}",
                context=self.log_context
            )
            # Fallback to False for all points on error to avoid crashing downstream
            return np.zeros(new_points.shape[0], dtype=bool)

    def get_volume(self) -> float:
        """
        Get the volume (or area in 2D) of the convex hull.

        Returns:
            The volume of the hull.
        """
        return self.hull.volume

    def get_area(self) -> float:
        """
        Get the surface area of the convex hull.

        Returns:
            The surface area of the hull.
        """
        return self.hull.area

    def get_vertices(self) -> np.ndarray:
        """
        Get the indices of the points forming the vertices of the hull.

        Returns:
            A numpy array of vertex indices.
        """
        return self.hull.vertices

    def get_hull_points(self) -> np.ndarray:
        """
        Get the actual coordinates of the hull vertices.

        Returns:
            A numpy array of shape (n_vertices, n_features).
        """
        return self.points[self.hull.vertices]


def compute_convex_hull(
    points: np.ndarray,
    log_context: Optional[dict] = None
) -> ConvexHullWrapper:
    """
    Convenience function to create a ConvexHullWrapper.

    Args:
        points: Input data array (n_samples, n_features).
        log_context: Optional logging context.

    Returns:
        An initialized ConvexHullWrapper instance.
    """
    return ConvexHullWrapper(points, log_context)


def test_points_in_hull(
    wrapper: ConvexHullWrapper,
    new_points: np.ndarray
) -> np.ndarray:
    """
    Convenience function to test points against a wrapper.

    Args:
        wrapper: An initialized ConvexHullWrapper.
        new_points: Points to test.

    Returns:
        Boolean array indicating inside/outside status.
    """
    return wrapper.is_inside(new_points)
