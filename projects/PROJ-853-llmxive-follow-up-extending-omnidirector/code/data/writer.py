import os
import json
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Import existing helpers from ingestion if needed, though we define serialization here
from data.ingestion import parse_grid_points_2d, parse_matrix_column, parse_vector_column

logger = logging.getLogger(__name__)

def serialize_grid_points(grid_points: Any) -> str:
    """
    Serializes a list of 2D grid points (list of lists or numpy array) to a JSON string.
    Input: [[x1, y1], [x2, y2], ...] or np.array
    Output: JSON string representation.
    """
    if isinstance(grid_points, np.ndarray):
        grid_points = grid_points.tolist()
    return json.dumps(grid_points)

def parse_grid_points_2d(json_str: str) -> List[List[float]]:
    """
    Parses a JSON string back into a list of 2D points.
    """
    if not json_str:
        return []
    return json.loads(json_str)

def serialize_matrix(matrix: Any) -> str:
    """
    Serializes a 3x3 rotation matrix (list of lists or numpy array) to a JSON string.
    """
    if isinstance(matrix, np.ndarray):
        matrix = matrix.tolist()
    return json.dumps(matrix)

def parse_matrix_column(json_str: str) -> List[List[float]]:
    """
    Parses a JSON string back into a 3x3 matrix.
    """
    if not json_str:
        return [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    return json.loads(json_str)

def serialize_vector(vector: Any) -> str:
    """
    Serializes a 3-element translation vector (list or numpy array) to a JSON string.
    """
    if isinstance(vector, np.ndarray):
        vector = vector.tolist()
    return json.dumps(vector)

def parse_vector_column(json_str: str) -> List[float]:
    """
    Parses a JSON string back into a 3-element vector.
    """
    if not json_str:
        return [0.0, 0.0, 0.0]
    return json.loads(json_str)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_filtered_dataset(
    data: List[Dict[str, Any]],
    output_path: Path,
    checksum_path: Optional[Path] = None
) -> None:
    """
    Writes the filtered dataset to a CSV file at `output_path`.
    
    Schema:
    - sequence_id
    - frame_id
    - radial_motion_deg
    - z_velocity
    - grid_points_2d (JSON string)
    - R_matrix (JSON string)
    - t_vector (JSON string)
    - randomized_depth (boolean)
    
    Also writes a checksum file if `checksum_path` is provided.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing filtered dataset to {output_path}")
    
    fieldnames = [
        "sequence_id",
        "frame_id",
        "radial_motion_deg",
        "z_velocity",
        "grid_points_2d",
        "R_matrix",
        "t_vector",
        "randomized_depth"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in data:
            # Ensure serialization of complex types
            row_data = {
                "sequence_id": row.get("sequence_id", ""),
                "frame_id": row.get("frame_id", 0),
                "radial_motion_deg": row.get("radial_motion_deg", 0.0),
                "z_velocity": row.get("z_velocity", 0.0),
                "randomized_depth": row.get("randomized_depth", False),
            }

            # Serialize grid_points_2d
            gp = row.get("grid_points_2d", [])
            row_data["grid_points_2d"] = serialize_grid_points(gp)

            # Serialize R_matrix
            rm = row.get("R_matrix", np.zeros((3, 3)))
            row_data["R_matrix"] = serialize_matrix(rm)

            # Serialize t_vector
            tv = row.get("t_vector", np.zeros(3))
            row_data["t_vector"] = serialize_vector(tv)

            writer.writerow(row_data)

    logger.info(f"Successfully wrote {len(data)} rows to {output_path}")

    if checksum_path:
        checksum = calculate_sha256(output_path)
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checksum_path, 'w', encoding='utf-8') as f:
            f.write(f"{checksum}  {output_path.name}\n")
        logger.info(f"Checksum written to {checksum_path}: {checksum}")

def main():
    """
    Entry point for testing or running the writer directly if needed.
    In the pipeline, this is called by the ingestion or preprocessing stage.
    """
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example usage for verification
    sample_data = [
        {
            "sequence_id": "seq_001",
            "frame_id": 0,
            "radial_motion_deg": 15.5,
            "z_velocity": 0.15,
            "grid_points_2d": [[10, 10], [20, 20]],
            "R_matrix": np.eye(3),
            "t_vector": [0.1, 0.2, 0.3],
            "randomized_depth": False
        }
    ]
    
    output_file = Path("data/processed/filtered_sequences.csv")
    checksum_file = Path("data/processed/filtered_sequences.csv.sha256")
    
    write_filtered_dataset(sample_data, output_file, checksum_file)

if __name__ == "__main__":
    main()