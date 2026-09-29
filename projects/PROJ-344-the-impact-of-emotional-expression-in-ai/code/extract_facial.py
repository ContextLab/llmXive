import os
import glob
import subprocess
import csv
import sys
import tempfile
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import from project API surface
from logging_config import get_logger, log_state_event
from utils import handle_corrupted_file
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

logger = get_logger()

def run_openface_on_video(video_path: str, output_dir: str) -> Optional[str]:
    """
    Runs OpenFace on a single video file and returns the path to the generated CSV.
    
    Args:
        video_path: Path to the input video file.
        output_dir: Directory where OpenFace should write its output.
        
    Returns:
        Path to the generated CSV file if successful, None otherwise.
    """
    logger.info(f"Running OpenFace on: {video_path}")
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct OpenFace command
        # Assuming 'openface' is installed and available in PATH as a CPU binary
        # Typical command structure: openface -f <video> -o <output_dir> -csv
        cmd = [
            "openface",
            "-f", video_path,
            "-o", output_dir,
            "-csv",
            "-cpus", "1"  # Force single CPU usage for stability
        ]
        
        logger.debug(f"Executing: {' '.join(cmd)}")
        
        # Execute OpenFace
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per video
        )
        
        if result.returncode != 0:
            logger.error(f"OpenFace failed for {video_path}: {result.stderr}")
            handle_corrupted_file(video_path, "OpenFace execution failed")
            return None
        
        # Determine output filename
        base_name = Path(video_path).stem
        expected_csv = Path(output_dir) / f"{base_name}.csv"
        
        if expected_csv.exists():
            logger.info(f"OpenFace output created: {expected_csv}")
            return str(expected_csv)
        else:
            logger.warning(f"OpenFace ran but output not found: {expected_csv}")
            return None
              
    except subprocess.TimeoutExpired:
        logger.error(f"OpenFace timed out for {video_path}")
        handle_corrupted_file(video_path, "OpenFace timeout")
        return None
    except FileNotFoundError:
        logger.error("OpenFace binary not found in PATH. Please ensure 'openface' is installed.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error running OpenFace on {video_path}: {str(e)}")
        handle_corrupted_file(video_path, str(e))
        return None

def aggregate_facial_features(raw_features_dir: str, output_path: str) -> None:
    """
    Aggregates all OpenFace CSV files into a single master features CSV.
    
    Args:
        raw_features_dir: Directory containing individual OpenFace output CSVs.
        output_path: Path for the final aggregated features.csv file.
    """
    logger.info(f"Aggregating facial features from {raw_features_dir}")
    
    csv_files = glob.glob(os.path.join(raw_features_dir, "*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {raw_features_dir}")
        # Create empty file with headers if no data found
        pd.DataFrame().to_csv(output_path, index=False)
        return

    all_data = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                logger.warning(f"Empty CSV found: {csv_file}")
                continue
            
            # Extract metadata from filename
            video_id = Path(csv_file).stem
            df['video_id'] = video_id
            
            # Ensure standard columns exist (OpenFace might vary by version)
            # We will standardize to a common schema for downstream processing
            required_cols = ['timestamp', 'video_id']
            # OpenFace standard columns often include:
            # action units (AU01_r, AU02_r, etc.), gaze, pose, etc.
            # We keep all numeric columns found
            
            # Filter to numeric columns + video_id + timestamp if present
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            # Ensure timestamp is first if present, then video_id
            cols_to_keep = ['video_id']
            if 'timestamp' in df.columns:
                cols_to_keep.append('timestamp')
            # Add all numeric feature columns
            for col in numeric_cols:
                if col not in cols_to_keep:
                    cols_to_keep.append(col)
            
            # Select and reorder
            df_subset = df[cols_to_keep]
            all_data.append(df_subset)
            
        except Exception as e:
            logger.error(f"Error reading {csv_file}: {e}")
            continue
    
    if not all_data:
        logger.warning("No valid data to aggregate.")
        # Write empty file with headers
        pd.DataFrame().to_csv(output_path, index=False)
        return

    # Concatenate all dataframes
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Sort by video_id and timestamp
    if 'timestamp' in final_df.columns:
        final_df = final_df.sort_values(by=['video_id', 'timestamp'])
    else:
        final_df = final_df.sort_values(by='video_id')
    
    # Write to output
    final_df.to_csv(output_path, index=False)
    logger.info(f"Aggregated features written to {output_path} ({len(final_df)} rows)")

def main():
    """
    Main entry point for facial feature extraction.
    Scans data/raw for videos, runs OpenFace on each, and aggregates results.
    """
    logger.info("Starting Facial Feature Extraction (T013)")
    
    # Ensure directories exist
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    # Find all video files in data/raw
    video_patterns = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.webm']
    video_files = []
    for pattern in video_patterns:
        video_files.extend(glob.glob(os.path.join(DATA_RAW_DIR, pattern)))
    
    if not video_files:
        logger.warning(f"No video files found in {DATA_RAW_DIR}")
        # Create empty output file
        pd.DataFrame().to_csv(os.path.join(DATA_PROCESSED_DIR, "features.csv"), index=False)
        return

    logger.info(f"Found {len(video_files)} video files to process")
    
    # Create a temporary directory for OpenFace intermediate outputs
    # OpenFace usually outputs a CSV per video
    temp_dir = os.path.join(DATA_PROCESSED_DIR, "openface_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    output_csv_path = os.path.join(DATA_PROCESSED_DIR, "features.csv")
    
    processed_count = 0
    
    for video_path in video_files:
        result_path = run_openface_on_video(video_path, temp_dir)
        if result_path:
            processed_count += 1
    
    if processed_count == 0:
        logger.error("No videos were successfully processed.")
        # Write empty file
        pd.DataFrame().to_csv(output_csv_path, index=False)
        return
    
    # Aggregate results
    aggregate_facial_features(temp_dir, output_csv_path)
    
    log_state_event("facial_extraction_complete", {"processed": processed_count})
    logger.info("Facial feature extraction completed successfully.")

if __name__ == "__main__":
    main()
