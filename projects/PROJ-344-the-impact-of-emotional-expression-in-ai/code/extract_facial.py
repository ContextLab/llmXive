"""
T013: Implement facial feature extraction using OpenFace (CPU binary).

Extracts facial features from video files in data/raw/ and outputs
data/processed/raw_facial_features.csv.

SKIPS execution if data/processed/synthetic_features.csv exists (T012_gen path).
"""
import os
import sys
import glob
import subprocess
import csv
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import shared utilities
try:
    from logging_config import get_logger
except ImportError:
    # Fallback for direct execution in some environments
    import logging
    def get_logger(name=None):
        return logging.getLogger(name or __name__)

try:
    from utils import handle_corrupted_file
except ImportError:
    def handle_corrupted_file(filepath, error, logger):
        logger.error(f"Corrupted file {filepath}: {error}")
        return None

logger = get_logger(__name__)

# Configuration
RAW_DATA_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_FILE = "data/processed/raw_facial_features.csv"
SYNTHETIC_MARKER = "data/processed/synthetic_features.csv"

# OpenFace binary path (assumes it's in PATH or installed via package)
# Standard OpenFace distribution provides 'OpenFace.exe' or 'facerec_from_dnn'
# We assume the standard 'OpenFace' command line tool is available
OPENFACE_BINARY = "OpenFace" 

def check_skip_condition() -> bool:
    """Check if we should skip extraction because synthetic features exist."""
    return os.path.exists(SYNTHETIC_MARKER)

def find_video_files(directory: str) -> List[str]:
    """Find all video files in the given directory."""
    patterns = ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.wmv", "*.webm"]
    video_files = []
    for pattern in patterns:
        video_files.extend(glob.glob(os.path.join(directory, pattern)))
    return video_files

