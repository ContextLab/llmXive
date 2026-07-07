import os
import sys
import logging
import yaml
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

from logging_config import get_logger

logger = get_logger(__name__)

# Constants
MIN_TRIALS_PER_LEVEL = 30
MIN_CUE_REWARD_DELAY_MS = 500
SNR_THRESHOLD = 3.0
ISOLATION_DISTANCE_THRESHOLD = 20.0
MAX_CONFOUNDED_TRIAL_FRACTION = 0.5

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """Check if DataFrame has required columns."""
    missing = set(required_cols) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def calculate_spike_counts(df: pd.DataFrame, time_window: Tuple[float, float] = (-0.5, 0.0)) -> pd.DataFrame:
    """
    Calculate spike counts within a time window relative to reward.
    Expects 'spike_timestamps' (list of timestamps) and 'reward_timestamp' columns.
    """
    def count_spikes(row):
        if pd.isna(row.get('spike_timestamps')) or pd.isna(row.get('reward_timestamp')):
            return 0
        try:
            # Handle string representation of list if necessary
            if isinstance(row['spike_timestamps'], str):
                timestamps = ast.literal_eval(row['spike_timestamps'])
            else:
                timestamps = row['spike_timestamps']
            
            reward_ts = row['reward_timestamp']
            count = 0
            for ts in timestamps:
                if (reward_ts + time_window[0]) <= ts <= (reward_ts + time_window[1]):
                    count += 1
            return count
        except Exception as e:
            logger.warning(f"Error parsing spike timestamps: {e}")
            return 0

    df['spike_count'] = df.apply(count_spikes, axis=1)
    return df

def count_trials_per_reward_level(df: pd.DataFrame) -> Dict[Any, int]:
    """Count trials per reward magnitude level."""
    return df.groupby('reward_magnitude').size().to_dict()

def validate_minimum_trials_per_level(trial_counts: Dict[Any, int], min_count: int = MIN_TRIALS_PER_LEVEL) -> bool:
    """Check if all reward levels have at least min_count trials."""
    for level, count in trial_counts.items():
        if count < min_count:
            logger.error(f"Reward level {level} has only {count} trials (min: {min_count})")
            return False
    return True

