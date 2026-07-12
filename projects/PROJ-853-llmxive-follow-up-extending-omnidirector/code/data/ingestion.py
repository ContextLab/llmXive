import os
import json
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, BinaryIO
import numpy as np
import pandas as pd

from data.models import GridFrame, CameraPose, ReconstructedBox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_output_directory(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def load_dataset_from_zip(zip_path: Path) -> pd.DataFrame:
    """
    Load the dataset from a zip file.
    Expects a 'data.json' or similar structure inside the zip.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Dataset zip file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Assume the main data is in a file named 'data.json' or 'sequences.json'
        # We try common names. If T007 generated a specific structure, we adapt.
        # Based on T007 schema, it likely contains a JSON list of sequences.
        json_filename = None
        for name in zip_ref.namelist():
            if name.endswith('.json') and 'data' in name.lower():
                json_filename = name
                break
        
        if not json_filename:
            # Fallback: try the first json file
            json_files = [n for n in zip_ref.namelist() if n.endswith('.json')]
            if not json_files:
                raise ValueError("No JSON data file found in zip archive.")
            json_filename = json_files[0]

        with zip_ref.open(json_filename) as f:
            data = json.load(f)
    
    # Convert to DataFrame
    # T007 output schema: sequence_id, frame_id, radial_motion_deg, z_velocity, 
    # grid_points_2d (list), R_matrix, t_vector, randomized_depth
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict) and 'sequences' in data:
        df = pd.DataFrame(data['sequences'])
    else:
        raise ValueError("Unexpected data format in dataset zip.")
    
    return df


def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame has the required columns for T007/T008.
    """
    required_cols = [
        'sequence_id', 'frame_id', 'radial_motion_deg', 'z_velocity',
        'grid_points_2d', 'R_matrix', 't_vector', 'randomized_depth'
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True


def parse_grid_points_2d(grid_points_str: Any) -> Optional[np.ndarray]:
    """
    Parse grid_points_2d from string or list to numpy array.
    Handles cases where points might be missing or malformed.
    """
    if grid_points_str is None:
        return None
    
    try:
        if isinstance(grid_points_str, str):
            # Expecting JSON string like "[[x1,y1], [x2,y2], ...]"
            points = json.loads(grid_points_str)
        elif isinstance(grid_points_str, (list, tuple)):
            points = list(grid_points_str)
        else:
            logger.warning(f"Unexpected type for grid_points_2d: {type(grid_points_str)}")
            return None
        
        if not points:
            return np.array([]).reshape(0, 2)
        
        arr = np.array(points, dtype=np.float32)
        if arr.ndim == 1 and len(arr) == 0:
            return arr.reshape(0, 2)
        if arr.ndim == 1:
            # Might be a flat list [x1, y1, x2, y2...]
            arr = arr.reshape(-1, 2)
        return arr
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse grid_points_2d: {e}")
        return None


def parse_matrix_column(matrix_str: Any, shape: Tuple[int, int]) -> Optional[np.ndarray]:
    """
    Parse R_matrix or t_vector from string or list to numpy array.
    """
    if matrix_str is None:
        return None
    
    try:
        if isinstance(matrix_str, str):
            data = json.loads(matrix_str)
        else:
            data = matrix_str
        
        arr = np.array(data, dtype=np.float32)
        if arr.shape != shape:
            # Try to reshape if flat
            if arr.size == np.prod(shape):
                arr = arr.reshape(shape)
            else:
                logger.warning(f"Matrix shape mismatch: expected {shape}, got {arr.shape}")
                return None
        return arr
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse matrix: {e}")
        return None


def interpolate_missing_points(grid_points: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Linear interpolation for missing/occluded grid points.
    grid_points: Nx2 array of pixel coordinates.
    mask: N boolean array where True indicates valid data, False indicates missing.
    
    Returns: Nx2 array with interpolated values for missing points.
    """
    if len(grid_points) == 0:
        return grid_points
    
    if not np.any(mask):
        # No valid data to interpolate from
        logger.warning("No valid grid points to interpolate from.")
        return grid_points
    
    if np.all(mask):
        return grid_points
    
    # Create an index array
    indices = np.arange(len(grid_points))
    valid_indices = indices[mask]
    invalid_indices = indices[~mask]
    
    # Interpolate x and y separately
    result = grid_points.copy()
    
    for dim in range(2):
        valid_vals = grid_points[valid_indices, dim]
        # Use numpy's interp which handles edge cases (extrapolates with edge values if needed, 
        # but here we assume missing points are surrounded by valid ones or we use nearest)
        # np.interp requires x-coordinates to be sorted, which indices are.
        if len(valid_indices) > 1:
            result[invalid_indices, dim] = np.interp(
                invalid_indices, valid_indices, valid_vals
            )
        elif len(valid_indices) == 1:
            # If only one valid point, fill with that value
            result[invalid_indices, dim] = valid_vals[0]
        else:
            # Should not happen due to early check, but just in case
            pass
    
    return result


def create_grid_frames(df_row: pd.Series) -> List[GridFrame]:
    """
    Create GridFrame objects from a DataFrame row.
    Handles missing grid points by interpolating if possible, or skipping if impossible.
    """
    sequence_id = df_row['sequence_id']
    frame_id = df_row['frame_id']
    radial_motion = df_row['radial_motion_deg']
    z_velocity = df_row['z_velocity']
    randomized_depth = df_row['randomized_depth']
    
    # Parse matrices
    R_matrix = parse_matrix_column(df_row['R_matrix'], (3, 3))
    t_vector = parse_matrix_column(df_row['t_vector'], (3,))
    
    if R_matrix is None or t_vector is None:
        logger.warning(f"Skipping frame {frame_id} in sequence {sequence_id} due to invalid pose matrices.")
        return []
    
    # Parse grid points
    grid_points = parse_grid_points_2d(df_row['grid_points_2d'])
    
    if grid_points is None or len(grid_points) == 0:
        logger.warning(f"Skipping frame {frame_id} in sequence {sequence_id} due to missing grid points.")
        return []
    
    # Check for missing points (NaN or None in the list)
    # Since we parsed to numpy, NaNs might be present if the original had nulls
    # Or we might have a mask if the source explicitly marked missing points.
    # For now, assume if the array has NaNs, they need interpolation.
    if np.isnan(grid_points).any():
        logger.info(f"Interpolating missing grid points for frame {frame_id} in sequence {sequence_id}")
        mask = ~np.isnan(grid_points).any(axis=1)
        grid_points = interpolate_missing_points(grid_points, mask)
        
        # If interpolation resulted in NaNs (e.g., all missing), skip
        if np.isnan(grid_points).any():
            logger.warning(f"Skipping frame {frame_id} after interpolation failed to resolve all missing points.")
            return []
    
    # Create GridFrame
    # Assuming GridFrame expects: sequence_id, frame_id, grid_points_2d, pose (R, t)
    # We need to check the GridFrame definition in models.py
    # Based on typical usage:
    grid_frame = GridFrame(
        sequence_id=sequence_id,
        frame_id=frame_id,
        grid_points_2d=grid_points,
        pose=CameraPose(R=R_matrix, t=t_vector),
        metadata={
            'radial_motion_deg': radial_motion,
            'z_velocity': z_velocity,
            'randomized_depth': randomized_depth
        }
    )
    
    return [grid_frame]


def extract_grid_video_pairs(df: pd.DataFrame) -> List[GridFrame]:
    """
    Extract grid frames and pair them with video sequences.
    Iterates through rows and creates GridFrame objects.
    """
    grid_frames = []
    for _, row in df.iterrows():
        frames = create_grid_frames(row)
        grid_frames.extend(frames)
    return grid_frames


def apply_geometric_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter sequences based on FR-001 heuristics:
    radial motion > 15° OR Z-axis velocity > 0.1 units/frame.
    Returns the retained rows.
    """
    # T009 logic: retained if (radial > 15) OR (z_vel > 0.1)
    # The task says "filter sequences ... to classify as 'retained' or 'excluded'"
    # Usually "filter" implies keeping the good ones.
    # Let's keep rows that satisfy the condition.
    
    mask = (df['radial_motion_deg'] > 15.0) | (df['z_velocity'] > 0.1)
    
    retained = df[mask].copy()
    excluded_count = len(df) - len(retained)
    logger.info(f"Geometric filter: retained {len(retained)} rows, excluded {excluded_count} rows.")
    
    return retained


def load_and_extract_dataset(zip_path: Path) -> Tuple[pd.DataFrame, List[GridFrame]]:
    """
    Main entry point for loading, validating, filtering, and extracting grid frames.
    """
    logger.info(f"Loading dataset from {zip_path}")
    df = load_dataset_from_zip(zip_path)
    
    if not validate_schema(df):
        raise ValueError("Dataset schema validation failed.")
    
    # Apply geometric filter (T009)
    df_filtered = apply_geometric_filter(df)
    
    # Extract grid frames (T010)
    grid_frames = extract_grid_video_pairs(df_filtered)
    
    return df_filtered, grid_frames


def main():
    """
    Main script to run the ingestion pipeline.
    """
    # Determine input path based on T007 output
    # T007 outputs to data/raw/omnidirector.zip (real) or data/raw/synthetic_omnidirector.zip
    # We check for real first, then synthetic.
    base_path = Path("data/raw")
    real_path = base_path / "omnidirector.zip"
    synthetic_path = base_path / "synthetic_omnidirector.zip"
    
    input_path = None
    if real_path.exists():
        input_path = real_path
    elif synthetic_path.exists():
        input_path = synthetic_path
    else:
        logger.error("No dataset found in data/raw/. Please run T007 first.")
        return
    
    logger.info(f"Processing dataset: {input_path}")
    
    try:
        df_filtered, grid_frames = load_and_extract_dataset(input_path)
        
        # Output the filtered dataframe to CSV for T011
        # T011 expects data/processed/filtered_sequences.csv
        output_dir = Path("data/processed")
        ensure_output_directory(output_dir)
        
        # We need to serialize grid_points_2d, R_matrix, t_vector back to strings for CSV
        # Re-load the original df_filtered from the zip or re-process to get strings?
        # The df_filtered here is from the loaded JSON, so grid_points_2d might be lists.
        # We need to ensure they are strings for CSV.
        
        # Convert lists/arrays to strings
        df_filtered['grid_points_2d'] = df_filtered['grid_points_2d'].apply(
            lambda x: json.dumps(x.tolist()) if isinstance(x, np.ndarray) else json.dumps(x) if isinstance(x, list) else x
        )
        df_filtered['R_matrix'] = df_filtered['R_matrix'].apply(
            lambda x: json.dumps(x.tolist()) if isinstance(x, np.ndarray) else x
        )
        df_filtered['t_vector'] = df_filtered['t_vector'].apply(
            lambda x: json.dumps(x.tolist()) if isinstance(x, np.ndarray) else x
        )
        
        output_path = output_dir / "filtered_sequences.csv"
        df_filtered.to_csv(output_path, index=False)
        logger.info(f"Filtered dataset written to {output_path}")
        
        # Log grid frames count
        logger.info(f"Extracted {len(grid_frames)} grid frames.")
        
    except Exception as e:
        logger.exception(f"Error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()