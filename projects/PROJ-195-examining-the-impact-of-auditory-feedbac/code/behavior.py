"""
Behavioral metric extraction module for US3.
Extracts trial-wise Reaction Times (RTs) from BIDS events.tsv files
and generates aggregated behavioral metrics.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np

# --- Logging Setup ---
def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configures a logger that writes to both console and a file.
    """
    logger = logging.getLogger("behavior")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# --- Helper Functions ---

def load_valid_subjects(valid_subjects_file: Path) -> List[str]:
    """
    Loads the list of valid subject IDs from the exclusion file generated in T017.
    """
    if not valid_subjects_file.exists():
        raise FileNotFoundError(f"Valid subjects file not found: {valid_subjects_file}")
    
    with open(valid_subjects_file, 'r') as f:
        subjects = [line.strip() for line in f if line.strip()]
    return subjects

def find_event_tsv(subject_dir: Path) -> Optional[Path]:
    """
    Locates the events.tsv file for a given subject directory.
    Expected path structure: subject_dir/func/sub-<id>_task-<task>_events.tsv
    """
    func_dir = subject_dir / "func"
    if not func_dir.exists():
        return None
    
    # Look for events.tsv files
    event_files = list(func_dir.glob("*events.tsv"))
    if not event_files:
        return None
    
    # Assuming the first one is the relevant one for the motor task
    return event_files[0]

def extract_trial_rts(events_file: Path) -> pd.DataFrame:
    """
    Reads an events.tsv file and extracts trial-wise RTs.
    
    Returns a DataFrame with columns:
    - subject_id
    - trial_index
    - rt (in seconds or ms depending on raw data, normalized to ms here)
    - condition (if available)
    """
    if not events_file.exists():
        raise FileNotFoundError(f"Events file not found: {events_file}")

    df = pd.read_csv(events_file, sep='\t')

    # Standard BIDS events.tsv usually has 'onset', 'duration', 'trial_type'
    # We need 'reaction_time' or 'rt'. If not present, we might need to derive from onset/duration
    # but typically behavioral data includes an 'rt' column.
    
    if 'reaction_time' in df.columns:
        rt_col = 'reaction_time'
    elif 'rt' in df.columns:
        rt_col = 'rt'
    else:
        # Fallback: If no explicit RT, we cannot calculate it from onset/duration alone
        # without knowing the stimulus duration vs response time logic.
        # However, for ds000246 (Auditory Feedback), 'reaction_time' is standard.
        raise KeyError(f"Could not find 'reaction_time' or 'rt' column in {events_file}. Columns: {df.columns.tolist()}")

    # Clean data
    df = df.dropna(subset=[rt_col])
    df = df[df[rt_col] > 0] # Remove non-positive RTs

    # Convert to milliseconds if the unit is seconds (common in BIDS)
    # We assume seconds if values are < 10, else ms. 
    # ds000246 typically uses seconds.
    if df[rt_col].max() < 10:
        df['rt_ms'] = df[rt_col] * 1000
    else:
        df['rt_ms'] = df[rt_col]

    # Add trial index
    df['trial_index'] = range(1, len(df) + 1)
    
    # Extract subject ID from path
    subject_id = subject_id_from_path(events_file)
    
    result = pd.DataFrame({
        'subject_id': subject_id,
        'trial_index': df['trial_index'].values,
        'rt_ms': df[rt_col].values,
        'condition': df['trial_type'].values if 'trial_type' in df.columns else 'unknown'
    })
    
    return result

def subject_id_from_path(file_path: Path) -> str:
    """
    Extracts subject ID (e.g., 'sub-01') from a BIDS path.
    """
    # Path usually looks like: data/raw/sub-01/func/...
    parts = file_path.parts
    for i, part in enumerate(parts):
        if part.startswith('sub-'):
            return part
    raise ValueError(f"Could not extract subject ID from path: {file_path}")

def calculate_learning_rate_slope(trial_data: pd.DataFrame) -> float:
    """
    Calculates the learning rate slope (RT change over trials) using OLS.
    Note: T031 only extracts metrics. T032 calculates the slope.
    This function is provided for API compatibility but logic is deferred to T032.
    """
    # Placeholder for API compatibility
    return 0.0

def process_subject_behavior(subject_dir: Path, output_csv: Path, logger: logging.Logger) -> bool:
    """
    Processes a single subject's behavioral data:
    1. Finds events.tsv
    2. Extracts RTs
    3. Calculates mean RT per subject
    4. Appends to the aggregate CSV
    """
    event_file = find_event_tsv(subject_dir)
    if not event_file:
        logger.warning(f"No events.tsv found for {subject_dir}. Skipping.")
        return False

    try:
        df = extract_trial_rts(event_file)
        if df.empty:
            logger.warning(f"No valid RTs found for {subject_dir}. Skipping.")
            return False

        # Calculate mean RT for this subject
        mean_rt = df['rt_ms'].mean()
        std_rt = df['rt_ms'].std()
        n_trials = len(df)

        # Create a summary row
        summary_row = pd.DataFrame([{
            'subject_id': df['subject_id'].iloc[0],
            'mean_rt': mean_rt,
            'std_rt': std_rt,
            'n_trials': n_trials
        }])

        # Append to output file
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        if output_csv.exists():
            existing = pd.read_csv(output_csv)
            combined = pd.concat([existing, summary_row], ignore_index=True)
            combined.to_csv(output_csv, index=False)
        else:
            summary_row.to_csv(output_csv, index=False)

        logger.info(f"Processed {subject_dir.name}: Mean RT = {mean_rt:.2f}ms (n={n_trials})")
        return True

    except Exception as e:
        logger.error(f"Error processing {subject_dir}: {e}", exc_info=True)
        return False

# --- Main Entry Point ---

def main():
    """
    Main execution flow for T031:
    1. Load valid subjects list.
    2. Iterate through data/raw/<subject>/ directories.
    3. Extract RTs and compute mean RT per subject.
    4. Save to data/processed/behavioral_metrics.csv.
    """
    # Paths
    project_root = Path(__file__).resolve().parent.parent
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    valid_subjects_file = data_processed / "valid_subjects.txt"
    output_file = data_processed / "behavioral_metrics.csv"
    log_file = data_processed / "behavior_processing.log"

    # Setup logging
    logger = setup_logging(log_file)
    logger.info("Starting behavioral metric extraction (T031)...")

    if not data_raw.exists():
        logger.error("Data raw directory not found. Run T018a first.")
        sys.exit(1)

    if not valid_subjects_file.exists():
        logger.error(f"Valid subjects file not found: {valid_subjects_file}. Run T017 first.")
        sys.exit(1)

    subjects = load_valid_subjects(valid_subjects_file)
    logger.info(f"Found {len(subjects)} valid subjects to process.")

    processed_count = 0
    for subj in subjects:
        subject_dir = data_raw / subj
        if subject_dir.exists():
            success = process_subject_behavior(subject_dir, output_file, logger)
            if success:
                processed_count += 1
        else:
            logger.warning(f"Subject directory not found: {subject_dir}")

    logger.info(f"Completed processing. {processed_count}/{len(subjects)} subjects processed.")
    logger.info(f"Output saved to: {output_file}")

    if not output_file.exists():
        logger.error("Failed to generate output file.")
        sys.exit(1)

    logger.info("T031 completed successfully.")

if __name__ == "__main__":
    main()
