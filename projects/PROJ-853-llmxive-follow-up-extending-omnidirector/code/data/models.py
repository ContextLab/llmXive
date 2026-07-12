"""
Base data models for the OmniDirector pipeline.

Defines core dataclasses for GridFrame, CameraPose, and ReconstructedBox.
These models are used throughout the ingestion, geometry, and analysis phases.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
import numpy as np
from numpy.typing import NDArray


@dataclass
class GridFrame:
    """
    Represents a single frame containing a detected grid structure.

    Attributes:
        sequence_id: Unique identifier for the video sequence.
        frame_id: Index of the frame within the sequence.
        grid_points_2d: List of (x, y) pixel coordinates for detected grid intersections.
        radial_motion_deg: Radial camera motion in degrees for this frame.
        z_velocity: Z-axis velocity (units/frame) for this frame.
        randomized_depth: Boolean flag indicating if depth was randomized in this frame.
    """
    sequence_id: str
    frame_id: int
    grid_points_2d: List[Tuple[float, float]]
    radial_motion_deg: float
    z_velocity: float
    randomized_depth: bool = False

    def to_dict(self) -> dict:
        """Convert the GridFrame to a dictionary for serialization."""
        return {
            "sequence_id": self.sequence_id,
            "frame_id": self.frame_id,
            "grid_points_2d": self.grid_points_2d,
            "radial_motion_deg": self.radial_motion_deg,
            "z_velocity": self.z_velocity,
            "randomized_depth": self.randomized_depth
        }

    @staticmethod
    def from_dict(data: dict) -> "GridFrame":
        """Reconstruct a GridFrame from a dictionary."""
        return GridFrame(
            sequence_id=data["sequence_id"],
            frame_id=data["frame_id"],
            grid_points_2d=data["grid_points_2d"],
            radial_motion_deg=data["radial_motion_deg"],
            z_velocity=data["z_velocity"],
            randomized_depth=data.get("randomized_depth", False)
        )


@dataclass
class CameraPose:
    """
    Represents the 6-DOF camera pose (Rotation and Translation) relative to the world grid.

    Attributes:
        sequence_id: Unique identifier for the video sequence.
        frame_id: Index of the frame within the sequence.
        R_matrix: 3x3 Rotation matrix (numpy array).
        t_vector: 3x1 Translation vector (numpy array).
        source: Source of the pose (e.g., 'ground_truth', 'estimated').
    """
    sequence_id: str
    frame_id: int
    R_matrix: NDArray[np.float64]
    t_vector: NDArray[np.float64]
    source: str = "estimated"

    def __post_init__(self):
        """Ensure matrices are numpy arrays of correct shape."""
        if not isinstance(self.R_matrix, np.ndarray):
            self.R_matrix = np.array(self.R_matrix, dtype=np.float64)
        if not isinstance(self.t_vector, np.ndarray):
            self.t_vector = np.array(self.t_vector, dtype=np.float64)

        if self.R_matrix.shape != (3, 3):
            raise ValueError(f"R_matrix must be 3x3, got {self.R_matrix.shape}")
        if self.t_vector.shape not in [(3,), (3, 1)]:
            raise ValueError(f"t_vector must be 3x1 or (3,), got {self.t_vector.shape}")

    def to_dict(self) -> dict:
        """Convert the CameraPose to a dictionary for JSON serialization."""
        return {
            "sequence_id": self.sequence_id,
            "frame_id": self.frame_id,
            "R_matrix": self.R_matrix.tolist(),
            "t_vector": self.t_vector.flatten().tolist(),
            "source": self.source
        }

    @staticmethod
    def from_dict(data: dict) -> "CameraPose":
        """Reconstruct a CameraPose from a dictionary."""
        return CameraPose(
            sequence_id=data["sequence_id"],
            frame_id=data["frame_id"],
            R_matrix=np.array(data["R_matrix"], dtype=np.float64),
            t_vector=np.array(data["t_vector"], dtype=np.float64).flatten().reshape(3, 1),
            source=data.get("source", "estimated")
        )


@dataclass
class ReconstructedBox:
    """
    Represents the reconstructed 3D bounding box dimensions of the scene volume.

    Attributes:
        sequence_id: Unique identifier for the video sequence.
        width: Width of the box (x-axis).
        height: Height of the box (y-axis).
        depth: Depth of the box (z-axis).
        confidence: Confidence score of the reconstruction (0.0 to 1.0).
        status: Status of the reconstruction (e.g., 'success', 'failed', 'ambiguous').
        error_metric: Optional absolute error against ground truth if available.
    """
    sequence_id: str
    width: float
    height: float
    depth: float
    confidence: float = 1.0
    status: str = "success"
    error_metric: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert the ReconstructedBox to a dictionary."""
        return {
            "sequence_id": self.sequence_id,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "confidence": self.confidence,
            "status": self.status,
            "error_metric": self.error_metric
        }

    @staticmethod
    def from_dict(data: dict) -> "ReconstructedBox":
        """Reconstruct a ReconstructedBox from a dictionary."""
        return ReconstructedBox(
            sequence_id=data["sequence_id"],
            width=data["width"],
            height=data["height"],
            depth=data["depth"],
            confidence=data.get("confidence", 1.0),
            status=data.get("status", "success"),
            error_metric=data.get("error_metric")
        )

    def aspect_ratio(self) -> Tuple[float, float, float]:
        """Return the aspect ratio (W:H:D) normalized by the smallest dimension."""
        dims = np.array([self.width, self.height, self.depth])
        min_dim = np.min(dims)
        if min_dim == 0:
            return (1.0, 1.0, 1.0)
        return tuple((dims / min_dim).tolist())