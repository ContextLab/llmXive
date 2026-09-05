"""
Combine extracted ROI timecourses from T014, T015, T016 into a single CSV.

Input:
  - data/processed/roi_left_hipp.npy
  - data/processed/roi_right_hipp.npy
  - data/processed/roi_dlpfc.npy

Output:
  - data/processed/roi_timecourses.csv
    Columns: subject_id, roi, timepoint, signal (float32, z-scored)

Schema Compliance: Matches specs/001-neural-narrative-networks-brain-inspired/contracts/neural-data.schema.yaml
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, error, info, warning
from config import get_config

logger = get_logger(__name__)
config = get_config()

def load_roi_timecourse(file_path: Path, roi_name: str) -> np.ndarray:
    """
    Load a .npy file containing timecourses.
    
    Expected shape: (n_subjects, n_timepoints)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file missing: {file_path}")
    
    logger.info(f"Loading {roi_name} data from {file_path}")
    data = np.load(file_path)
    
    if data.size == 0:
        raise ValueError(f"Loaded {roi_name} data is empty: {file_path}")
    
    logger.info(f"Loaded {roi_name} shape: {data.shape}")
    return data

def z_score_normalize(signal: np.ndarray) -> np.ndarray:
    """
    Apply z-score normalization along the timepoint axis (axis=1).
    Returns float32 array.
    """
    # Calculate mean and std per subject (row)
    mean = np.mean(signal, axis=1, keepdims=True)
    std = np.std(signal, axis=1, keepdims=True)
    
    # Avoid division by zero
    std = np.where(std == 0, 1, std)
    
    normalized = (signal - mean) / std
    return normalized.astype(np.float32)

def combine_roi_timecourses():
    """
    Main execution logic for T017b.
    """
    data_dir = Path(project_root) / "data" / "processed"
    output_file = data_dir / "roi_timecourses.csv"
    
    # Define input paths
    inputs = [
        (data_dir / "roi_left_hipp.npy", "left_hipp"),
        (data_dir / "roi_right_hipp.npy", "right_hipp"),
        (data_dir / "roi_dlpfc.npy", "dlpfc"),
    ]
    
    all_rows = []
    
    for input_path, roi_name in inputs:
        try:
            # Load raw data
            raw_data = load_roi_timecourse(input_path, roi_name)
            
            # Validate shape: (n_subjects, n_timepoints)
            if raw_data.ndim != 2:
                raise ValueError(f"Expected 2D array (subjects, timepoints), got {raw_data.ndim}D")
            
            n_subjects, n_timepoints = raw_data.shape
            
            # Generate subject IDs based on count (e.g., sub-01, sub-02...)
            # Assuming T014-T016 processed the first 10 subjects found
            subject_ids = [f"sub-{i+1:02d}" for i in range(n_subjects)]
            
            # Normalize (z-score)
            normalized_data = z_score_normalize(raw_data)
            
            # Flatten to long format for CSV
            for s_idx, sub_id in enumerate(subject_ids):
                for t_idx in range(n_timepoints):
                    all_rows.append({
                        "subject_id": sub_id,
                        "roi": roi_name,
                        "timepoint": int(t_idx),
                        "signal": float(normalized_data[s_idx, t_idx])
                    })
            
            logger.info(f"Processed {roi_name}: {len(all_rows)} rows added")
            
        except FileNotFoundError as e:
            logger.error(f"E001: {e}")
            raise
        except ValueError as e:
            logger.error(f"E002: {e}")
            raise
    
    if not all_rows:
        raise RuntimeError("No data rows were generated. Check input files.")
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    # Ensure column order matches schema
    df = df[["subject_id", "roi", "timepoint", "signal"]]
    
    # Ensure data types
    df["subject_id"] = df["subject_id"].astype(str)
    df["roi"] = df["roi"].astype(str)
    df["timepoint"] = df["timepoint"].astype(int)
    df["signal"] = df["signal"].astype(np.float32)
    
    # Save to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    logger.info(f"Successfully wrote combined timecourses to {output_file}")
    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Signal dtype: {df['signal'].dtype}")
    
    return output_file

def main():
    try:
        combine_roi_timecourses()
        info("T017b completed successfully.")
    except Exception as e:
        error(f"T017b failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
