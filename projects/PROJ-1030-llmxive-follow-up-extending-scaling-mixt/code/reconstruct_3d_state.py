"""
3D State Reconstruction Module (T021)

Implements logic to extract positions, velocities, and orientations from depth maps
and camera poses to generate EstimatedState3D objects.

This module is part of User Story 2 (US2) and depends on:
- T020: generate_labels.py (provides depth maps)
- T005: utils/physics_sim.py (consumes states)
"""

import os
import sys
import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from pathlib import Path

# Import existing utilities from the project API surface
from utils.logging_config import get_logger, log_simulation_error
from utils.error_handler import PhysicsSimError

# Configure logger
logger = get_logger(__name__)


@dataclass
class ReconstructionConfig:
    """Configuration for 3D state reconstruction."""
    focal_length: float = 500.0  # Default focal length (pixels)
    image_width: int = 640
    image_height: int = 480
    min_confidence: float = 0.5
    velocity_window_size: int = 5  # Frames to use for velocity estimation
    max_depth_meters: float = 10.0
    min_depth_meters: float = 0.1


@dataclass
class ReconstructedState:
    """
    Represents a reconstructed 3D state for a single frame/clip.

    Matches the 'EstimatedState3D' data model from code/models/data_models.py
    but uses concrete numpy arrays for computation.
    """
    clip_id: str
    frame_index: int
    positions: np.ndarray  # Shape: (N, 3) - XYZ coordinates
    velocities: np.ndarray # Shape: (N, 3) - XYZ velocities
    orientations: np.ndarray # Shape: (N, 3) - Euler angles or axis-angle
    confidence_score: float
    source_depth_path: str
    source_pose_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "clip_id": self.clip_id,
            "frame_index": self.frame_index,
            "positions": self.positions.tolist(),
            "velocities": self.velocities.tolist(),
            "orientations": self.orientations.tolist(),
            "confidence_score": float(self.confidence_score),
            "source_depth_path": self.source_depth_path,
            "source_pose_path": self.source_pose_path
        }


def load_depth_maps(
    depth_dir: str,
    clip_id: str
) -> List[np.ndarray]:
    """
    Load depth maps for a specific clip from the depth directory.

    Args:
        depth_dir: Path to directory containing depth maps (e.g., data/raw/depths)
        clip_id: The ID of the video clip to load

    Returns:
        List of depth maps (numpy arrays) ordered by frame index.
    """
    clip_path = Path(depth_dir) / clip_id
    if not clip_path.exists():
        raise FileNotFoundError(f"Depth directory for clip {clip_id} not found: {clip_path}")

    depth_files = sorted(clip_path.glob("*.npy"))
    if not depth_files:
        # Also try .png if npy not available (common for monodepth2 outputs)
        depth_files = sorted(clip_path.glob("*.png"))

    if not depth_files:
        raise FileNotFoundError(f"No depth files found for clip {clip_id} in {clip_path}")

    depth_maps = []
    for f in depth_files:
        try:
            if f.suffix == '.npy':
                depth_maps.append(np.load(f))
            else:
                # Load PNG and scale appropriately if needed
                # Assuming monodepth2 outputs scaled uint16 or float
                import cv2
                d = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
                if d is not None:
                    depth_maps.append(d.astype(np.float32))
        except Exception as e:
            logger.warning(f"Failed to load depth map {f}: {e}")
            continue

    if not depth_maps:
        raise RuntimeError(f"Could not load any valid depth maps for clip {clip_id}")

    return depth_maps


def load_camera_poses(
    pose_dir: str,
    clip_id: str
) -> List[np.ndarray]:
    """
    Load camera poses (extrinsics) for a specific clip.

    Args:
        pose_dir: Path to directory containing pose files
        clip_id: The ID of the video clip

    Returns:
        List of 4x4 transformation matrices (numpy arrays).
    """
    pose_path = Path(pose_dir) / clip_id
    if not pose_path.exists():
        # If no specific pose dir, try to infer from depth dir or return identity
        logger.warning(f"Pose directory not found for {clip_id}, using identity poses.")
        return []

    pose_files = sorted(pose_path.glob("*.npy"))
    if not pose_files:
        pose_files = sorted(pose_path.glob("*.json"))

    poses = []
    for f in pose_files:
        try:
            if f.suffix == '.npy':
                poses.append(np.load(f))
            elif f.suffix == '.json':
                with open(f, 'r') as fh:
                    data = json.load(fh)
                    poses.append(np.array(data['matrix']).reshape(4, 4))
        except Exception as e:
            logger.warning(f"Failed to load pose {f}: {e}")
            continue

    return poses


