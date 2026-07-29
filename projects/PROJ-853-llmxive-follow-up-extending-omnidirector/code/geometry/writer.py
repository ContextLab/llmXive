import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from config import get_path

logger = logging.getLogger(__name__)


def serialize_ndarray(obj: np.ndarray) -> List[List[float]]:
    """
    Serializes a numpy array to a list of lists of floats for JSON compatibility.
    Handles 1D, 2D, and 3D arrays.
    """
    return obj.tolist()


def write_poses_and_boxes(
    poses_data: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Writes pose estimates and reconstructed box dimensions to a JSON file.

    Args:
        poses_data: List of dictionaries containing pose and box data.
                    Expected keys: 'sequence_id', 'frame_id', 'camera_pose',
                    'reconstructed_box', 'status', 'error_metrics' (optional).
        output_path: Optional path to write the JSON file. Defaults to
                     'data/processed/poses_estimated.json' based on config.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = get_path("POSES_ESTIMATED_JSON")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(poses_data)} pose/box records to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(poses_data, f, indent=2)

    logger.info(f"Successfully wrote poses to {output_file}")
    return str(output_file)


def main():
    """
    Main entry point for testing the writer module directly.
    Generates dummy data to demonstrate functionality.
    """
    logging.basicConfig(level=logging.INFO)

    # Generate dummy data matching the expected schema from T017/T018
    dummy_poses = [
        {
            "sequence_id": "seq_001",
            "frame_id": 1,
            "status": "success",
            "camera_pose": {
                "R": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                "t": [0.0, 0.0, 0.0]
            },
            "reconstructed_box": {
                "width": 1.0,
                "height": 1.0,
                "depth": 1.0
            }
        },
        {
            "sequence_id": "seq_001",
            "frame_id": 2,
            "status": "success",
            "camera_pose": {
                "R": [[0.99, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                "t": [0.01, 0.0, 0.0]
            },
            "reconstructed_box": {
                "width": 1.0,
                "height": 1.0,
                "depth": 1.0
            }
        }
    ]

    output_file = write_poses_and_boxes(dummy_poses)
    logger.info(f"Dummy data written to {output_file}")


if __name__ == "__main__":
    main()
