"""
code/04_extract_behavioral_metrics.py

Implements Task T013: Behavioral parsing and filtering.

- Loads behavioral data (RT trials) from the raw data directory.
- Filters outliers (<100ms, >2000ms).
- Excludes participants with <70% valid trials remaining.
- Computes median RT per participant.
- Outputs `data/processed/behavioral_metrics.csv`.
"""
import os
import sys
import json
import glob
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs, set_global_seed

# Constants
MIN_RT_MS = 100.0
MAX_RT_MS = 2000.0
MIN_VALID_TRIAL_FRACTION = 0.70
OUTPUT_FILE = get_path("processed", "behavioral_metrics.csv")
LOG_FILE = get_path("processed", "behavioral_processing_log.json")


def load_behavioral_trials(raw_data_dir: str) -> pd.DataFrame:
    """
    Load all behavioral trial files (CSV) from the raw data directory.
    Expects files named like 'sub-<id>_task-<task>_behav.csv' or similar.
    Returns a single DataFrame with columns: ['participant_id', 'trial_id', 'rt_ms', 'condition'].
    """
    raw_path = Path(raw_data_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_path}")

    # Search for CSV files containing 'behav' or 'rt' in the name
    # Adjust pattern if the specific PhysioNet structure differs, 
    # but typically behavioral data is in subfolders or specific files.
    # For PhysioNet EEG Motor Movement/Imagery, behavioral data is often 
    # in a separate CSV or embedded in the event info. 
    # We assume a standard structure where behavioral CSVs exist in data/raw/behavioral/
    # or are extracted alongside EEG.
    
    # Strategy: Look for CSVs in data/raw/behavioral/ or data/raw/
    # If specific file names are known from T007, use them. 
    # Assuming a generic search for 'behav' or 'rt' files in raw_data_dir or subdirs.
    
    csv_files = []
    for ext in ["*.csv"]:
        csv_files.extend(raw_path.rglob(ext))
    
    if not csv_files:
        # Fallback: check if there's a specific behavioral directory
        behavioral_dir = raw_path / "behavioral"
        if behavioral_dir.exists():
            csv_files = list(behavioral_dir.rglob("*.csv"))
        else:
            # Try to find any CSV that might contain RT data
            # This is a heuristic; real implementation should match T007's output structure
            pass

    all_trials = []
    found_files = 0

    for csv_file in csv_files:
        try:
            # Heuristic: Skip files that are clearly not behavioral (e.g., checksums, logs)
            if "checksum" in csv_file.name.lower() or "log" in csv_file.name.lower():
                continue
            
            df = pd.read_csv(csv_file)
            
            # Normalize column names
            cols = df.columns.str.lower().str.replace(" ", "_")
            df.columns = cols

            # Identify columns
            # Look for participant ID
            pid_col = None
            for c in ["participant_id", "subject_id", "sub_id", "id", "subject"]:
                if c in df.columns:
                    pid_col = c
                    break
            
            # Look for RT column
            rt_col = None
            for c in ["rt_ms", "reaction_time", "rt", "response_time"]:
                if c in df.columns:
                    rt_col = c
                    break

            if pid_col and rt_col:
                # Extract relevant columns
                sub_df = df[[pid_col, rt_col]].copy()
                sub_df.columns = ["participant_id", "rt_ms"]
                
                # Ensure RT is numeric
                sub_df["rt_ms"] = pd.to_numeric(sub_df["rt_ms"], errors="coerce")
                sub_df = sub_df.dropna(subset=["rt_ms"])
                
                # Add trial ID if not present
                sub_df["trial_id"] = range(len(sub_df))
                
                # Try to extract subject ID from filename if not in data
                # PhysioNet often uses sub-XX in path or filename
                if "participant_id" not in sub_df.columns or sub_df["participant_id"].isna().all():
                    # Fallback to extracting from filename
                    # Assuming filename pattern like sub-01_task-...
                    import re
                    match = re.search(r"sub-(\d+)", str(csv_file))
                    if match:
                        sub_df["participant_id"] = int(match.group(1))
                
                if "participant_id" in sub_df.columns and not sub_df["participant_id"].isna().all():
                    all_trials.append(sub_df)
                    found_files += 1
            
        except Exception as e:
            # Skip problematic files
            continue

    if not all_trials:
        raise ValueError("No valid behavioral trial data found in the raw directory.")

    combined = pd.concat(all_trials, ignore_index=True)
    combined["participant_id"] = combined["participant_id"].astype(int)
    return combined