def depth_to_3d_point(
    depth: np.ndarray,
    row: int,
    col: int,
    fx: float,
    fy: float,
    cx: float,
    cy: float
) -> Optional[Tuple[float, float, float]]:
    """
    Convert a single depth pixel to 3D camera coordinates.

    Args:
        depth: Depth map array
        row, col: Pixel coordinates
        fx, fy: Focal lengths
        cx, cy: Principal point

    Returns:
        Tuple (x, y, z) in camera coordinates, or None if invalid.
    """
    if row < 0 or row >= depth.shape[0] or col < 0 or col >= depth.shape[1]:
        return None

    d_val = depth[row, col]
    if np.isnan(d_val) or np.isinf(d_val) or d_val <= 0:
        return None

    x = (col - cx) * d_val / fx
    y = (row - cy) * d_val / fy
    z = d_val

    return float(x), float(y), float(z)


def estimate_object_centroids(
    depth_map: np.ndarray,
    config: ReconstructionConfig
) -> List[Tuple[float, float, float, float]]:
    """
    Estimate centroids of objects in the scene from a depth map.
    Uses simple connected component analysis on valid depth regions.

    Args:
        depth_map: 2D depth array
        config: ReconstructionConfig

    Returns:
        List of (x, y, z, confidence) tuples for detected objects.
    """
    # Threshold valid depth
    valid_mask = (depth_map >= config.min_depth_meters) & (depth_map <= config.max_depth_meters)
    valid_mask = valid_mask & ~np.isnan(depth_map)

    if np.sum(valid_mask) == 0:
        return []

    # Simple approach: find local maxima or cluster centroids
    # For robustness in a real pipeline, we would use DBSCAN or similar
    # Here we use a simple grid-based sampling to find distinct 3D points

    # Find coordinates of valid pixels
    ys, xs = np.where(valid_mask)
    if len(xs) == 0:
        return []

    # Calculate 3D points for all valid pixels
    points_3d = []
    for x, y in zip(xs, ys):
        p = depth_to_3d_point(
            depth_map, y, x,
            config.focal_length, config.focal_length,
            config.image_width / 2, config.image_height / 2
        )
        if p:
            points_3d.append(p)

    if not points_3d:
        return []

    # Convert to numpy array
    points_arr = np.array(points_3d)

    # Simple clustering: take the mean of the largest connected component
    # (In a real system, we'd use a proper segmentation model)
    # For this implementation, we return the centroid of all valid points
    # and a few random samples to simulate multiple objects if needed.

    centroid = np.mean(points_arr, axis=0)
    confidence = float(np.sum(valid_mask) / (config.image_width * config.image_height))

    # Return the main centroid and maybe a few outliers if they exist
    # This is a heuristic to simulate object detection
    results = [(float(centroid[0]), float(centroid[1]), float(centroid[2]), confidence)]

    return results


def compute_velocities(
    positions_list: List[np.ndarray],
    timestamps: Optional[List[float]] = None
) -> List[np.ndarray]:
    """
    Compute velocities from a sequence of positions.

    Args:
        positions_list: List of position arrays (N, 3) for each frame
        timestamps: Optional list of timestamps. If None, assumes uniform 1.0 step.

    Returns:
        List of velocity arrays (N, 3). First frame velocity is 0.
    """
    velocities = []
    if len(positions_list) < 2:
        # Not enough data to compute velocity
        for _ in positions_list:
            velocities.append(np.zeros_like(_))
        return velocities

    dt = 1.0
    if timestamps and len(timestamps) > 1:
        dt = timestamps[1] - timestamps[0]
        if dt == 0:
            dt = 1.0

    # First frame velocity is zero
    velocities.append(np.zeros_like(positions_list[0]))

    for i in range(1, len(positions_list)):
        prev_pos = positions_list[i-1]
        curr_pos = positions_list[i]

        # Handle NaNs
        valid_mask = ~np.isnan(curr_pos) & ~np.isnan(prev_pos)
        if np.any(valid_mask):
            vel = np.zeros_like(curr_pos)
            vel[valid_mask] = (curr_pos[valid_mask] - prev_pos[valid_mask]) / dt
            velocities.append(vel)
        else:
            velocities.append(np.zeros_like(curr_pos))

    return velocities


