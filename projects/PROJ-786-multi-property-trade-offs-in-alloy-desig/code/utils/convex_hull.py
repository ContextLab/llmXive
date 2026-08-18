"""
Convex Hull and Delaunay Triangulation Utilities for Alloy Design.

This module provides a robust wrapper around scipy.spatial.ConvexHull and Delaunay
to support:
  1. Computing the convex hull of empirical alloy data points.
  2. Testing whether synthetic candidate points lie within the convex hull.
  3. Logging context-aware information for debugging and validation.

All functions are designed to work with numpy arrays of shape (N, D), where
N is the number of points and D is the dimensionality (feature space).
"""

import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from scipy.spatial import ConvexHull, Delaunay

from utils.logging_config import log_info_with_context, log_error_with_context, get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class ConvexHullWrapper:
    """
    A wrapper class for scipy.spatial.ConvexHull and Delaunay to manage
    convex hull computations and point-in-hull tests.

    Attributes:
        hull (ConvexHull): The computed convex hull object.
        delaunay (Delaunay): The Delaunay triangulation object for point testing.
        points (np.ndarray): The original input points used to compute the hull.
        is_valid (bool): True if the hull was successfully computed.
    """

    def __init__(self, points: np.ndarray):
        """
        Initialize the wrapper and compute the hull.

        Args:
            points (np.ndarray): Input array of shape (N, D).

        Raises:
            ValueError: If input points are not a 2D numpy array or have < 3 points.
            RuntimeError: If the convex hull computation fails (e.g., points are collinear/coplanar).
        """
        if not isinstance(points, np.ndarray):
            raise ValueError("Input points must be a numpy array.")

        if points.ndim != 2:
            raise ValueError(f"Input points must be 2D (N, D), got {points.ndim}D.")

        if points.shape[0] < 3:
            raise ValueError(f"Convex hull requires at least 3 points, got {points.shape[0]}.")

        self.points = points
        self.hull: Optional[ConvexHull] = None
        self.delaunay: Optional[Delaunay] = None
        self.is_valid = False

        try:
            self.hull = ConvexHull(points)
            # Delaunay is required for efficient point-in-hull testing in higher dimensions
            self.delaunay = Delaunay(points)
            self.is_valid = True
            log_info_with_context(
                logger,
                "ConvexHullWrapper",
                f"Successfully computed ConvexHull and Delaunay for {points.shape[0]} points in {points.shape[1]} dimensions."
            )
        except Exception as e:
            log_error_with_context(
                logger,
                "ConvexHullWrapper",
                f"Failed to compute ConvexHull or Delaunay: {str(e)}"
            )
            raise RuntimeError(f"Convex hull computation failed: {e}") from e

    def get_volume(self) -> float:
        """
        Get the volume of the convex hull.

        Returns:
            float: The volume of the hull.

        Raises:
            RuntimeError: If the hull is not valid.
        """
        if not self.is_valid:
            raise RuntimeError("Hull is not valid. Cannot compute volume.")
        return float(self.hull.volume)

    def get_area(self) -> float:
        """
        Get the surface area of the convex hull.

        Returns:
            float: The surface area of the hull.

        Raises:
            RuntimeError: If the hull is not valid.
        """
        if not self.is_valid:
            raise RuntimeError("Hull is not valid. Cannot compute area.")
        return float(self.hull.area)

    def contains(self, points: np.ndarray) -> np.ndarray:
        """
        Test if points lie inside the convex hull.

        Uses the Delaunay triangulation to check if points are within the hull.
        For points on the boundary, this returns True.

        Args:
            points (np.ndarray): Array of shape (M, D) to test.

        Returns:
            np.ndarray: Boolean array of shape (M,) indicating containment.

        Raises:
            RuntimeError: If the hull is not valid.
        """
        if not self.is_valid:
            raise RuntimeError("Hull is not valid. Cannot test containment.")

        if points.ndim == 1:
            points = points.reshape(1, -1)

        if points.shape[1] != self.points.shape[1]:
            raise ValueError(f"Point dimension mismatch: expected {self.points.shape[1]}, got {points.shape[1]}")

        # scipy.spatial.Delaunay.contains is efficient for this
        return self.delaunay.contains(points)


def compute_convex_hull(points: np.ndarray) -> ConvexHullWrapper:
    """
    Compute the convex hull for a given set of points.

    This is a convenience function that wraps the ConvexHullWrapper initialization.

    Args:
        points (np.ndarray): Input array of shape (N, D).

    Returns:
        ConvexHullWrapper: An instance containing the computed hull and utilities.
    """
    return ConvexHullWrapper(points)


def test_points_in_hull(hull_wrapper: ConvexHullWrapper, points: np.ndarray) -> np.ndarray:
    """
    Test if a set of points lies within a pre-computed convex hull.

    Args:
        hull_wrapper (ConvexHullWrapper): The wrapper containing the computed hull.
        points (np.ndarray): Array of shape (M, D) to test.

    Returns:
        np.ndarray: Boolean array of shape (M,) where True means the point is inside.
    """
    return hull_wrapper.contains(points)