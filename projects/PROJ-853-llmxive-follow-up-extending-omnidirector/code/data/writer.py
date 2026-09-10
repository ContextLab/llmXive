import os
import json
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from config import get_path, load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serialize_grid_points(grid_points: List[List[float]]) -> str:
    """
    Serialize a list of 2D grid points (pixel coords) to a JSON string.
    Input: [[x1, y1], [x2, y2], ...]
    Output: "[[x1,y1],[x2,y2],...]"
    """
    if not grid_points:
        return "[]"
    return json.dumps(grid_points)


def parse_grid_points_2d(s: str) -> List[List[float]]:
    """
    Parse a serialized grid points string back to a list of lists.
    """
    if not s or s == "[]":
        return []
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse grid points: {s}")
        return []


def serialize_matrix(matrix: np.ndarray) -> str:
    """
    Serialize a numpy matrix (R_matrix) to a JSON string.
    Input: 3x3 numpy array
    Output: "[[r11,r12,r13],[r21,r22,r23],[r31,r32,r33]]"
    """
    if matrix is None or matrix.size == 0:
        return "[]"
    return json.dumps(matrix.tolist())


def parse_matrix_column(s: str) -> np.ndarray:
    """
    Parse a serialized matrix string back to a numpy array.
    """
    if not s or s == "[]":
        return np.zeros((3, 3))
    try:
        arr = np.array(json.loads(s))
        if arr.shape != (3, 3):
            logger.warning(f"Matrix shape mismatch: {arr.shape}, defaulting to zeros.")
            return np.zeros((3, 3))
        return arr
    except (json.JSONDecodeError, ValueError):
        logger.error(f"Failed to parse matrix: {s}")
        return np.zeros((3, 3))


def serialize_vector(vector: np.ndarray) -> str:
    """
    Serialize a numpy vector (t_vector) to a JSON string.
    Input: 3x1 or (3,) numpy array
    Output: "[t1,t2,t3]"
    """
    if vector is None or vector.size == 0:
        return "[]"
    return json.dumps(vector.tolist())


def parse_vector_column(s: str) -> np.ndarray:
    """
    Parse a serialized vector string back to a numpy array.
    """
    if not s or s == "[]":
        return np.zeros(3)
    try:
        arr = np.array(json.loads(s))
        if arr.shape != (3,):
            logger.warning(f"Vector shape mismatch: {arr.shape}, defaulting to zeros.")
            return np.zeros(3)
        return arr
    except (json.JSONDecodeError, ValueError):
        logger.error(f"Failed to parse vector: {s}")
        return np.zeros(3)


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def write_filtered_dataset(
    dataframe: Any,
    output_path: Path,
    checksum_path: Optional[Path] = None
) -> None:
    """
    Writes the filtered dataset to a CSV file with the required schema:
    sequence_id, frame_id, radial_motion_deg, z_velocity, grid_points_2d, R_matrix, t_vector, randomized_depth

    Also calculates and writes a SHA-256 checksum if checksum_path is provided.
    """
    if dataframe is None or dataframe.empty:
        logger.warning("DataFrame is empty. Writing empty CSV.")
        # Ensure the file exists even if empty, with headers
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "sequence_id", "frame_id", "radial_motion_deg", "z_velocity",
                "grid_points_2d", "R_matrix", "t_vector", "randomized_depth"
            ])
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare columns
    columns = [
        "sequence_id", "frame_id", "radial_motion_deg", "z_velocity",
        "grid_points_2d", "R_matrix", "t_vector", "randomized_depth"
    ]

    # Check if columns exist in dataframe
    missing_cols = [c for c in columns if c not in dataframe.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataframe: {missing_cols}")

    # Serialize complex columns
    df_to_write = dataframe.copy()

    # Serialize grid_points_2d if it's a list of lists
    if 'grid_points_2d' in df_to_write.columns:
        df_to_write['grid_points_2d'] = df_to_write['grid_points_2d'].apply(
            lambda x: serialize_grid_points(x) if isinstance(x, list) else json.dumps(x.tolist())
        )

    # Serialize R_matrix
    if 'R_matrix' in df_to_write.columns:
        df_to_write['R_matrix'] = df_to_write['R_matrix'].apply(
            lambda x: serialize_matrix(x) if isinstance(x, np.ndarray) else x
        )

    # Serialize t_vector
    if 't_vector' in df_to_write.columns:
        df_to_write['t_vector'] = df_to_write['t_vector'].apply(
            lambda x: serialize_vector(x) if isinstance(x, np.ndarray) else x
        )

    # Ensure boolean column is correct type
    if 'randomized_depth' in df_to_write.columns:
        df_to_write['randomized_depth'] = df_to_write['randomized_depth'].astype(bool)

    # Write to CSV
    df_to_write.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset written to {output_path} with {len(df_to_write)} rows.")

    # Calculate checksum
    if checksum_path:
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        checksum = calculate_sha256(output_path)
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        logger.info(f"Checksum written to {checksum_path}: {checksum}")


def main():
    """
    Main entry point to demonstrate writing the filtered dataset.
    This function is intended to be called by the pipeline after filtering.
    """
    config = load_config()
    output_path = get_path(config, "processed_filtered_sequences_csv")
    checksum_path = get_path(config, "processed_filtered_sequences_checksum")

    # This function expects the dataframe to be passed in or loaded from a previous step.
    # For the purpose of this task implementation, we assume the calling context (T009/T010)
    # has produced the dataframe. In a real pipeline, this would be passed as an argument
    # or loaded from an intermediate state.
    # However, to make this script runnable as a standalone artifact for T011,
    # we will attempt to load the pre-filtered data if it exists in memory (simulated)
    # or raise an error if not, as per the constraint "Implement the task for real".
    # Since T011 is the *writer*, we assume the data is ready in the pipeline context.
    # We will implement the logic to accept a dataframe argument if called,
    # but for the script entry point, we check if the input exists.

    # In the actual pipeline flow (T009 -> T011), the dataframe is passed.
    # Here we just define the function. The execution will be handled by the pipeline orchestrator.
    logger.info("Writer module loaded. Use write_filtered_dataset() to save data.")

    # If running as a script, we might need to simulate the input for testing
    # but the task is to implement the writer logic.
    # We will not generate fake data here as per constraints.
    # The pipeline runner will call write_filtered_dataset(df, output_path).


if __name__ == "__main__":
    main()