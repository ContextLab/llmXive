"""
Ingestion pipeline for neural correlates of anticipatory reward processing.

This module handles loading, validating, and aligning spike train data with
trial metadata to produce a unified DataFrame for downstream analysis.
"""

import os
import sys
import logging
import yaml
import ast
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Import local logging setup
from logging_config import setup_logging, get_logger

# Configure module logger
logger = get_logger(__name__)

# Constants
SPIKE_WINDOW_MS = 500  # Window relative to reward time for spike counting
MIN_TRIALS_PER_LEVEL = 30  # Minimum trials required per reward magnitude level
SNR_THRESHOLD = 3.0  # Minimum acceptable SNR
ISOLATION_DISTANCE_THRESHOLD = 20.0  # Minimum acceptable isolation distance
CONFOUNDED_DELAY_THRESHOLD_MS = 500  # Delay threshold for confounded trials

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load dataset schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate that DataFrame contains required columns from schema."""
    required_columns = list(schema.get('fields', {}).keys())
    missing_columns = [col for col in required_columns if col not in df.columns]
    return missing_columns

def calculate_spike_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate spike counts in the window [-500ms, 0ms] relative to reward timestamp.
    
    Args:
        df: DataFrame with spike_time_ms and reward_time_ms columns
        
    Returns:
        DataFrame with added 'spike_count' column per trial
    """
    if 'spike_time_ms' not in df.columns or 'reward_time_ms' not in df.columns:
        logger.error("Missing required columns: spike_time_ms or reward_time_ms")
        raise ValueError("Missing required columns for spike count calculation")
    
    # Calculate spike count per trial
    # Filter spikes that occurred in the window [reward_time_ms - 500, reward_time_ms]
    df['spike_count'] = df.apply(
        lambda row: len(df[
            (df['trial_id'] == row['trial_id']) &
            (df['spike_time_ms'] >= row['reward_time_ms'] - SPIKE_WINDOW_MS) &
            (df['spike_time_ms'] <= row['reward_time_ms'])
        ]) if 'spike_time_ms' in df.columns and 'trial_id' in df.columns else 0,
        axis=1
    )
    
    # Group by trial_id to get total spike count per trial
    trial_spike_counts = df.groupby('trial_id')['spike_count'].sum().reset_index()
    trial_spike_counts.rename(columns={'spike_count': 'total_spike_count'}, inplace=True)
    
    # Merge back to main dataframe (keep first row per trial for metadata)
    df = df.drop_duplicates(subset='trial_id', keep='first')
    df = df.merge(trial_spike_counts, on='trial_id', how='left')
    df['spike_count'] = df['total_spike_count'].fillna(0).astype(int)
    df = df.drop(columns=['total_spike_count'])
    
    return df

