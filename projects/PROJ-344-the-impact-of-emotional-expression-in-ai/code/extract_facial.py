"""
Facial Feature Extraction Module using OpenFace (CPU).

This module extracts facial landmarks, action units, and gaze estimates
from video frames using the OpenFace CPU binary. It adheres to the
project's data processing constraints (CPU-only, no GPU).

Inputs:
    Video files from data/raw/ (expected structure: <interaction_id>.mp4 or .avi)
Outputs:
    data/processed/facial_features.csv
"""
import os
import glob
import subprocess
import csv
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import project utilities
from logging_config import get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_error
from utils import handle_corrupted_file
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

logger = get_logger(__name__)

# Configuration
OPENFACE_BINARY = "OpenFace"  # Assumes OpenFace is in PATH or installed globally
# If OpenFace is not in PATH, set the absolute path here:
# OPENFACE_BINARY = "/usr/local/bin/OpenFace"

# Expected output columns from OpenFace (simplified subset for consistency metric)
# OpenFace typically outputs: timestamp, face_id, confidence, landmarks, action_units, gaze
# We will focus on Action Units (AU) and confidence for consistency scoring.
FOCUSED_AU_COLUMNS = [
    'AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r',
    'AU09_r', 'AU10_r', 'AU12_r', 'AU15_r', 'AU17_r', 'AU23_r', 'AU25_r'
]

def run_openface_on_video(video_path: str, output_dir: str) -> Optional[str]:
    """
    Runs the OpenFace binary on a single video file.

    Args:
        video_path: Absolute path to the video file.
        output_dir: Directory where OpenFace will write CSV outputs.

    Returns:
        Path to the generated CSV file if successful, None otherwise.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    try:
        # Construct command
        # -f: input file, -ow: output directory, -of: output filename prefix
        # -no_display: run headless
        # -cpu: ensure CPU mode (though default for binary is usually CPU)
        cmd = [
            OPENFACE_BINARY,
            '-f', video_path,
            '-ow', output_dir,
            '-no_display',
            '-cpu'
        ]

        logger.info(f"Running OpenFace on {video_path}...")
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5 minute timeout per video
        )

        if process.returncode != 0:
            logger.error(f"OpenFace failed for {video_path}: {process.stderr.decode()}")
            return None

        # Find the generated CSV (OpenFace names it <filename>.csv)
        video_name = Path(video_path).stem
        expected_csv = os.path.join(output_dir, f"{video_name}.csv")

        if os.path.exists(expected_csv):
            logger.info(f"OpenFace completed. Output: {expected_csv}")
            return expected_csv
        else:
            # Check if it was named differently or if no face was detected
            matches = glob.glob(os.path.join(output_dir, f"{video_name}*.csv"))
            if matches:
                logger.warning(f"Expected {expected_csv} but found {matches[0]}. Using found file.")
                return matches[0]
            else:
                logger.warning(f"No CSV output generated for {video_path}. Likely no face detected.")
                return None

    except subprocess.TimeoutExpired:
        logger.error(f"OpenFace timed out for {video_path}")
        return None
    except Exception as e:
        logger.error(f"Error running OpenFace on {video_path}: {str(e)}")
        return None

def aggregate_facial_features(raw_data_dir: str, processed_output_dir: str) -> pd.DataFrame:
    """
    Iterates through raw video data, runs OpenFace, and aggregates results.

    Args:
        raw_data_dir: Path to directory containing raw video files.
        processed_output_dir: Path to save the aggregated CSV.

    Returns:
        DataFrame containing aggregated facial features.
    """
    os.makedirs(processed_output_dir, exist_ok=True)
    
    # Create a temporary directory for OpenFace intermediate outputs
    temp_dir = tempfile.mkdtemp(prefix="openface_tmp_")
    logger.info(f"Using temporary directory for OpenFace outputs: {temp_dir}")

    all_features = []
    video_files = glob.glob(os.path.join(raw_data_dir, "*.mp4")) + \
                  glob.glob(os.path.join(raw_data_dir, "*.avi")) + \
                  glob.glob(os.path.join(raw_data_dir, "*.mov"))

    if not video_files:
        logger.warning(f"No video files found in {raw_data_dir}")
        return pd.DataFrame()

    logger.info(f"Found {len(video_files)} video files to process.")

    for video_path in video_files:
        interaction_id = Path(video_path).stem
        logger.info(f"Processing interaction: {interaction_id}")

        csv_output = run_openface_on_video(video_path, temp_dir)

        if csv_output and os.path.exists(csv_output):
            try:
                df = pd.read_csv(csv_output)
                
                # Filter to relevant columns if they exist
                existing_cols = [c for c in FOCUSED_AU_COLUMNS if c in df.columns]
                if not existing_cols:
                    # Fallback: keep all columns if specific AUs missing, but log warning
                    logger.warning(f"No standard AU columns found in {csv_output}. Keeping all.")
                    existing_cols = df.columns.tolist()

                # Add metadata
                df['interaction_id'] = interaction_id
                df['source_file'] = os.path.basename(video_path)
                
                # Select columns: interaction_id, timestamp, and AUs
                cols_to_keep = ['interaction_id', 'timestamp'] + existing_cols
                df_subset = df[cols_to_keep]
                
                all_features.append(df_subset)
                
                # Clean up specific CSV to save space
                os.remove(csv_output)
                
            except Exception as e:
                logger.error(f"Failed to parse OpenFace output for {interaction_id}: {e}")
                handle_corrupted_file(csv_output, "OpenFace CSV parse error")
        else:
            logger.warning(f"Skipping {interaction_id} due to OpenFace failure or no face detected.")

    # Clean up temp directory
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"Could not remove temp dir {temp_dir}: {e}")

    if all_features:
        final_df = pd.concat(all_features, ignore_index=True)
        output_path = os.path.join(processed_output_dir, "facial_features.csv")
        final_df.to_csv(output_path, index=False)
        logger.info(f"Saved aggregated facial features to {output_path}")
        return final_df
    else:
        logger.warning("No facial features extracted from any video.")
        # Create empty file with schema to prevent downstream crashes
        empty_df = pd.DataFrame(columns=['interaction_id', 'timestamp'] + FOCUSED_AU_COLUMNS)
        output_path = os.path.join(processed_output_dir, "facial_features.csv")
        empty_df.to_csv(output_path, index=False)
        return empty_df

def main():
    """Main entry point for facial feature extraction."""
    log_pipeline_start("T013", "Facial Feature Extraction")
    
    try:
        # Ensure directories exist (T001 should have done this, but safe to check)
        os.makedirs(DATA_RAW_DIR, exist_ok=True)
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
        
        df = aggregate_facial_features(DATA_RAW_DIR, DATA_PROCESSED_DIR)
        
        if df.empty:
            logger.warning("Extraction completed but no data was generated.")
        else:
            logger.info(f"Extraction complete. Total rows: {len(df)}")
            
        log_pipeline_complete("T013", "Facial Feature Extraction")
        
    except Exception as e:
        log_pipeline_error("T013", str(e))
        raise

if __name__ == "__main__":
    main()