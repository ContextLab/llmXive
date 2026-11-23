"""
Dataset Ingestion Module for OmniDirector Project.

This module handles loading the OmniDirector dataset from zip archives (real or synthetic),
extracting grid-video pairs, and preparing data for geometric filtering.
"""
import os
import json
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, BinaryIO, Iterator
import pandas as pd
import numpy as np

from config import get_path, load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = [
    'sequence_id', 'frame_id', 'radial_motion_deg', 'z_velocity',
    'grid_points_2d', 'R_matrix', 't_vector', 'randomized_depth'
]

def ensure_output_directory(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def load_dataset_from_zip(zip_path: Path) -> pd.DataFrame:
    """
    Load dataset from a zip file containing a CSV.

    Args:
        zip_path: Path to the zip file (e.g., data/raw/omnidirector.zip)

    Returns:
        DataFrame containing the dataset
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Dataset zip file not found: {zip_path}")

    logger.info(f"Loading dataset from {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Find the CSV file inside the zip
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise ValueError(f"No CSV file found in {zip_path}")

        csv_file = csv_files[0]
        logger.info(f"Found CSV file: {csv_file}")

        # Read the CSV
        with zip_ref.open(csv_file) as f:
            df = pd.read_csv(f)

    logger.info(f"Loaded {len(df)} rows from {csv_file}")
    return df

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains all required columns.

    Args:
        df: DataFrame to validate

    Raises:
        ValueError: If required columns are missing
    """
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    logger.info("Schema validation passed")

def parse_grid_points_2d(points_str: str) -> List[Tuple[int, int]]:
    """
    Parse grid_points_2d string representation to list of tuples.

    Args:
        points_str: String representation of grid points, e.g., "[[10,20],[30,40]]"

    Returns:
        List of (x, y) tuples
    """
    if isinstance(points_str, list):
        return [tuple(p) for p in points_str]
    try:
        points = json.loads(points_str)
        return [tuple(p) for p in points]
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse grid points: {points_str}, error: {e}")
        return []

def parse_matrix_column(matrix_str: str) -> np.ndarray:
    """
    Parse R_matrix string representation to numpy array.

    Args:
        matrix_str: String representation of 3x3 matrix

    Returns:
        3x3 numpy array
    """
    if isinstance(matrix_str, np.ndarray):
        return matrix_str
    try:
        matrix = json.loads(matrix_str)
        return np.array(matrix, dtype=np.float32)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse matrix: {matrix_str}, error: {e}")
        return np.eye(3, dtype=np.float32)

def parse_vector_column(vector_str: str) -> np.ndarray:
    """
    Parse t_vector string representation to numpy array.

    Args:
        vector_str: String representation of 3-element vector

    Returns:
        3-element numpy array
    """
    if isinstance(vector_str, np.ndarray):
        return vector_str
    try:
        vector = json.loads(vector_str)
        return np.array(vector, dtype=np.float32)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse vector: {vector_str}, error: {e}")
        return np.zeros(3, dtype=np.float32)

def interpolate_missing_points(
    grid_points: List[Tuple[int, int]],
    expected_count: int = 16
) -> List[Tuple[int, int]]:
    """
    Interpolate missing grid points if count is less than expected.

    Args:
        grid_points: List of existing grid points
        expected_count: Expected number of points (default 16 for 4x4 grid)

    Returns:
        List of grid points, interpolated if necessary
    """
    if len(grid_points) >= expected_count:
        return grid_points[:expected_count]

    if not grid_points:
        # Return default grid if no points available
        logger.warning("No grid points available, returning default grid")
        return [(i * 50, j * 50) for i in range(4) for j in range(4)]

    # Simple interpolation: repeat existing points or use default pattern
    logger.warning(f"Only {len(grid_points)} points found, interpolating")
    result = []
    idx = 0
    for _ in range(expected_count):
        result.append(grid_points[idx % len(grid_points)])
        idx += 1
    return result

def create_grid_frames(
    df: pd.DataFrame,
    sequence_id: str
) -> List[Dict[str, Any]]:
    """
    Create grid frame records from DataFrame rows for a specific sequence.

    Args:
        df: DataFrame containing the dataset
        sequence_id: ID of the sequence to process

    Returns:
        List of grid frame dictionaries
    """
    sequence_df = df[df['sequence_id'] == sequence_id]
    grid_frames = []

    for _, row in sequence_df.iterrows():
        frame = {
            'sequence_id': row['sequence_id'],
            'frame_id': int(row['frame_id']),
            'radial_motion_deg': float(row['radial_motion_deg']),
            'z_velocity': float(row['z_velocity']),
            'grid_points_2d': parse_grid_points_2d(str(row['grid_points_2d'])),
            'R_matrix': parse_matrix_column(str(row['R_matrix'])),
            't_vector': parse_vector_column(str(row['t_vector'])),
            'randomized_depth': bool(row['randomized_depth'])
        }
        # Interpolate if needed
        frame['grid_points_2d'] = interpolate_missing_points(frame['grid_points_2d'])
        grid_frames.append(frame)

    return grid_frames

def extract_grid_video_pairs(
    df: pd.DataFrame
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract grid-video pairs grouped by sequence ID.

    Args:
        df: DataFrame containing the dataset

    Returns:
        Dictionary mapping sequence_id to list of grid frames
    """
    logger.info("Extracting grid-video pairs")
    pairs = {}
    sequence_ids = df['sequence_id'].unique()

    for seq_id in sequence_ids:
        pairs[str(seq_id)] = create_grid_frames(df, str(seq_id))

    logger.info(f"Extracted {len(pairs)} sequence pairs")
    return pairs

def apply_geometric_filter(
    df: pd.DataFrame,
    radial_threshold: float = 15.0,
    z_velocity_threshold: float = 0.1
) -> pd.DataFrame:
    """
    Apply geometric filtering based on radial motion and Z-axis velocity.

    Filters sequences where: radial_motion_deg > 15 OR z_velocity > 0.1

    Args:
        df: DataFrame containing the dataset
        radial_threshold: Threshold for radial motion in degrees
        z_velocity_threshold: Threshold for Z-axis velocity

    Returns:
        Filtered DataFrame with retained sequences
    """
    logger.info(f"Applying geometric filter: radial > {radial_threshold}° OR z_velocity > {z_velocity_threshold}")

    # Filter based on criteria
    mask = (df['radial_motion_deg'] > radial_threshold) | (df['z_velocity'] > z_velocity_threshold)
    filtered_df = df[mask].copy()

    logger.info(f"Retained {len(filtered_df)} rows out of {len(df)}")
    return filtered_df

def load_and_extract_dataset(
    raw_dir: Path,
    processed_dir: Path,
    use_real: bool = True
) -> Tuple[pd.DataFrame, Dict[str, List[Dict[str, Any]]]]:
    """
    Main function to load dataset and extract grid-video pairs.

    Args:
        raw_dir: Directory containing raw data zips
        processed_dir: Directory for processed outputs
        use_real: Whether to try loading real data first

    Returns:
        Tuple of (raw DataFrame, extracted grid-video pairs)
    """
    ensure_output_directory(processed_dir)

    # Determine which zip to load
    if use_real:
        zip_path = raw_dir / "omnidirector.zip"
        if not zip_path.exists():
            logger.warning(f"Real dataset not found at {zip_path}, falling back to synthetic")
            use_real = False

    if use_real:
        zip_path = raw_dir / "omnidirector.zip"
    else:
        zip_path = raw_dir / "synthetic_omnidirector.zip"
        if not zip_path.exists():
            raise FileNotFoundError(
                f"Neither real nor synthetic dataset found. "
                f"Expected: {raw_dir / 'omnidirector.zip'} or {raw_dir / 'synthetic_omnidirector.zip'}"
            )

    # Load dataset
    df = load_dataset_from_zip(zip_path)

    # Validate schema
    validate_schema(df)

    # Extract grid-video pairs
    pairs = extract_grid_video_pairs(df)

    return df, pairs

def main() -> None:
    """
    Main entry point for dataset ingestion.
    Loads dataset, validates schema, and extracts grid-video pairs.
    """
    config = load_config()
    raw_dir = get_path("raw_data_dir")
    processed_dir = get_path("processed_data_dir")

    try:
        df, pairs = load_and_extract_dataset(raw_dir, processed_dir)

        # Log summary
        logger.info(f"Dataset loaded successfully: {len(df)} rows, {len(pairs)} sequences")

        # Save extracted pairs to a JSON file for downstream tasks
        output_path = processed_dir / "grid_video_pairs.json"
        with open(output_path, 'w') as f:
            json.dump(pairs, f, indent=2, default=str)
        logger.info(f"Saved grid-video pairs to {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Data source error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()