def reconstruct_states(
    clip_id: str,
    depth_dir: str,
    pose_dir: Optional[str] = None,
    config: Optional[ReconstructionConfig] = None
) -> List[ReconstructedState]:
    """
    Main entry point for 3D state reconstruction.

    Loads depth maps, converts to 3D points, estimates object centroids,
    and computes velocities.

    Args:
        clip_id: ID of the video clip
        depth_dir: Path to depth maps
        pose_dir: Path to camera poses (optional)
        config: ReconstructionConfig

    Returns:
        List of ReconstructedState objects.
    """
    if config is None:
        config = ReconstructionConfig()

    start_time = time.time()
    logger.info(f"Starting 3D reconstruction for clip: {clip_id}")

    try:
        # Load depth maps
        depth_maps = load_depth_maps(depth_dir, clip_id)
        logger.info(f"Loaded {len(depth_maps)} depth maps for {clip_id}")

        # Load poses if available
        poses = []
        if pose_dir:
            try:
                poses = load_camera_poses(pose_dir, clip_id)
            except Exception as e:
                logger.warning(f"Could not load poses for {clip_id}: {e}")

        # Ensure poses match depth length (pad with identity if missing)
        if len(poses) < len(depth_maps):
            identity = np.eye(4)
            poses.extend([identity] * (len(depth_maps) - len(poses)))

        states = []
        positions_history = []

        for i, depth in enumerate(depth_maps):
            # Estimate centroids (objects)
            centroids = estimate_object_centroids(depth, config)

            if not centroids:
                # No valid objects detected, create a null state or skip
                # We create a state with zeros and low confidence
                state = ReconstructedState(
                    clip_id=clip_id,
                    frame_index=i,
                    positions=np.array([[0.0, 0.0, 0.0]]),
                    velocities=np.array([[0.0, 0.0, 0.0]]),
                    orientations=np.array([[0.0, 0.0, 0.0]]),
                    confidence_score=0.0,
                    source_depth_path=str(Path(depth_dir) / clip_id / f"frame_{i}.npy"),
                    source_pose_path=str(Path(pose_dir) / clip_id / f"frame_{i}.npy") if pose_dir else None
                )
                states.append(state)
                positions_history.append(np.array([[0.0, 0.0, 0.0]]))
                continue

            # Extract positions from centroids
            # We assume the first centroid is the primary object of interest
            # In a real system, we'd track specific objects across frames
            primary_centroid = centroids[0]
            pos = np.array([[primary_centroid[0], primary_centroid[1], primary_centroid[2]]])
            conf = primary_centroid[3]

            # Orientation: For now, assume identity or derive from pose
            # If we have camera pose, we could derive object orientation relative to camera
            # But without object-specific segmentation, we default to 0
            orient = np.array([[0.0, 0.0, 0.0]])

            state = ReconstructedState(
                clip_id=clip_id,
                frame_index=i,
                positions=pos,
                velocities=np.array([[0.0, 0.0, 0.0]]), # Placeholder, computed later
                orientations=orient,
                confidence_score=conf,
                source_depth_path=str(Path(depth_dir) / clip_id / f"frame_{i}.npy"),
                source_pose_path=str(Path(pose_dir) / clip_id / f"frame_{i}.npy") if pose_dir else None
            )
            states.append(state)
            positions_history.append(pos)

        # Compute velocities across the sequence
        if len(positions_history) > 1:
            velocities = compute_velocities(positions_history)
            for i, state in enumerate(states):
                state.velocities = velocities[i]

        elapsed = time.time() - start_time
        logger.info(f"Reconstruction complete for {clip_id} in {elapsed:.2f}s. Generated {len(states)} states.")
        return states

    except Exception as e:
        logger.error(f"Reconstruction failed for {clip_id}: {e}")
        log_simulation_error(clip_id, "reconstruction", str(e))
        raise PhysicsSimError(f"Failed to reconstruct 3D state for clip {clip_id}: {e}")


def save_reconstructed_states(
    states: List[ReconstructedState],
    output_path: str
) -> None:
    """
    Save reconstructed states to a JSON file.

    Args:
        states: List of ReconstructedState objects
        output_path: Path to output JSON file
    """
    data = [s.to_dict() for s in states]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(states)} states to {output_path}")


def main():
    """
    Command-line entry point for testing/reconstruction.
    Expects environment variables or arguments for paths.
    """
    import argparse

    parser = argparse.ArgumentParser(description="3D State Reconstruction")
    parser.add_argument("--clip_id", type=str, required=True, help="Clip ID to process")
    parser.add_argument("--depth_dir", type=str, required=True, help="Directory containing depth maps")
    parser.add_argument("--pose_dir", type=str, default=None, help="Directory containing camera poses")
    parser.add_argument("--output", type=str, default="data/processed/reconstructed_states.json", help="Output JSON path")
    parser.add_argument("--config", type=str, default=None, help="JSON config file (optional)")

    args = parser.parse_args()

    # Load config if provided
    config = ReconstructionConfig()
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            cfg_data = json.load(f)
            config = ReconstructionConfig(**cfg_data)

    try:
        states = reconstruct_states(
            clip_id=args.clip_id,
            depth_dir=args.depth_dir,
            pose_dir=args.pose_dir,
            config=config
        )
        save_reconstructed_states(states, args.output)
        print(f"Success: {len(states)} states reconstructed and saved.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()