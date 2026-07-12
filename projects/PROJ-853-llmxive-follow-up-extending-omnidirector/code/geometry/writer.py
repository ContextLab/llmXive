import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


def serialize_ndarray(arr: Optional[np.ndarray]) -> Any:
    """
    Serializes a numpy array to a JSON-compatible list.
    Handles None and empty arrays gracefully.
    """
    if arr is None:
        return None
    if isinstance(arr, np.ndarray):
        return arr.tolist()
    # Fallback for scalar or list
    return arr


def write_poses_and_boxes(
    poses: List[Dict[str, Any]],
    boxes: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """
    Writes pose estimates and reconstructed boxes to a single JSON file.

    Args:
        poses: List of dictionaries containing camera pose data (R, t, sequence_id, frame_id).
        boxes: List of dictionaries containing reconstructed box data (dimensions, sequence_id).
        output_path: Path to the output JSON file.

    The output structure is:
    {
        "metadata": { "version": "1.0", "count_poses": int, "count_boxes": int },
        "poses": [ ... ],
        "boxes": [ ... ]
    }
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Ensure arrays are serialized correctly
    serialized_poses = []
    for p in poses:
        rec = p.copy()
        if 'R_matrix' in rec:
            rec['R_matrix'] = serialize_ndarray(rec['R_matrix'])
        if 't_vector' in rec:
            rec['t_vector'] = serialize_ndarray(rec['t_vector'])
        if 'rotation_vec' in rec:
            rec['rotation_vec'] = serialize_ndarray(rec['rotation_vec'])
        if 'translation_vec' in rec:
            rec['translation_vec'] = serialize_ndarray(rec['translation_vec'])
        serialized_poses.append(rec)

    serialized_boxes = []
    for b in boxes:
        rec = b.copy()
        if 'dimensions' in rec:
            rec['dimensions'] = serialize_ndarray(rec['dimensions'])
        serialized_boxes.append(rec)

    output_data = {
        "metadata": {
            "version": "1.0",
            "count_poses": len(serialized_poses),
            "count_boxes": len(serialized_boxes)
        },
        "poses": serialized_poses,
        "boxes": serialized_boxes
    }

    with open(output_path_obj, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Wrote {len(serialized_poses)} poses and {len(serialized_boxes)} boxes to {output_path}")


def main() -> None:
    """
    Entry point for writing poses and boxes.
    Expects environment variables or default paths for input data if not passed via args.
    For T019, this is primarily a utility called by the solver pipeline,
    but provided here for standalone execution if needed.
    """
    # Default paths based on project structure
    poses = []
    boxes = []
    
    # In a real pipeline, these would be populated by solver.py or reconstruction.py
    # For this artifact implementation, we define the writer logic.
    # If run standalone, it writes an empty structure or raises if no data provided.
    
    # Example usage logic (commented out to prevent errors if run without data source):
    # output_path = get_path("processed_poses_json") 
    # write_poses_and_boxes(poses, boxes, output_path)
    
    logger.info("Writer module loaded. Call write_poses_and_boxes with data.")


if __name__ == "__main__":
    main()