import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from scipy.spatial import ConvexHull, Delaunay

from utils.logging_config import log_info_with_context, log_error_with_context, get_logger

logger = get_logger(__name__)

class ConvexHullWrapper:
    """Wrapper for scipy.spatial.ConvexHull with additional utilities."""
    
    def __init__(self, points: np.ndarray):
        self.points = points
        self.hull = ConvexHull(points)
        self.delaunay = Delaunay(points)
    
    def contains(self, point: np.ndarray) -> bool:
        """Tests if a point is inside the convex hull."""
        return self.delaunay.find_simplex(point) >= 0

def compute_convex_hull(points: np.ndarray) -> ConvexHullWrapper:
    """Computes the convex hull of a set of points."""
    return ConvexHullWrapper(points)

def test_points_in_hull(hull_wrapper: ConvexHullWrapper, points: np.ndarray) -> List[bool]:
    """Tests multiple points against the convex hull."""
    return [hull_wrapper.contains(p) for p in points]