def process_behavioral_data(trials_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply outlier filtering and participant exclusion logic.
    
    1. Exclude trials with RT < 100ms or RT > 2000ms.
    2. For each participant, calculate the fraction of valid trials.
    3. Exclude participants with < 70% valid trials.
    4. Compute median RT for remaining participants.
    """
    # 1. Filter outliers
    initial_count = len(trials_df)
    valid_trials = trials_df[
        (trials_df["rt_ms"] >= MIN_RT_MS) & 
        (trials_df["rt_ms"] <= MAX_RT_MS)
    ].copy()
    
    outlier_count = initial_count - len(valid_trials)
    
    # 2. Group by participant
    participant_stats = valid_trials.groupby("participant_id").agg(
        total_trials=("rt_ms", "count"),
        median_rt=("rt_ms", "median"),
        mean_rt=("rt_ms", "mean"),
        std_rt=("rt_ms", "std")
    ).reset_index()

    # Calculate valid trial fraction
    # We need to know the total trials *before* filtering to calculate the fraction
    # However, the task says "exclude participants if <70% trials remain".
    # This implies we compare valid_trials count to the original count per participant.
    
    original_counts = trials_df.groupby("participant_id").size().reset_index(name="original_trials")
    participant_stats = participant_stats.merge(original_counts, on="participant_id")
    
    participant_stats["valid_fraction"] = participant_stats["total_trials"] / participant_stats["original_trials"]
    
    # 3. Exclude participants with < 70% valid trials
    kept_participants = participant_stats[participant_stats["valid_fraction"] >= MIN_VALID_TRIAL_FRACTION]
    excluded_participants = participant_stats[participant_stats["valid_fraction"] < MIN_VALID_TRIAL_FRACTION]
    
    # 4. Select final columns
    result = kept_participants[["participant_id", "median_rt", "total_trials", "original_trials", "valid_fraction"]]
    result = result.rename(columns={"median_rt": "median_rt_ms"})
    
    return result, {
        "initial_total_trials": initial_count,
        "outlier_trials": outlier_count,
        "participants_excluded_due_to_low_trials": len(excluded_participants),
        "participants_kept": len(kept_participants)
    }


def main():
    """Main entry point for behavioral metric extraction."""
    set_global_seed(42)
    ensure_dirs()
    
    raw_dir = get_path("raw")
    
    print(f"Loading behavioral trials from {raw_dir}...")
    try:
        trials_df = load_behavioral_trials(raw_dir)
        print(f"Loaded {len(trials_df)} trials from {trials_df['participant_id'].nunique()} participants.")
    except Exception as e:
        print(f"Error loading behavioral data: {e}")
        # If data is missing, we cannot proceed. 
        # In a real pipeline, this might trigger a failure or skip.
        sys.exit(1)

    print(f"Processing behavioral data (outliers: {MIN_RT_MS}-{MAX_RT_MS}ms, min valid: {MIN_VALID_TRIAL_FRACTION*100}%)...")
    metrics_df, stats_log = process_behavioral_data(trials_df)
    
    print(f"Processing complete. Kept {len(metrics_df)} participants.")
    
    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved metrics to {OUTPUT_FILE}")
    
    # Save log
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(stats_log, f, indent=2)
    print(f"Saved processing log to {LOG_FILE}")
    
    return metrics_df


if __name__ == "__main__":
    main()