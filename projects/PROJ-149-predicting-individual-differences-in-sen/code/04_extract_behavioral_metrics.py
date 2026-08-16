"""
T013: Implement behavioral parsing for US1.
Extracts median RT, excludes outliers (<100ms, >2000ms), and excludes participants
if <70% trials remain.
Outputs:
  - data/interim/behavioral_metrics.csv
  - data/interim/behavioral_exclusion_log.csv
"""
import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Import config utilities
from config import get_path, ensure_dirs

# Import PhysioNet metadata helpers from the feasibility check module
# We need to map participant IDs to the correct files.
# The feasibility check T008a likely created a joined_metadata.csv or similar.
# However, for T013, we need to load the raw behavioral data associated with the
# PhysioNet Motor Movement/Imagery dataset.
# The dataset structure on PhysioNet for this study (EEG Motor Movement/Imagery)
# contains reaction time data in the annotations of the .edf files for specific tasks.
# Specifically, "Simple Reaction Time" tasks are what we need.
# Since T008a verified the presence of "Simple Reaction Time", we look for those files.

def load_physionet_behavioral_data(raw_data_dir: str) -> pd.DataFrame:
    """
    Load behavioral data (Reaction Times) from PhysioNet EEG Motor Movement/Imagery dataset.
    This function scans the raw data directory for .edf files, reads their annotations,
    and extracts reaction times for the "Simple Reaction Time" task.
    """
    import mne
    import re

    rt_records = []

    # Find all .edf files
    edf_files = glob.glob(os.path.join(raw_data_dir, "**", "*.edf"), recursive=True)
    if not edf_files:
        raise FileNotFoundError(f"No .edf files found in {raw_data_dir}")

    for edf_path in edf_files:
        try:
            raw = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
            annotations = raw.annotations
            
            # Check if this file contains the "Simple Reaction Time" task
            # The task name is usually in the description of the annotation or the filename
            # PhysioNet EEG Motor Movement/Imagery dataset:
            # Subjects are 001 to 109.
            # Tasks include: "open/closed eyes", "left/right fist clench", "feet movement", "simple reaction time".
            # We are interested in "simple reaction time".
            
            # Extract subject ID from filename (e.g., 001.edf -> 001)
            filename = os.path.basename(edf_path)
            # Pattern: <subject_id>.edf or <subject_id>_task.edf
            match = re.match(r"(\d+)", filename)
            if match:
                subject_id = match.group(1)
            else:
                continue

            # Look for reaction time annotations
            # In this dataset, reaction times are often stored as annotations with description "rt" or similar,
            # or we might need to infer from the task name.
            # Let's check annotations descriptions.
            # According to the dataset documentation, simple reaction time trials are marked.
            # We will look for annotations that indicate a trial start and the response.
            # However, a simpler heuristic for this specific dataset (if annotations are sparse):
            # The dataset has specific files for specific tasks.
            # Let's assume the filename or directory structure indicates the task if available.
            # If not, we scan annotations for "simple" or "reaction".
            
            has_simple_rt = False
            if "simple" in filename.lower() or "reaction" in filename.lower():
                has_simple_rt = True
            
            # If not obvious from filename, check annotations
            if not has_simple_rt:
                for desc in annotations.description:
                    if "simple" in desc.lower() or "reaction" in desc.lower():
                        has_simple_rt = True
                        break
            
            if not has_simple_rt:
                continue

            # Extract RTs from annotations if possible
            # In some versions of this dataset, the RT is stored in the duration of an annotation
            # or as a specific value in the description.
            # A common pattern in PhysioNet EEG Motor Movement/Imagery is that the 'rt' is not explicitly
            # in the EDF annotations for all tasks, but for the Simple Reaction Time task,
            # the trial structure is: Stimulus (Go) -> Response.
            # If the dataset is the "EEG Motor Movement/Imagery Dataset" (Goldberger et al.),
            # the RT data might be in a separate file or embedded.
            # Given the constraints, we will assume the annotations contain the RT data
            # or we derive it from the time between events if marked.
            
            # For the purpose of this implementation, we will assume that if the file is identified
            # as a "Simple Reaction Time" file, we can extract RTs from the annotations.
            # If the annotations are empty or do not contain RTs, we skip.
            
            # Heuristic: If the file is a Simple RT file, look for annotations with 'rt' or similar.
            # If none found, we might need to look for a specific pattern.
            # Let's try to find annotations that have a non-zero duration or specific description.
            
            # Actually, for the PhysioNet EEG Motor Movement/Imagery dataset, the RTs are often
            # not in the EDF files directly for all subjects, but for the "Simple Reaction Time" task,
            # they are sometimes provided in the .mat files or derived.
            # However, T008a verified the presence of "Simple Reaction Time".
            # We will assume the data is present in the annotations as 'rt' or similar.
            
            # Let's try to extract RTs from annotations where the description contains 'rt' or 'response'.
            # If that fails, we might need to look at the event codes.
            
            # For this implementation, we will simulate the extraction if the file is valid.
            # In a real scenario, we would parse the specific annotation structure.
            # Since we cannot guarantee the exact annotation format without the raw data,
            # we will use a robust method: check for 'rt' in annotations.
            
            rt_values = []
            for i, desc in enumerate(annotations.description):
                if "rt" in desc.lower() or "response" in desc.lower():
                    # Try to parse the duration as RT (in seconds) -> convert to ms
                    rt_val = annotations.duration[i] * 1000
                    if rt_val > 0:
                        rt_values.append(rt_val)
                
            # If no RTs found in annotations, we might need to check if there's a specific pattern.
            # If the file is a Simple RT file but no RTs are in annotations, we skip.
            if not rt_values:
                # Fallback: Check if the file has a specific naming convention that implies RTs are present.
                # If not, we cannot extract.
                continue
            
            rt_records.extend([
                {"participant_id": subject_id, "rt_ms": rt} for rt in rt_values
            ])

        except Exception as e:
            # Log error but continue with other files
            print(f"Error processing {edf_path}: {e}", file=sys.stderr)
            continue

    if not rt_records:
        raise ValueError("No reaction time data found in the dataset.")

    return pd.DataFrame(rt_records)

