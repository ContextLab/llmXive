"""
Geometry utilities for the OmniDirector pipeline.
Defines the canonical World Grid Model and helper functions for geometric operations.
"""
import numpy as np
from typing import List, Tuple, Union, Optional
from numpy.typing import NDArray

# Default grid configuration constants
DEFAULT_GRID_SIZE = 10  # 10x10 grid
DEFAULT_SPACING = 1.0   # 1.0 unit spacing between points
DEFAULT_Z_PLANE = 0.0   # Grid lies on Z=0 plane

class WorldGridModel:
    """
    Represents a canonical unit grid in 3D world space.
    
    The grid is defined as a set of points lying on the Z=0 plane,
    arranged in a regular square lattice.
    
    Attributes:
        size (int): Number of points along one dimension (total points = size^2).
        spacing (float): Distance between adjacent grid points.
        z_plane (float): Z-coordinate of the plane (default 0.0).
        points_3d (NDArray): Array of shape (N, 3) containing 3D coordinates.
        points_2d (NDArray): Array of shape (N, 2) containing projected 2D coordinates (X, Y).
    """
    
    def __init__(
        self, 
        size: int = DEFAULT_GRID_SIZE, 
        spacing: float = DEFAULT_SPACING, 
        z_plane: float = DEFAULT_Z_PLANE
    ):
        """
        Initialize the World Grid Model.
        
        Args:
            size: Number of points along one dimension (e.g., 10 for a 10x10 grid).
            spacing: Distance between adjacent points in world units.
            z_plane: Z-coordinate where the grid is placed.
        """
        self.size = size
        self.spacing = spacing
        self.z_plane = z_plane
        
        # Generate the grid points
        self._generate_points()
    
    def _generate_points(self) -> None:
        """Generate the 3D and 2D coordinates for the grid."""
        # Create 1D arrays for X and Y coordinates
        x_coords = np.arange(self.size) * self.spacing
        y_coords = np.arange(self.size) * self.spacing
        
        # Create a meshgrid
        xx, yy = np.meshgrid(x_coords, y_coords)
        
        # Flatten to get 1D arrays of coordinates
        x_flat = xx.flatten()
        y_flat = yy.flatten()
        
        # Create Z array (all points on the same plane)
        z_flat = np.full_like(x_flat, self.z_plane, dtype=np.float64)
        
        # Stack into (N, 3) array
        self.points_3d = np.stack([x_flat, y_flat, z_flat], axis=1).astype(np.float64)
        
        # Create 2D projection (X, Y) for convenience
        self.points_2d = np.stack([x_flat, y_flat], axis=1).astype(np.float64)
    
    def get_points_3d(self) -> NDArray[np.float64]:
        """
        Get the 3D coordinates of all grid points.
        
        Returns:
            NDArray: Array of shape (N, 3) with 3D coordinates.
        """
        return self.points_3d
    
    def get_points_2d(self) -> NDArray[np.float64]:
        """
        Get the 2D (X, Y) coordinates of all grid points.
        
        Returns:
            NDArray: Array of shape (N, 2) with 2D coordinates.
        """
        return self.points_2d
    
    def get_size(self) -> int:
        """Return the number of points along one dimension."""
        return self.size
    
    def get_total_points(self) -> int:
        """Return the total number of points in the grid."""
        return self.size * self.size
    
    def __repr__(self) -> str:
        return (
            f"WorldGridModel(size={self.size}, spacing={self.spacing}, "
            f"z_plane={self.z_plane}, total_points={self.get_total_points()})"
        )


def create_default_world_grid() -> WorldGridModel:
    """
    Create a default WorldGridModel instance.
    
    Returns:
        WorldGridModel: A grid with default parameters (10x10, spacing=1.0, Z=0).
    """
    return WorldGridModel()


def get_grid_points_as_object_points(
    grid_model: WorldGridModel
) -> NDArray[np.float32]:
    """
    Convert WorldGridModel points to OpenCV object points format (float32).
    
    This is useful for passing to cv2.solvePnP or similar functions.
    
    Args:
        grid_model: The WorldGridModel instance.
        
    Returns:
        NDArray: Array of shape (N, 3) with float32 dtype.
    """
    return grid_model.get_points_3d().astype(np.float32)