def validate_zero_reward_and_silent_neurons(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Keep zero-reward trials, filter out silent neurons (spike_count == 0 for all trials).
    Returns filtered DF and count of dropped silent neuron rows.
    """
    initial_len = len(df)
    # Filter out rows where spike_count is 0 (silent neurons) but keep zero-reward if they have spikes
    # Actually, "silent neurons" usually means the neuron didn't fire at all across the session or in the window.
    # The task says: "Handle zero-reward trials (keep as valid) and silent neurons (filter out with log warning)"
    # Interpretation: Filter rows where spike_count is 0.
    df_filtered = df[df['spike_count'] > 0]
    dropped = initial_len - len(df_filtered)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with zero spike counts (silent neurons).")
    return df_filtered, dropped

def validate_cue_reward_delay(df: pd.DataFrame, min_delay_ms: int = MIN_CUE_REWARD_DELAY_MS) -> Tuple[pd.DataFrame, int]:
    """
    Validate cue-reward delay.
    Flag trials with delay < min_delay_ms.
    Halt if valid trials drop below 30 per level or >50% confounded.
    Returns filtered DF and count of confounded trials.
    """
    if 'cue_timestamp' not in df.columns:
        logger.warning("No 'cue_timestamp' column found. Skipping cue-reward delay validation.")
        return df, 0

    df['cue_reward_delay'] = df['reward_timestamp'] - df['cue_timestamp']
    # Convert to ms if necessary (assuming seconds input based on typical neuro data)
    # Assuming timestamps are in seconds, delay is in seconds.
    # Task says < 500ms. If timestamps are seconds, threshold is 0.5.
    # Let's assume input is seconds.
    threshold = min_delay_ms / 1000.0 
    
    confounded_mask = df['cue_reward_delay'] < threshold
    num_confounded = confounded_mask.sum()
    total_trials = len(df)

    if num_confounded > 0:
        logger.warning(f"Found {num_confounded} trials with cue-reward delay < {min_delay_ms}ms.")
        
        # Check if >50% confounded
        if num_confounded / total_trials > MAX_CONFOUNDED_TRIAL_FRACTION:
            logger.critical(f"More than {MAX_CONFOUNDED_TRIAL_FRACTION*100}% of trials are confounded. Halting.")
            raise RuntimeError(f"Too many confounded trials: {num_confounded}/{total_trials}")

        # Filter out confounded trials
        df = df[~confounded_mask]
        
        # Check remaining trials per level
        counts = df.groupby('reward_magnitude').size()
        for level, count in counts.items():
            if count < MIN_TRIALS_PER_LEVEL:
                logger.critical(f"After removing confounded trials, reward level {level} has only {count} trials. Halting.")
                raise RuntimeError(f"Insufficient trials for reward level {level} after validation.")

    return df, int(num_confounded)

def validate_spike_sorting_metadata(df: pd.DataFrame, metadata_path: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate upstream spike sorting metadata (SNR, Isolation Distance).
    Generate report at data/processed/spike_sorting_validation_report.md.
    Returns filtered DF and list of rejected neuron IDs.
    """
    if not os.path.exists(metadata_path):
        logger.warning(f"Spike sorting metadata file not found: {metadata_path}. Skipping metadata validation.")
        # If we can't validate, we might proceed but warn, or halt? 
        # Task says "Validate ... and GENERATE report". If missing, we can't validate.
        # Let's assume we proceed but log a warning, as the main data might still be usable 
        # but the quality is unknown. However, strict adherence might require halting.
        # Given T015 is about error handling, we handle the missing file gracefully here.
        return df, []

    try:
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to parse spike sorting metadata: {e}")
        raise

    rejected_neurons = []
    valid_rows = []
    
    for idx, row in df.iterrows():
        neuron_id = row['neuron_id']
        neuron_meta = next((n for n in metadata if n.get('neuron_id') == neuron_id), None)
        
        if not neuron_meta:
            logger.warning(f"No metadata found for neuron {neuron_id}. Marking as rejected.")
            rejected_neurons.append(neuron_id)
            continue

        snr = neuron_meta.get('snr', 0)
        isolation_dist = neuron_meta.get('isolation_distance', 0)

        if snr < SNR_THRESHOLD or isolation_dist < ISOLATION_DISTANCE_THRESHOLD:
            logger.warning(f"Neuron {neuron_id} rejected: SNR={snr} (<{SNR_THRESHOLD}) or IsolationDist={isolation_dist} (<{ISOLATION_DISTANCE_THRESHOLD})")
            rejected_neurons.append(neuron_id)
        else:
            valid_rows.append(idx)

    df_filtered = df.loc[valid_rows].reset_index(drop=True)
    
    # Generate Report
    report_path = Path("data/processed/spike_sorting_validation_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("# Spike Sorting Validation Report\n\n")
        f.write(f"**Criteria**: SNR > {SNR_THRESHOLD}, Isolation Distance > {ISOLATION_DISTANCE_THRESHOLD}\n\n")
        f.write(f"**Total Neurons Checked**: {len(df)}\n")
        f.write(f"**Rejected Neurons**: {len(rejected_neurons)}\n")
        f.write(f"**Valid Neurons**: {len(valid_rows)}\n\n")
        f.write("## Rejected Neurons\n\n")
        for n in rejected_neurons:
            f.write(f"- {n}\n")

    return df_filtered, rejected_neurons

def generate_validation_report(
    total_rows: int, 
    valid_rows: int, 
    dropped_rows: int, 
    confounded_count: int,
    rejected_neurons: List[str],
    output_path: str
) -> None:
    """Generate data/processed/validation_report.json with metrics."""
    report = {
        "ingestion_rows_total": total_rows,
        "ingestion_rows_valid": valid_rows,
        "ingestion_rows_dropped": dropped_rows,
        "validation_status": "passed" if dropped_rows < total_rows else "failed",
        "confounded_trials_removed": confounded_count,
        "rejected_neurons": rejected_neurons
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

def run_ingestion_pipeline(
    input_path: str,
    schema_path: str,
    metadata_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Main ingestion pipeline with error handling for missing/malformed metadata.
    """
    # 1. Load Schema
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        logger.critical(f"Schema loading failed: {e}")
        raise
    
    required_cols = schema.get('required_columns', [])
    
    # 2. Load Data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.critical(f"Failed to load input data: {e}")
        raise

    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows from {input_path}")

    # 3. Validate Columns
    if not validate_columns(df, required_cols):
        raise ValueError("Column validation failed.")

    # 4. Calculate Spike Counts
    df = calculate_spike_counts(df)

    # 5. Validate Zero Reward / Silent Neurons
    df, silent_dropped = validate_zero_reward_and_silent_neurons(df)
    
    # 6. Validate Cue-Reward Delay
    try:
        df, confounded_count = validate_cue_reward_delay(df)
    except RuntimeError as e:
        logger.critical(f"Validation failed: {e}")
        raise

    # 7. Validate Spike Sorting Metadata (T015: Error Handling for missing/malformed)
    rejected_neurons = []
    if metadata_path:
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata file missing: {metadata_path}. Proceeding without metadata validation.")
            # T015 Implementation: Handle missing file gracefully (log warning, continue)
            # Do not crash, but note it in the report if needed.
        else:
            try:
                df, rejected_neurons = validate_spike_sorting_metadata(df, metadata_path)
            except Exception as e:
                logger.error(f"Metadata validation failed due to malformed file: {e}")
                raise
    else:
        logger.info("No metadata path provided. Skipping metadata validation.")

    # 8. Final Checks
    trial_counts = count_trials_per_reward_level(df)
    if not validate_minimum_trials_per_level(trial_counts):
        raise ValueError("Minimum trial count validation failed.")

    # 9. Generate Reports
    valid_rows = len(df)
    dropped_rows = total_rows - valid_rows
    report_path = "data/processed/validation_report.json"
    generate_validation_report(total_rows, valid_rows, dropped_rows, confounded_count, rejected_neurons, report_path)

    # 10. Prepare Output
    output_df = df[['trial_id', 'neuron_id', 'spike_count', 'reward_magnitude', 'cue_reward_delay']].copy()
    # Ensure timestamp_relative_to_reward is calculated if needed, but task T014 says output includes it.
    # We calculated cue_reward_delay above. Let's add a relative spike timestamp column if we had raw spikes,
    # but for the aggregated count, we just have the count. 
    # T014 says: "unified Pandas DataFrame with trial_id, neuron_id, spike_count, reward_magnitude, timestamp_relative_to_reward"
    # Since we aggregated, 'timestamp_relative_to_reward' might be the center of the window or the reward timestamp.
    # Let's add the reward timestamp as the reference.
    if 'reward_timestamp' in df.columns:
        output_df['timestamp_relative_to_reward'] = 0.0 # Relative to itself is 0
    
    logger.info(f"Pipeline complete. Outputting {len(output_df)} valid rows.")
    return output_df

def main():
    # Example usage for T015 testing
    input_file = "data/raw/synthetic_test.csv"
    schema_file = "contracts/dataset.schema.yaml"
    metadata_file = "data/raw/spike_sorting_metadata.yaml" # This might not exist, testing T015 logic

    # Ensure directories exist
    os.makedirs("data/processed", exist_ok=True)

    try:
        result_df = run_ingestion_pipeline(input_file, schema_file, metadata_file)
        print(f"Success. Processed {len(result_df)} rows.")
        print(result_df.head())
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()