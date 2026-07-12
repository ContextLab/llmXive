"""
Preprocessing module for OmniDirector dataset.
Implements grid frame extraction and ground-truth pairing.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd

from data.models import GridFrame, CameraPose
from data.ingestion import load_dataset_from_zip, parse_grid_points_2d, parse_matrix_column

logger = logging.getLogger(__name__)


def extract_grid_frames_from_dataframe(
    df: pd.DataFrame,
    sequence_id_col: str = "sequence_id",
    frame_id_col: str = "frame_id",
    grid_points_col: str = "grid_points_2d",
    r_matrix_col: str = "R_matrix",
    t_vector_col: str = "t_vector",
    radial_motion_col: str = "radial_motion_deg",
    z_velocity_col: str = "z_velocity",
    randomized_depth_col: str = "randomized_depth"
) -> List[GridFrame]:
    """
    Extract GridFrame objects from a pandas DataFrame.
    
    This function iterates through the dataframe rows, parses the grid points
    and camera pose matrices, and constructs GridFrame objects.
    
    Args:
        df: DataFrame containing the sequence data.
        sequence_id_col: Name of the column containing sequence IDs.
        frame_id_col: Name of the column containing frame IDs.
        grid_points_col: Name of the column containing 2D grid points.
        r_matrix_col: Name of the column containing rotation matrices.
        t_vector_col: Name of the column containing translation vectors.
        radial_motion_col: Name of the column containing radial motion data.
        z_velocity_col: Name of the column containing Z-axis velocity.
        randomized_depth_col: Name of the column indicating randomized depth.
        
    Returns:
        List of GridFrame objects with extracted data and ground-truth pairing.
    """
    grid_frames = []
    
    for _, row in df.iterrows():
        try:
            sequence_id = row[sequence_id_col]
            frame_id = row[frame_id_col]
            
            # Parse grid points
            grid_points_2d = parse_grid_points_2d(row[grid_points_col])
            
            # Parse rotation matrix
            r_matrix = parse_matrix_column(row[r_matrix_col])
            
            # Parse translation vector
            t_vector = parse_matrix_column(row[t_vector_col])
            
            # Create CameraPose object
            camera_pose = CameraPose(
                R_matrix=r_matrix,
                t_vector=t_vector
            )
            
            # Create GridFrame object
            grid_frame = GridFrame(
                sequence_id=sequence_id,
                frame_id=frame_id,
                grid_points_2d=grid_points_2d,
                camera_pose=camera_pose,
                radial_motion_deg=row.get(radial_motion_col, 0.0),
                z_velocity=row.get(z_velocity_col, 0.0),
                randomized_depth=bool(row.get(randomized_depth_col, False))
            )
            
            grid_frames.append(grid_frame)
            
        except Exception as e:
            logger.warning(f"Failed to process frame {row.get(frame_id_col, 'unknown')} "
                         f"in sequence {row.get(sequence_id_col, 'unknown')}: {e}")
            continue
    
    logger.info(f"Successfully extracted {len(grid_frames)} grid frames from DataFrame")
    return grid_frames


def pair_ground_truth(
    grid_frames: List[GridFrame],
    metadata: Optional[Dict[str, Any]] = None
) -> List[GridFrame]:
    """
    Pair grid frames with ground-truth parameters.
    
    This function ensures that each GridFrame has the necessary ground-truth
    information for validation and analysis.
    
    Args:
        grid_frames: List of GridFrame objects to be paired.
        metadata: Optional metadata dictionary containing additional ground-truth info.
        
    Returns:
        List of GridFrame objects with ground-truth pairing completed.
    """
    paired_frames = []
    
    for frame in grid_frames:
        # Ensure the frame has all required ground-truth fields
        # The GridFrame dataclass already includes these fields, 
        # but we validate they are properly set
        if frame.grid_points_2d is None or len(frame.grid_points_2d) == 0:
            logger.warning(f"Frame {frame.frame_id} in sequence {frame.sequence_id} "
                         f"has no grid points - skipping ground-truth pairing")
            continue
        
        if frame.camera_pose.R_matrix is None or frame.camera_pose.t_vector is None:
            logger.warning(f"Frame {frame.frame_id} in sequence {frame.sequence_id} "
                         f"has incomplete camera pose - skipping ground-truth pairing")
            continue
        
        # If metadata is provided, we could enrich the frame with additional ground-truth
        if metadata:
            seq_key = f"{frame.sequence_id}_{frame.frame_id}"
            if seq_key in metadata:
                # Merge any additional metadata into the frame
                # (This is a placeholder for future extensions)
                pass
        
        paired_frames.append(frame)
    
    logger.info(f"Successfully paired ground-truth for {len(paired_frames)} grid frames")
    return paired_frames


def save_grid_frames_to_csv(
    grid_frames: List[GridFrame],
    output_path: Union[str, Path]
) -> None:
    """
    Save grid frames to a CSV file.
    
    Args:
        grid_frames: List of GridFrame objects to save.
        output_path: Path to the output CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    records = []
    for frame in grid_frames:
        record = {
            'sequence_id': frame.sequence_id,
            'frame_id': frame.frame_id,
            'radial_motion_deg': frame.radial_motion_deg,
            'z_velocity': frame.z_velocity,
            'grid_points_2d': json.dumps(frame.grid_points_2d.tolist() if isinstance(frame.grid_points_2d, np.ndarray) else frame.grid_points_2d),
            'R_matrix': json.dumps(frame.camera_pose.R_matrix.tolist() if isinstance(frame.camera_pose.R_matrix, np.ndarray) else frame.camera_pose.R_matrix),
            't_vector': json.dumps(frame.camera_pose.t_vector.tolist() if isinstance(frame.camera_pose.t_vector, np.ndarray) else frame.camera_pose.t_vector),
            'randomized_depth': frame.randomized_depth
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(records)} grid frames to {output_path}")


def main(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    zip_path: Optional[Union[str, Path]] = None
) -> List[GridFrame]:
    """
    Main entry point for grid frame extraction and ground-truth pairing.
    
    This function loads the dataset (either from a pre-processed CSV or from a zip file),
    extracts grid frames, pairs them with ground-truth, and saves the results.
    
    Args:
        input_path: Path to the input data (CSV or zip file).
        output_path: Path to save the extracted grid frames.
        zip_path: Optional path to the zip file if input_path is a CSV.
        
    Returns:
        List of extracted and paired GridFrame objects.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    if zip_path:
        zip_path = Path(zip_path)
    
    logger.info(f"Starting grid frame extraction from {input_path}")
    
    # Load dataset
    if input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_path.suffix == '.zip':
        df = load_dataset_from_zip(input_path)
    else:
        raise ValueError(f"Unsupported input file format: {input_path.suffix}")
    
    # Extract grid frames
    grid_frames = extract_grid_frames_from_dataframe(df)
    
    # Pair with ground-truth
    paired_frames = pair_ground_truth(grid_frames)
    
    # Save results
    save_grid_frames_to_csv(paired_frames, output_path)
    
    logger.info(f"Grid frame extraction and ground-truth pairing completed. "
               f"Output saved to {output_path}")
    
    return paired_frames


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract grid frames and pair with ground-truth")
    parser.add_argument("--input", type=str, required=True, help="Input data path (CSV or ZIP)")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    parser.add_argument("--zip", type=str, help="Optional zip file path if input is CSV")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main(args.input, args.output, args.zip)