def extract_rt_from_eeg_annotations(raw_data_dir: str) -> pd.DataFrame:
    """
    Wrapper to load and extract RTs.
    """
    return load_physionet_behavioral_data(raw_data_dir)

def process_behavioral_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process behavioral data:
    1. Exclude outliers (<100ms, >2000ms).
    2. Exclude participants if <70% of trials remain.
    3. Compute median RT per participant.
    
    Returns:
      - metrics_df: DataFrame with participant_id, median_rt, n_trials, n_trials_excluded
      - exclusion_log_df: DataFrame with participant_id, reason
    """
    metrics_records = []
    exclusion_records = []

    # Group by participant
    grouped = df.groupby("participant_id")

    for pid, group in grouped:
        original_count = len(group)
        rt_values = group["rt_ms"].values

        # Filter outliers
        valid_mask = (rt_values >= 100) & (rt_values <= 2000)
        valid_rt_values = rt_values[valid_mask]
        excluded_count = original_count - len(valid_rt_values)

        # Check retention rate
        retention_rate = len(valid_rt_values) / original_count

        if retention_rate < 0.70:
            exclusion_records.append({
                "participant_id": pid,
                "reason": f"Retention rate < 70% ({retention_rate:.2%})"
            })
        else:
            median_rt = np.median(valid_rt_values)
            metrics_records.append({
                "participant_id": pid,
                "median_rt": median_rt,
                "n_trials": len(valid_rt_values),
                "n_trials_excluded": excluded_count
            })

    metrics_df = pd.DataFrame(metrics_records)
    exclusion_log_df = pd.DataFrame(exclusion_records)

    return metrics_df, exclusion_log_df

def main():
    parser = argparse.ArgumentParser(description="Extract behavioral metrics from PhysioNet data.")
    parser.add_argument("--raw-data-dir", type=str, default=None, help="Path to raw data directory. If not provided, uses config.")
    parser.add_argument("--output-dir", type=str, default=None, help="Path to output directory. If not provided, uses config.")
    args = parser.parse_args()

    # Get paths from config if not provided
    if args.raw_data_dir is None:
        raw_data_dir = get_path("data_raw") # Assuming 'data_raw' is a key in config
    else:
        raw_data_dir = args.raw_data_dir

    if args.output_dir is None:
        output_dir = get_path("interim_data") # Assuming 'interim_data' is a key in config
    else:
        output_dir = args.output_dir

    # Ensure output directory exists
    ensure_dirs(output_dir)

    print(f"Loading behavioral data from {raw_data_dir}...")
    try:
        rt_df = extract_rt_from_eeg_annotations(raw_data_dir)
    except Exception as e:
        print(f"Error loading behavioral data: {e}", file=sys.stderr)
        # Create empty files to satisfy the output requirement even on failure?
        # No, the task says "fail loudly" if real data is missing.
        # But we need to produce the files if the data is there but processing fails.
        # If the dataset is missing, we should fail.
        raise RuntimeError("Failed to load real behavioral data.") from e

    print(f"Loaded {len(rt_df)} reaction time records.")
    print("Processing behavioral data...")

    metrics_df, exclusion_log_df = process_behavioral_data(rt_df)

    # Define output paths
    metrics_path = os.path.join(output_dir, "behavioral_metrics.csv")
    exclusion_log_path = os.path.join(output_dir, "behavioral_exclusion_log.csv")

    # Save outputs
    metrics_df.to_csv(metrics_path, index=False)
    exclusion_log_df.to_csv(exclusion_log_path, index=False)

    print(f"Saved behavioral metrics to {metrics_path}")
    print(f"Saved exclusion log to {exclusion_log_path}")
    print(f"Total participants processed: {len(metrics_df)}")
    print(f"Total participants excluded: {len(exclusion_log_df)}")

if __name__ == "__main__":
    main()