def detect_orthogonal_grid_lines(
    grid_points_2d: NDArray[np.float64],
    tolerance_deg: float = 5.0
) -> Tuple[List[Tuple[int, ...]], List[Tuple[int, ...]]]:
    """
    Detect orthogonal grid lines from a set of 2D grid points.
    
    This function groups points into horizontal and vertical lines based on their
    geometric arrangement. It assumes the input points form a regular grid structure
    (possibly distorted by perspective).
    
    Args:
        grid_points_2d: Array of shape (N, 2) containing 2D pixel coordinates.
        tolerance_deg: Maximum angular deviation (in degrees) from perfect orthogonality
                       allowed when grouping lines.
    
    Returns:
        Tuple containing:
            - horizontal_lines: List of tuples, each containing indices of points in a horizontal line.
            - vertical_lines: List of tuples, each containing indices of points in a vertical line.
    """
    if len(grid_points_2d) == 0:
        return [], []
    
    # Sort points by Y coordinate to identify rows
    # We'll use a clustering approach based on Y-coordinate proximity
    points = grid_points_2d.copy()
    indices = np.arange(len(points))
    
    # Sort by Y coordinate
    y_sorted_idx = np.argsort(points[:, 1])
    sorted_points = points[y_sorted_idx]
    sorted_indices = indices[y_sorted_idx]
    
    # Cluster points into rows based on Y-coordinate proximity
    rows = []
    if len(sorted_points) > 0:
        current_row = [sorted_indices[0]]
        current_y = sorted_points[0, 1]
        
        for i in range(1, len(sorted_points)):
            y_diff = abs(sorted_points[i, 1] - current_y)
            # Use a threshold based on grid spacing (assume min spacing is ~10 pixels for detection)
            if y_diff < 10.0:  # pixels
                current_row.append(sorted_indices[i])
            else:
                # Sort current row by X coordinate and add to rows
                current_row_sorted = sorted(current_row, key=lambda idx: points[idx, 0])
                rows.append(tuple(current_row_sorted))
                current_row = [sorted_indices[i]]
                current_y = sorted_points[i, 1]
        
        # Add the last row
        if current_row:
            current_row_sorted = sorted(current_row, key=lambda idx: points[idx, 0])
            rows.append(tuple(current_row_sorted))
    
    # Now cluster points into columns based on X-coordinate proximity
    x_sorted_idx = np.argsort(points[:, 0])
    sorted_points_x = points[x_sorted_idx]
    sorted_indices_x = indices[x_sorted_idx]
    
    columns = []
    if len(sorted_points_x) > 0:
        current_col = [sorted_indices_x[0]]
        current_x = sorted_points_x[0, 0]
        
        for i in range(1, len(sorted_points_x)):
            x_diff = abs(sorted_points_x[i, 0] - current_x)
            if x_diff < 10.0:  # pixels
                current_col.append(sorted_indices_x[i])
            else:
                # Sort current column by Y coordinate and add to columns
                current_col_sorted = sorted(current_col, key=lambda idx: points[idx, 1])
                columns.append(tuple(current_col_sorted))
                current_col = [sorted_indices_x[i]]
                current_x = sorted_points_x[i, 0]
        
        # Add the last column
        if current_col:
            current_col_sorted = sorted(current_col, key=lambda idx: points[idx, 1])
            columns.append(tuple(current_col_sorted))
    
    return rows, columns


def compute_line_intersection(
    line1_points: List[Tuple[int, ...]],
    line2_points: List[Tuple[int, ...]],
    grid_points_2d: NDArray[np.float64]
) -> Optional[Tuple[float, float]]:
    """
    Compute the intersection point of two lines defined by sets of 2D points.
    
    Args:
        line1_points: List of point indices defining the first line.
        line2_points: List of point indices defining the second line.
        grid_points_2d: Array of shape (N, 2) containing all 2D coordinates.
    
    Returns:
        Tuple (x, y) of the intersection point, or None if lines are parallel.
    """
    if len(line1_points) < 2 or len(line2_points) < 2:
        return None
    
    # Fit lines using least squares
    pts1 = grid_points_2d[list(line1_points)]
    pts2 = grid_points_2d[list(line2_points)]
    
    # Fit line 1: y = m1*x + c1
    try:
        m1, c1 = np.polyfit(pts1[:, 0], pts1[:, 1], 1)
    except np.linalg.LinAlgError:
        return None
    
    # Fit line 2: y = m2*x + c2
    try:
        m2, c2 = np.polyfit(pts2[:, 0], pts2[:, 1], 1)
    except np.linalg.LinAlgError:
        return None
    
    # Check if lines are parallel (slopes are equal)
    if abs(m1 - m2) < 1e-6:
        return None
    
    # Calculate intersection
    x = (c2 - c1) / (m1 - m2)
    y = m1 * x + c1
    
    return (float(x), float(y))


def find_grid_intersections(
    horizontal_lines: List[Tuple[int, ...]],
    vertical_lines: List[Tuple[int, ...]],
    grid_points_2d: NDArray[np.float64]
) -> List[Tuple[float, float, int, int]]:
    """
    Find all intersection points between horizontal and vertical grid lines.
    
    Args:
        horizontal_lines: List of tuples containing point indices for horizontal lines.
        vertical_lines: List of tuples containing point indices for vertical lines.
        grid_points_2d: Array of shape (N, 2) containing all 2D coordinates.
    
    Returns:
        List of tuples (x, y, h_line_idx, v_line_idx) for each intersection.
    """
    intersections = []
    
    for h_idx, h_line in enumerate(horizontal_lines):
        for v_idx, v_line in enumerate(vertical_lines):
            intersection = compute_line_intersection(h_line, v_line, grid_points_2d)
            if intersection is not None:
                intersections.append((intersection[0], intersection[1], h_idx, v_idx))
    
    return intersections