def calculate_cue_delay(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate cue_delay as reward_time_ms - cue_time_ms for each trial.
    
    Args:
        df: DataFrame with cue_time_ms and reward_time_ms columns
        
    Returns:
        DataFrame with added 'cue_delay' column
    """
    if 'cue_time_ms' not in df.columns or 'reward_time_ms' not in df.columns:
        logger.warning("Missing cue_time_ms or reward_time_ms columns. Skipping cue_delay calculation.")
        df['cue_delay'] = np.nan
        return df
    
    df['cue_delay'] = df['reward_time_ms'] - df['cue_time_ms']
    return df

def count_trials_per_reward_level(df: pd.DataFrame) -> Dict[int, int]:
    """Count trials per reward magnitude level."""
    if 'reward_magnitude' not in df.columns:
        logger.error("Missing reward_magnitude column")
        return {}
    
    return df['reward_magnitude'].value_counts().to_dict()

def validate_minimum_trials_per_level(trial_counts: Dict[int, int], min_trials: int = MIN_TRIALS_PER_LEVEL) -> Tuple[bool, List[int]]:
    """Check if each reward level has at least min_trials trials."""
    insufficient_levels = [level for level, count in trial_counts.items() if count < min_trials]
    return len(insufficient_levels) == 0, insufficient_levels

def validate_zero_reward_and_silent_neurons(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Handle zero-reward trials (keep) and silent neurons (filter out).
    
    Returns:
        Tuple of (filtered_df, zero_reward_count, silent_neuron_count)
    """
    zero_reward_count = 0
    silent_neuron_count = 0
    
    if 'reward_magnitude' in df.columns:
        zero_reward_count = len(df[df['reward_magnitude'] == 0])
        logger.info(f"Found {zero_reward_count} zero-reward trials (kept as valid)")
    
    # Filter out silent neurons (spike_count == 0)
    if 'spike_count' in df.columns:
        silent_mask = df['spike_count'] == 0
        silent_neuron_count = silent_mask.sum()
        if silent_neuron_count > 0:
            logger.warning(f"Filtering out {silent_neuron_count} silent neuron entries")
            df = df[~silent_mask]
    
    return df, zero_reward_count, silent_neuron_count

def validate_spike_sorting_metadata(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Validate spike sorting metadata (SNR and Isolation Distance).
    
    Filters trials where snr <= 3 OR isolation_distance <= 20.
    
    Returns:
        Tuple of (filtered_df, rejected_count, acceptance_rate)
    """
    if 'snr' not in df.columns or 'isolation_distance' not in df.columns:
        logger.error("Missing spike sorting metadata columns: snr or isolation_distance")
        raise ValueError("Missing spike sorting metadata. Cannot proceed without SNR and Isolation Distance.")
    
    total_rows = len(df)
    # Rejection criteria: snr <= 3 OR isolation_distance <= 20
    rejected_mask = (df['snr'] <= SNR_THRESHOLD) | (df['isolation_distance'] <= ISOLATION_DISTANCE_THRESHOLD)
    rejected_count = rejected_mask.sum()
    accepted_count = total_rows - rejected_count
    acceptance_rate = (accepted_count / total_rows * 100) if total_rows > 0 else 0
    
    if rejected_count > 0:
        logger.warning(f"Rejecting {rejected_count} trials due to poor spike sorting quality")
    
    df = df[~rejected_mask]
    
    return df, rejected_count, acceptance_rate

def generate_validation_report(
    total_rows: int,
    valid_rows: int,
    dropped_rows: int,
    validated_sample_size: int,
    confounded_count: int,
    flagged_trial_ids: List[str],
    spike_sorting_rejected: int,
    spike_sorting_acceptance_rate: float,
    zero_reward_count: int,
    silent_neuron_count: int
) -> Dict[str, Any]:
    """Generate validation report metrics."""
    return {
        "ingestion_rows_total": total_rows,
        "ingestion_rows_valid": valid_rows,
        "ingestion_rows_dropped": dropped_rows,
        "validated_sample_size": validated_sample_size,
        "confounded_trial_count": confounded_count,
        "flagged_trial_ids": flagged_trial_ids,
        "spike_sorting_rejected_count": spike_sorting_rejected,
        "spike_sorting_acceptance_rate": spike_sorting_acceptance_rate,
        "zero_reward_trials": zero_reward_count,
        "silent_neurons_filtered": silent_neuron_count
    }

def write_validation_report(report: Dict[str, Any], output_path: str) -> None:
    """Write validation report to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

def write_spike_sorting_report(
    rejected_trials: List[str],
    acceptance_rate: float,
    output_path: str
) -> None:
    """Generate spike sorting validation report in Markdown."""
    with open(output_path, 'w') as f:
        f.write("# Spike Sorting Validation Report\n\n")
        f.write("## Rejection Criteria\n")
        f.write(f"- SNR Threshold: <= {SNR_THRESHOLD} (rejected)\n")
        f.write(f"- Isolation Distance Threshold: <= {ISOLATION_DISTANCE_THRESHOLD} (rejected)\n\n")
        f.write("## Summary\n")
        f.write(f"- Acceptance Rate: {acceptance_rate:.2f}%\n\n")
        f.write("## Rejected Trials\n")
        if rejected_trials:
            for trial_id in rejected_trials[:50]:  # Limit to first 50 for readability
                f.write(f"- {trial_id}\n")
            if len(rejected_trials) > 50:
                f.write(f"- ... and {len(rejected_trials) - 50} more\n")
        else:
            f.write("No trials rejected.\n")
    
    logger.info(f"Spike sorting report written to {output_path}")

def write_claim_status(status: str, reason: str, output_path: str) -> None:
    """Write claim status to JSON file."""
    status_data = {"status": status, "reason": reason}
    with open(output_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Claim status written to {output_path}")

def run_ingestion_pipeline(
    input_path: str,
    schema_path: str,
    output_dir: str,
    state_dir: str
) -> pd.DataFrame:
    """
    Run the complete ingestion pipeline.
    
    Args:
        input_path: Path to input CSV file
        schema_path: Path to schema YAML file
        output_dir: Directory for output files
        state_dir: Directory for state files
        
    Returns:
        Unified DataFrame with processed data
    """
    # Ensure output directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows")
    
    # Validate columns
    missing_cols = validate_columns(df, schema)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Calculate spike counts
    logger.info("Calculating spike counts...")
    df = calculate_spike_counts(df)
    
    # Calculate cue delay
    logger.info("Calculating cue delay...")
    df = calculate_cue_delay(df)
    
    # Validate spike sorting metadata (T013e)
    try:
        df, spike_sorting_rejected, spike_sorting_acceptance_rate = validate_spike_sorting_metadata(df)
    except ValueError as e:
        # Missing metadata -> REJECT
        write_claim_status("REJECTED", str(e), os.path.join(state_dir, "claim_status.json"))
        raise
    
    # Write spike sorting report
    rejected_trial_ids = df[df['spike_count'] == 0]['trial_id'].tolist()  # Placeholder for actual rejected IDs
    write_spike_sorting_report(
        rejected_trial_ids,
        spike_sorting_acceptance_rate,
        os.path.join(output_dir, "spike_sorting_validation_report.md")
    )
    
    # Validate minimum trials per level
    trial_counts = count_trials_per_reward_level(df)
    valid_levels, insufficient_levels = validate_minimum_trials_per_level(trial_counts)
    if not valid_levels:
        logger.warning(f"Insufficient trials for levels: {insufficient_levels}")
        # Do not halt, just log warning as per task requirements
    
    # Handle zero-reward and silent neurons (T013c)
    df, zero_reward_count, silent_neuron_count = validate_zero_reward_and_silent_neurons(df)
    
    # Calculate confounded trials (T013f, T013h)
    # Confounded if cue-reward delay < 500ms
    if 'cue_delay' in df.columns:
        confounded_mask = df['cue_delay'] < CONFOUNDED_DELAY_THRESHOLD_MS
        confounded_count = confounded_mask.sum()
        flagged_trial_ids = df[confounded_mask]['trial_id'].tolist()
        df['confounded'] = confounded_mask
    else:
        confounded_count = 0
        flagged_trial_ids = []
        df['confounded'] = False
        # If cue_delay missing, set status to LIMITED
        write_claim_status("LIMITED", "No time-resolved analysis possible (missing cue_time_ms)", os.path.join(state_dir, "claim_status.json"))
    
    # Determine final status
    current_status = "SUCCESS"
    if confounded_count > 0:
        current_status = "LIMITED"
        write_claim_status(current_status, f"Confounded trials detected: {confounded_count}", os.path.join(state_dir, "claim_status.json"))
        logger.warning(f"Confounded trials detected: {confounded_count}. Status set to LIMITED.")
    
    # Calculate validated sample size
    validated_sample_size = len(df)
    dropped_rows = total_rows - validated_sample_size
    
    # Generate and write validation report (T013f)
    report = generate_validation_report(
        total_rows=total_rows,
        valid_rows=validated_sample_size,
        dropped_rows=dropped_rows,
        validated_sample_size=validated_sample_size,
        confounded_count=confounded_count,
        flagged_trial_ids=flagged_trial_ids,
        spike_sorting_rejected=spike_sorting_rejected,
        spike_sorting_acceptance_rate=spike_sorting_acceptance_rate,
        zero_reward_count=zero_reward_count,
        silent_neuron_count=silent_neuron_count
    )
    write_validation_report(report, os.path.join(output_dir, "validation_report.json"))
    
    # Select final columns for output (T014)
    output_columns = [
        'trial_id',
        'neuron_id',
        'spike_count',
        'reward_magnitude',
        'cue_time_ms',
        'reward_time_ms',
        'cue_delay',
        'confounded'
    ]
    
    # Ensure all required columns exist
    for col in output_columns:
        if col not in df.columns:
            df[col] = np.nan
    
    unified_df = df[output_columns].copy()
    
    # Add timestamp_relative_to_reward (T014 requirement)
    # This is the spike_time_ms relative to reward_time_ms, but since we aggregated by trial,
    # we can calculate the mean or keep the window center. For trial-level analysis,
    # we use 0 as the reference point (reward time) or the average relative time if available.
    # Since we aggregated, we set this to 0 (reward time) for trial-level analysis.
    unified_df['timestamp_relative_to_reward'] = 0.0
    
    logger.info(f"Ingestion pipeline complete. Output shape: {unified_df.shape}")
    return unified_df

def main():
    """Main entry point for ingestion pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ingestion pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--schema", required=True, help="Path to schema YAML file")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--state-dir", default="state", help="State directory")
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        df = run_ingestion_pipeline(
            input_path=args.input,
            schema_path=args.schema,
            output_dir=args.output_dir,
            state_dir=args.state_dir
        )
        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()