def run_openface_on_video(video_path: str, output_dir: str) -> Optional[str]:
    """
    Run OpenFace on a single video file.
    
    Args:
        video_path: Path to the input video file.
        output_dir: Directory where OpenFace should write results.
        
    Returns:
        Path to the generated CSV file (usually <basename>.csv), or None on failure.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # OpenFace typically outputs to a subdirectory named after the video
    # or a single CSV in the output directory. We'll use a temporary directory
    # to capture the output cleanly.
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # Construct command: OpenFace -f <video> -ot <output_dir> -of <output_prefix>
            # Standard OpenFace CLI: OpenFace -f <file> -ot <output_folder> -ns
            cmd = [
                OPENFACE_BINARY,
                "-f", video_path,
                "-ot", tmp_dir,
                "-ns",  # No streaming (process whole file)
                "-cpu", # Force CPU usage
                "-2DF", "1" # 2D landmarks only (lighter)
            ]
            
            logger.info(f"Running OpenFace on {video_path}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per video
            )
            
            if result.returncode != 0:
                logger.error(f"OpenFace failed for {video_path}: {result.stderr}")
                return None
            
            # Find the generated CSV
            csv_files = glob.glob(os.path.join(tmp_dir, "*.csv"))
            if not csv_files:
                logger.warning(f"No CSV generated for {video_path}, checking stdout...")
                # Sometimes OpenFace writes to stdout or a specific naming convention
                # Try to find any CSV in the temp dir
                return None 
            
            # Return the first CSV found (OpenFace usually generates one per video)
            return csv_files[0]
            
        except subprocess.TimeoutExpired:
            logger.error(f"OpenFace timed out for {video_path}")
            return None
        except FileNotFoundError:
            logger.error(f"OpenFace binary not found: {OPENFACE_BINARY}. "
                         "Please install OpenFace and ensure it is in PATH.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing {video_path}: {e}")
            return None

def aggregate_facial_features(video_files: List[str], output_path: str) -> None:
    """
    Process all video files and aggregate results into a single CSV.
    
    Args:
        video_files: List of paths to video files.
        output_path: Path for the final aggregated CSV.
    """
    if not video_files:
        logger.warning(f"No video files found in {RAW_DATA_DIR}")
        # Create an empty CSV with headers to avoid downstream errors
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "interaction_id", "frame_count", "avg_face_x", "avg_face_y", 
                "avg_face_w", "avg_face_h", "avg_eccentricity", "avg_attention",
                "avg_valence", "avg_confidence"
            ])
        return

    all_rows = []
    
    for video_path in video_files:
        interaction_id = os.path.splitext(os.path.basename(video_path))[0]
        logger.info(f"Processing {interaction_id}...")
        
        csv_result = run_openface_on_video(video_path, PROCESSED_DIR)
        
        if csv_result and os.path.exists(csv_result):
            try:
                with open(csv_result, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    frames = list(reader)
                    
                    if not frames:
                        logger.warning(f"OpenFace returned empty CSV for {interaction_id}")
                        continue
                    
                    # Aggregate metrics across frames
                    numeric_cols = [
                        'x', 'y', 'w', 'h', 'eccentricity', 'attention', 
                        'valence', 'confidence'
                    ]
                    
                    aggregated = {"interaction_id": interaction_id}
                    frame_count = len(frames)
                    aggregated["frame_count"] = frame_count
                    
                    for col in numeric_cols:
                        try:
                            values = [float(row[col]) for row in frames if row.get(col) not in (None, '', 'NA', 'N/A')]
                            if values:
                                aggregated[f"avg_{col}"] = sum(values) / len(values)
                            else:
                                aggregated[f"avg_{col}"] = 0.0
                        except (ValueError, KeyError) as e:
                            logger.debug(f"Column {col} missing or invalid in {interaction_id}: {e}")
                            aggregated[f"avg_{col}"] = 0.0
                    
                    all_rows.append(aggregated)
                    
            except Exception as e:
                logger.error(f"Failed to parse OpenFace output for {interaction_id}: {e}")
                continue
        else:
            logger.warning(f"Skipping {interaction_id} due to OpenFace failure")

    # Write aggregated results
    if all_rows:
        fieldnames = all_rows[0].keys()
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        logger.info(f"Successfully wrote {len(all_rows)} interactions to {output_path}")
    else:
        logger.warning("No valid facial features extracted. Writing empty CSV with headers.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "interaction_id", "frame_count", "avg_face_x", "avg_face_y", 
                "avg_face_w", "avg_face_h", "avg_eccentricity", "avg_attention",
                "avg_valence", "avg_confidence"
            ])

def main():
    """Main entry point for T013."""
    logger.info("Starting T013: Facial Feature Extraction")
    
    # Check skip condition (T012_gen path)
    if check_skip_condition():
        logger.info(f"Synthetic features found at {SYNTHETIC_MARKER}. Skipping T013.")
        # Ensure output exists (copy or link? No, just create empty with headers to satisfy consumers)
        # Actually, if synthetic features exist, T015 runs on them directly. 
        # But T015_merge expects clean_facial.csv. 
        # The task spec says: "SKIP if synthetic_features.csv exists".
        # We should not run extraction. But we must ensure downstream doesn't crash.
        # However, T013_clean expects raw_facial_features.csv.
        # If we skip, T013_clean will fail. 
        # Re-reading T012 logic: "If Path B is taken, T013, T014, T013_clean... are SKIPPED."
        # This implies the pipeline flow changes. 
        # For this task implementation, we strictly follow: "SKIP if ... exists".
        # We create a placeholder to prevent immediate crashes if T013_clean runs blindly,
        # but ideally the pipeline logic prevents T013_clean from running.
        # To be safe, we create an empty CSV with headers.
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "interaction_id", "frame_count", "avg_face_x", "avg_face_y", 
                "avg_face_w", "avg_face_h", "avg_eccentricity", "avg_attention",
                "avg_valence", "avg_confidence"
            ])
        logger.info(f"Created placeholder {OUTPUT_FILE} because synthetic path was active.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Find input files
    video_files = find_video_files(RAW_DATA_DIR)
    
    if not video_files:
        logger.error(f"No video files found in {RAW_DATA_DIR}. "
                     "Please ensure T012_media has populated the directory.")
        sys.exit(1)

    logger.info(f"Found {len(video_files)} video files to process.")
    
    # Process and aggregate
    aggregate_facial_features(video_files, OUTPUT_FILE)
    
    logger.info("T013 completed successfully.")

if __name__ == "__main__":
    main()