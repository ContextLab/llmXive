"""
Convex Hull utilities for alloy composition space analysis.

Provides wrappers for scipy.spatial.ConvexHull and Delaunay
to test point inclusion and calculate distances to hull boundaries.
"""

import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from typing import Tuple, Optional, List, Dict, Any
from utils.logging_config import log_info_with_context, log_error_with_context, get_logger

class ConvexHullWrapper:
    """
    Wrapper around scipy.spatial.ConvexHull for composition space operations.
    
    Provides methods for:
    - Testing if points are inside the hull
    - Calculating distance to hull boundary
    - Getting hull radius for proximity thresholds
    """
    
    def __init__(self, points: np.ndarray):
        """
        Initialize the convex hull wrapper.
        
        Args:
            points: Array of shape (n_samples, n_features) representing the training data
        """
        self.logger = get_logger(__name__)
        self.points = points
        self.n_features = points.shape[1]
        
        if points.shape[0] < self.n_features + 1:
            raise ValueError(f"Need at least {self.n_features + 1} points to compute convex hull in {self.n_features}D space")
        
        try:
            self.hull = ConvexHull(points)
            self.delaunay = Delaunay(points)
            log_info_with_context("ConvexHull", f"Computed convex hull with {len(self.hull.vertices)} vertices")
        except Exception as e:
            log_error_with_context("ConvexHull", f"Failed to compute convex hull: {e}")
            raise
    
    def is_inside(self, point: np.ndarray, return_distance: bool = False) -> Tuple[bool, Optional[float]]:
        """
        Test if a point is inside or on the boundary of the convex hull.
        
        Args:
            point: Array of shape (n_features,) representing a composition
            return_distance: If True, also return distance to hull boundary
        
        Returns:
            Tuple of (is_inside, distance_to_boundary)
            distance_to_boundary is None if return_distance is False
        """
        point = np.atleast_2d(point)
        
        # Test if point is inside using Delaunay
        try:
            inside = self.delaunay.find_simplex(point) != -1
        except Exception as e:
            log_error_with_context("ConvexHull", f"Point inclusion test failed: {e}")
            return False, None if not return_distance else 0.0
        
        if not return_distance:
            return inside[0], None
        
        # Calculate distance to hull boundary if point is inside
        if inside[0]:
            distance = self._calculate_distance_to_boundary(point[0])
            return True, distance
        else:
            # For points outside, calculate distance to nearest hull vertex
            distance = self._calculate_distance_to_hull(point[0])
            return False, distance
    
    def _calculate_distance_to_boundary(self, point: np.ndarray) -> float:
        """
        Calculate distance from an interior point to the hull boundary.
        
        This is approximated as the minimum distance to any hull facet.
        """
        # Get hull equations: each row is [normal, offset] where normal.x + offset = 0
        # Distance from point to plane: |normal.x + offset| / ||normal||
        equations = self.hull.equations
        normals = equations[:, :-1]
        offsets = equations[:, -1]
        
        # Calculate signed distances to all facets
        # For interior points, all signed distances should be positive
        signed_distances = np.dot(normals, point) + offsets
        
        # The distance to boundary is the minimum positive distance
        # (points inside have positive distances to all facets)
        min_distance = np.min(signed_distances)
        
        return max(0.0, min_distance)
    
    def _calculate_distance_to_hull(self, point: np.ndarray) -> float:
        """
        Calculate distance from an exterior point to the nearest point on the hull.
        
        This is approximated as the minimum distance to any hull vertex.
        """
        vertices = self.points[self.hull.vertices]
        distances = np.linalg.norm(vertices - point, axis=1)
        return np.min(distances)
    
    def get_radius(self) -> float:
        """
        Calculate the radius of the convex hull.
        
        Defined as the maximum distance from the centroid to any vertex.
        """
        centroid = np.mean(self.points, axis=0)
        vertices = self.points[self.hull.vertices]
        distances = np.linalg.norm(vertices - centroid, axis=1)
        return np.max(distances)
    
    def get_volume(self) -> float:
        """Get the volume of the convex hull."""
        return self.hull.volume
    
    def get_area(self) -> float:
        """Get the surface area of the convex hull."""
        return self.hull.area

def compute_convex_hull(points: np.ndarray) -> ConvexHullWrapper:
    """
    Compute a convex hull wrapper for the given points.
    
    Args:
        points: Array of shape (n_samples, n_features)
    
    Returns:
        ConvexHullWrapper instance
    """
    return ConvexHullWrapper(points)

def test_points_in_hull(
    hull_wrapper: ConvexHullWrapper,
    test_points: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Test multiple points for inclusion in the convex hull.
    
    Args:
        hull_wrapper: Initialized ConvexHullWrapper
        test_points: Array of shape (n_points, n_features)
    
    Returns:
        Tuple of (inside_flags, distances)
    """
    inside_flags = []
    distances = []
    
    for point in test_points:
        is_inside, distance = hull_wrapper.is_inside(point, return_distance=True)
        inside_flags.append(is_inside)
        distances.append(distance if distance is not None else 0.0)
    
    return np.array(inside_flags), np.array(distances)
