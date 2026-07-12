"""
Bounding box dimension reconstruction from motion vectors.

Implements the reconstruction of bounding box dimensions (height, width, depth)
from camera motion vectors estimated by the solvePnP solver.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from config import get_path, get_config
from data.models import CameraPose, ReconstructedBox

logger = logging.getLogger(__name__)


def calculate_box_dimensions(
    poses: List[CameraPose],
    reference_pose: Optional[CameraPose] = None
) -> ReconstructedBox:
    """
    Calculate bounding box dimensions (height, width, depth) from a sequence of camera poses.

    The logic assumes the camera moves around a static object (the grid/bounding box).
    By analyzing the range of translation vectors relative to the object center,
    we can infer the dimensions of the object's bounding volume.

    Args:
        poses: List of CameraPose objects containing estimated R and t vectors.
        reference_pose: Optional reference pose to define the origin. If None,
                        the first pose in the list is used.

    Returns:
        ReconstructedBox object with estimated dimensions.
    """
    if not poses:
        raise ValueError("Cannot reconstruct dimensions from empty pose list.")

    if reference_pose is None:
        reference_pose = poses[0]

    # Extract translation vectors
    # t_vectors are typically in camera coordinates relative to the world origin (object center).
    # We collect the translation vectors of all frames.
    t_vectors = []
    for pose in poses:
        t_vectors.append(pose.t_vector)

    t_matrix = np.array(t_vectors)  # Shape: (N, 3)

    # Calculate the range (extent) of the camera positions in the world frame.
    # If the camera orbits the object, the span of the camera's position
    # corresponds to the span of the object's bounding box (assuming the camera
    # stays at a roughly constant distance or the object fills the view).
    #
    # Specifically, if the object is centered at (0,0,0), and the camera moves
    # along the surface of a sphere (or box) around it, the extent of the
    # camera positions (max - min) along each axis gives the dimensions of the
    # "viewing volume".
    #
    # However, in the context of "OmniDirector" and grid frames, the grid
    # defines the object boundaries. The solver estimates the camera pose
    # relative to the grid. If the grid is the bounding box of the object,
    # then the camera motion vectors (t) describe the camera's position relative
    # to the box center.
    #
    # To get the box dimensions, we look at the spread of the camera positions.
    # If the camera captures the entire grid from various angles, the min and max
    # of the camera's X, Y, Z coordinates (relative to the grid center) define
    # the extent of the grid itself.

    # Calculate min and max for each axis (X, Y, Z)
    min_vals = np.min(t_matrix, axis=0)
    max_vals = np.max(t_matrix, axis=0)

    # Dimensions are the span in each axis
    # X -> Width, Y -> Height, Z -> Depth (assuming standard convention)
    # Note: Coordinate system conventions may vary. Assuming:
    # X: Horizontal (Width)
    # Y: Vertical (Height)
    # Z: Depth (Forward/Backward)
    dimensions = max_vals - min_vals

    width = float(dimensions[0])
    height = float(dimensions[1])
    depth = float(dimensions[2])

    logger.info(
        f"Reconstructed dimensions: Width={width:.4f}, Height={height:.4f}, Depth={depth:.4f}"
    )

    return ReconstructedBox(
        width=width,
        height=height,
        depth=depth,
        center=(0.0, 0.0, 0.0),  # Assumed centered at origin
        confidence=1.0  # Placeholder confidence
    )


def reconstruct_sequence_dimensions(
    sequence_id: str,
    poses: List[CameraPose]
) -> Dict[str, Any]:
    """
    Reconstruct dimensions for a specific sequence and return a dictionary.

    Args:
        sequence_id: Identifier for the sequence.
        poses: List of CameraPose objects for the sequence.

    Returns:
        Dictionary containing sequence_id and reconstructed dimensions.
    """
    box = calculate_box_dimensions(poses)

    return {
        "sequence_id": sequence_id,
        "width": box.width,
        "height": box.height,
        "depth": box.depth,
        "num_frames": len(poses)
    }


def process_poses_for_reconstruction(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Main entry point to process poses and reconstruct bounding box dimensions.

    Reads from `data/processed/poses_estimated.json` (default) or a specified path.
    Writes results to `data/processed/reconstructed_boxes.json` (default) or a specified path.

    Args:
        input_path: Path to the JSON file containing estimated poses.
        output_path: Path to write the reconstructed dimensions.

    Returns:
        List of dictionaries with reconstruction results.
    """
    if input_path is None:
        input_path = str(get_path("poses_estimated_json"))
    if output_path is None:
        output_path = str(get_path("reconstructed_boxes_json"))

    logger.info(f"Reading poses from: {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r") as f:
        data = json.load(f)

    # Expected structure: {"sequences": [ { "sequence_id": "...", "poses": [...] }, ... ]}
    # Or simply a list of poses per sequence. We adapt to the structure from T019.
    # Assuming T019 produces: { "sequences": [ { "sequence_id": str, "poses": [ { "frame_id": int, "R": [...], "t": [...] } ] } ] }

    sequences = data.get("sequences", [])
    if not sequences:
        # Fallback if structure is different, e.g. direct list
        logger.warning("No 'sequences' key found. Checking if root is a list.")
        if isinstance(data, list):
            sequences = data
        else:
            raise ValueError("Unexpected JSON structure in poses file.")

    results = []
    for seq_data in sequences:
        seq_id = seq_data.get("sequence_id")
        if not seq_id:
            logger.warning(f"Skipping sequence entry without ID: {seq_data}")
            continue

        raw_poses = seq_data.get("poses", [])
        if not raw_poses:
            logger.warning(f"No poses found for sequence {seq_id}")
            continue

        # Convert raw pose dicts to CameraPose objects
        poses = []
        for p in raw_poses:
            R_list = p.get("R")
            t_list = p.get("t")
            if R_list and t_list:
                R = np.array(R_list, dtype=float).reshape(3, 3)
                t = np.array(t_list, dtype=float)
                poses.append(CameraPose(frame_id=p.get("frame_id", 0), R=R, t=t))

        if not poses:
            continue

        try:
            reconstruction = reconstruct_sequence_dimensions(seq_id, poses)
            results.append(reconstruction)
            logger.info(f"Reconstructed dimensions for {seq_id}: {reconstruction}")
        except Exception as e:
            logger.error(f"Failed to reconstruct dimensions for {seq_id}: {e}")
            # Continue processing other sequences
            continue

    # Write results
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Writing reconstruction results to: {output_path}")
    with open(output_path, "w") as f:
        json.dump({"reconstructed_boxes": results}, f, indent=2)

    return results


def main():
    """CLI entry point for dimension reconstruction."""
    logging.basicConfig(level=logging.INFO)
    try:
        results = process_poses_for_reconstruction()
        logger.info(f"Successfully reconstructed {len(results)} sequences.")
    except Exception as e:
        logger.error(f"Reconstruction process failed: {e}")
        raise


if __name__ == "__main__":
    main()