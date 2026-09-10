"""
Writer module for geometry outputs.
Handles serialization of poses and reconstructed boxes to JSON.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from config import get_path

logger = logging.getLogger(__name__)

def serialize_ndarray(obj: Any) -> Any:
    """
    Custom JSON encoder hook for numpy arrays.
    Converts numpy arrays to lists for JSON serialization.
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def write_poses_and_boxes(
    poses_data: List[Dict[str, Any]],
    boxes_data: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Combines pose estimates and reconstructed box dimensions into a single
    JSON structure and writes it to disk.

    Args:
        poses_data: List of dictionaries containing pose estimates (R, t, etc.)
        boxes_data: List of dictionaries containing reconstructed box dimensions
        output_path: Optional path to write the file. If None, uses config default.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = get_path("poses_estimated_json")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(poses_data)} pose estimates and {len(boxes_data)} box reconstructions to {output_path}")

    # Structure the output: a list of records, each containing both pose and box info
    # We assume poses_data and boxes_data are ordered by the same sequence_id/frame_id
    # or we merge them by sequence_id if available.
    # For robustness, we'll create a unified list where each entry corresponds to a frame.
    
    final_records = []
    
    # If lengths differ, we take the minimum and log a warning, or try to merge by ID.
    # Based on typical pipeline flow, these should be aligned lists of processed frames.
    min_len = min(len(poses_data), len(boxes_data))
    
    if len(poses_data) != len(boxes_data):
        logger.warning(f"Mismatch in number of poses ({len(poses_data)}) and boxes ({len(boxes_data)}). "
                       f"Writing first {min_len} pairs. Ensure processing order is consistent.")

    for i in range(min_len):
        record = {}
        # Add pose data
        record.update(poses_data[i])
        # Add box data
        if i < len(boxes_data):
            record.update(boxes_data[i])
        final_records.append(record)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_records, f, indent=2, default=serialize_ndarray)
        logger.info(f"Successfully wrote {len(final_records)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write JSON to {output_path}: {e}")
        raise

    return output_path

def main():
    """
    Entry point for testing the writer module directly.
    Generates sample data to verify serialization works.
    """
    import sys
    import tempfile
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create sample data matching expected schema from T017/T018
    sample_poses = [
        {
            "sequence_id": "seq_001",
            "frame_id": 1,
            "R_matrix": np.eye(3),
            "t_vector": np.array([0.0, 0.0, 0.0]),
            "success": True,
            "error": 0.0
        },
        {
            "sequence_id": "seq_001",
            "frame_id": 2,
            "R_matrix": np.eye(3) * 0.98, # Simulated rotation
            "t_vector": np.array([0.1, 0.0, 0.0]),
            "success": True,
            "error": 0.05
        }
    ]

    sample_boxes = [
        {
            "sequence_id": "seq_001",
            "frame_id": 1,
            "width": 1.0,
            "height": 1.0,
            "depth": 1.0,
            "volume": 1.0
        },
        {
            "sequence_id": "seq_001",
            "frame_id": 2,
            "width": 1.0,
            "height": 1.0,
            "depth": 1.0,
            "volume": 1.0
        }
    ]

    # Use a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        output_file = write_poses_and_boxes(sample_poses, sample_boxes, output_path=tmp_path)
        
        # Verify the file was written and can be read back
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2, "Expected 2 records"
        assert "R_matrix" in data[0], "Expected R_matrix in record"
        assert "width" in data[0], "Expected width in record"
        
        print(f"Verification passed. Output written to: {output_file}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

if __name__ == "__main__":
    main()
