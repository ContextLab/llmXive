"""
T020: Write combined timecourses to CSV with z-scored signal.

Reads the intermediate combined ROI data from data/processed/combined_roi_temp.npz
(produced by T019), applies z-score normalization per (subject_id, roi), and
writes the final output to data/processed/roi_timecourses.csv.

Schema Compliance:
  - subject_id: str
  - roi: str
  - timepoint: int
  - signal: float32 (z-scored)
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = DATA_PROCESSED / "combined_roi_temp.npz"
OUTPUT_PATH = DATA_PROCESSED / "roi_timecourses.csv"

# Error codes from logging_config
E001 = "E001"  # Data corruption/missing files
E002 = "E002"  # Empty timepoints/data

def log_error(code: str, message: str):
    """Print error to stderr with code prefix."""
    sys.stderr.write(f"{code}: {message}\n")
    sys.stderr.flush()

def main():
    # 1. Verify input file exists
    if not INPUT_PATH.exists():
        log_error(E001, f"Missing input file: {INPUT_PATH}. T019 must complete first.")
        sys.exit(1)

    # 2. Load the combined data
    try:
        data = np.load(INPUT_PATH)
    except Exception as e:
        log_error(E001, f"Failed to load {INPUT_PATH}: {e}")
        sys.exit(1)

    # Expect keys: subject_id, roi, timepoint, signal
    required_keys = ['subject_id', 'roi', 'timepoint', 'signal']
    for key in required_keys:
        if key not in data:
            log_error(E001, f"Missing expected key '{key}' in {INPUT_PATH}")
            sys.exit(1)

    # 3. Convert to DataFrame
    df = pd.DataFrame({
        'subject_id': data['subject_id'],
        'roi': data['roi'],
        'timepoint': data['timepoint'].astype(int),
        'signal': data['signal'].astype(np.float32)
    })

    # 4. Filter out PADDED rows (they have signal=np.nan and specific markers)
    # T019 sets subject_id='PADDED', roi='N/A' for padding.
    # We exclude these from the final CSV as they are not real measurements.
    real_data_mask = (df['subject_id'] != 'PADDED') & (df['roi'] != 'N/A')
    df_real = df[real_data_mask].copy()

    if df_real.empty:
        log_error(E002, "No real timepoint data found after filtering padding rows.")
        sys.exit(1)

    # 5. Z-score normalization per (subject_id, roi)
    # Formula: z = (x - mean) / std
    # If std is 0, set z to 0.0
    def zscore_group(x):
        mean_val = x.mean()
        std_val = x.std()
        if std_val == 0 or np.isnan(std_val):
            return np.zeros_like(x, dtype=np.float32)
        return ((x - mean_val) / std_val).astype(np.float32)

    df_real['signal'] = df_real.groupby(['subject_id', 'roi'])['signal'].transform(zscore_group)

    # 6. Ensure correct dtypes for output
    df_real['subject_id'] = df_real['subject_id'].astype(str)
    df_real['roi'] = df_real['roi'].astype(str)
    df_real['timepoint'] = df_real['timepoint'].astype(int)
    df_real['signal'] = df_real['signal'].astype(np.float32)

    # 7. Sort for consistency (subject, roi, timepoint)
    df_real = df_real.sort_values(by=['subject_id', 'roi', 'timepoint']).reset_index(drop=True)

    # 8. Write to CSV
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_real.to_csv(OUTPUT_PATH, index=False)

    print(f"Successfully wrote {len(df_real)} rows to {OUTPUT_PATH}")
    print(f"Columns: {list(df_real.columns)}")
    print(f"Signal dtype: {df_real['signal'].dtype}")

if __name__ == "__main__":
    main()