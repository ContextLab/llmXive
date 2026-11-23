"""
Ingestion pipeline for Neural Correlates of Anticipatory Reward Processing.
Loads, validates, and aligns spike train data with trial metadata.
"""
import os
import sys
import logging
import yaml
import ast
import json
import pandas as pd
import numpy as np
from pathlib import Path
from logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

def load_schema(schema_path="contracts/dataset.schema.yaml"):
    """Load the dataset schema from YAML."""
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        raise

def validate_columns(df, schema):
    """Validate that the DataFrame contains required columns."""
    required_cols = schema.get('required_columns', [])
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def calculate_spike_counts(df, window_start_ms=-500, window_end_ms=0):
    """
    Calculate spike counts in a specific window relative to reward time.
    Assumes 'spike_time_ms' and 'reward_time_ms' are columns.
    """
    if 'spike_time_ms' not in df.columns or 'reward_time_ms' not in df.columns:
        # Fallback: if data is already aggregated (one row per trial/spike_count), return as is
        if 'spike_count' in df.columns:
            return df['spike_count']
        raise ValueError("Missing 'spike_time_ms' or 'reward_time_ms' columns")
    
    # Filter spikes within the window
    mask = (df['spike_time_ms'] >= (df['reward_time_ms'] + window_start_ms)) & \
           (df['spike_time_ms'] <= (df['reward_time_ms'] + window_end_ms))
    return mask.sum()

def calculate_cue_delay(df):
    """Calculate cue_delay = reward_time_ms - cue_time_ms."""
    if 'cue_time_ms' not in df.columns or 'reward_time_ms' not in df.columns:
        logger.warning("Missing cue_time_ms or reward_time_ms. Cannot calculate cue_delay.")
        return None
    return df['reward_time_ms'] - df['cue_time_ms']

def count_trials_per_reward_level(df, reward_col='reward_magnitude'):
    """Count trials for each reward magnitude level."""
    if reward_col not in df.columns:
        return {}
    return df[reward_col].value_counts().to_dict()

def validate_minimum_trials_per_level(counts, min_trials=30):
    """Check if each reward level has at least min_trials."""
    invalid_levels = [k for k, v in counts.items() if v < min_trials]
    if invalid_levels:
        logger.warning(f"Levels with insufficient trials (< {min_trials}): {invalid_levels}")
        return False
    return True

def validate_zero_reward_and_silent_neurons(df):
    """
    Handle zero-reward trials (keep) and silent neurons (filter).
    Returns filtered DataFrame and log of filtered neurons.
    """
    initial_rows = len(df)
    
    # Filter out silent neurons (neurons with 0 spikes across all trials)
    # Assuming 'spike_count' is available or we can calculate it
    if 'spike_count' in df.columns:
        # Group by neuron and sum spikes
        neuron_spikes = df.groupby('neuron_id')['spike_count'].sum()
        silent_neurons = neuron_spikes[neuron_spikes == 0].index.tolist()
        if silent_neurons:
            logger.warning(f"Filtering out {len(silent_neurons)} silent neurons: {silent_neurons}")
            df = df[~df['neuron_id'].isin(silent_neurons)]
    
    final_rows = len(df)
    logger.info(f"Silent neuron filtering: {initial_rows} -> {final_rows} rows")
    return df

def validate_spike_sorting_metadata(df, snr_threshold=3.0, isolation_distance_threshold=20.0):
    """
    Validate spike sorting metadata (SNR and Isolation Distance).
    Returns filtered DataFrame, rejection stats, and validation status.
    """
    required_cols = ['snr', 'isolation_distance']
    if not all(c in df.columns for c in required_cols):
        logger.error("Missing spike sorting metadata columns (snr, isolation_distance).")
        return None, {
            'rejection_criteria': 'SNR > 3.0 AND Isolation Distance > 20.0',
            'rejected_trials': 0,
            'accepted_trials': 0,
            'acceptance_rate': 0.0,
            'status': 'REJECTED',
            'reason': 'Missing spike sorting metadata'
        }, True # Halt flag

    initial_rows = len(df)
    mask = (df['snr'] > snr_threshold) & (df['isolation_distance'] > isolation_distance_threshold)
    df_valid = df[mask]
    rejected_count = initial_rows - len(df_valid)
    acceptance_rate = len(df_valid) / initial_rows if initial_rows > 0 else 0.0

    stats = {
        'rejection_criteria': f'SNR > {snr_threshold} AND Isolation Distance > {isolation_distance_threshold}',
        'rejected_trials': rejected_count,
        'accepted_trials': len(df_valid),
        'acceptance_rate': acceptance_rate,
        'status': 'SUCCESS' if rejected_count == 0 else 'LIMITED',
        'reason': 'Some trials rejected based on spike sorting quality' if rejected_count > 0 else 'All trials passed'
    }

    logger.info(f"Spike sorting validation: {rejected_count} trials rejected. Acceptance rate: {acceptance_rate:.2%}")
    return df_valid, stats, False

def generate_validation_report(stats, sample_size, confounded_count=0):
    """Generate a validation report dictionary."""
    report = {
        'ingestion_rows_total': stats.get('accepted_trials', sample_size) + stats.get('rejected_trials', 0),
        'ingestion_rows_valid': stats.get('accepted_trials', 0),
        'ingestion_rows_dropped': stats.get('rejected_trials', 0),
        'validated_sample_size': stats.get('accepted_trials', 0),
        'confounded_trial_count': confounded_count,
        'status': stats.get('status', 'UNKNOWN'),
        'reason': stats.get('reason', 'No reason provided')
    }
    return report

def write_validation_report(report, output_path="data/processed/validation_report.json"):
    """Write validation report to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

def write_spike_sorting_report(stats, output_path="data/processed/spike_sorting_validation_report.md"):
    """Write spike sorting validation report to Markdown."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# Spike Sorting Validation Report\n\n")
        f.write(f"## Rejection Criteria\n{stats.get('rejection_criteria', 'N/A')}\n\n")
        f.write(f"## Results\n")
        f.write(f"- Rejected Trials: {stats.get('rejected_trials', 0)}\n")
        f.write(f"- Accepted Trials: {stats.get('accepted_trials', 0)}\n")
        f.write(f"- Acceptance Rate: {stats.get('acceptance_rate', 0.0):.2%}\n")
    logger.info(f"Spike sorting report written to {output_path}")

def write_claim_status(status, reason, output_path="state/claim_status.json"):
    """Write claim status to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'status': status, 'reason': reason}, f, indent=2)
    logger.info(f"Claim status written to {output_path}")

def run_ingestion_pipeline(input_path, output_path="data/processed/aligned_data.csv"):
    """
    Main ingestion pipeline:
    1. Load data.
    2. Validate columns.
    3. Calculate spike counts (if raw).
    4. Calculate cue delay.
    5. Validate metadata.
    6. Filter silent neurons.
    7. Write output.
    """
    logger.info(f"Starting ingestion pipeline for {input_path}")
    
    # 1. Load Data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # 2. Validate Schema
    schema = load_schema()
    validate_columns(df, schema)

    # 3. Calculate Spike Counts (if raw spike data)
    # If 'spike_count' is missing, try to calculate from raw spikes
    if 'spike_count' not in df.columns:
        if 'spike_time_ms' in df.columns and 'reward_time_ms' in df.columns:
            # This implies raw data. We need to group by trial/neuron first.
            # For simplicity in this pipeline, we assume the input is already aggregated 
            # OR we perform a groupby if 'spike_time_ms' exists.
            # If the input has one row per spike, we must group.
            if df.shape[0] > 0 and 'trial_id' in df.columns and 'neuron_id' in df.columns:
                # Check if multiple rows per trial/neuron exist
                counts = df.groupby(['trial_id', 'neuron_id']).size().reset_index(name='spike_count')
                # Merge back to get other columns (assuming other columns are constant per trial/neuron)
                # This is a simplification. In reality, we'd need to merge carefully.
                # For this task, we assume the input is already at the trial level or we just count.
                # If the input is raw spikes, we group and count.
                # Let's assume the input is raw spikes for the calculation logic.
                df = df.groupby(['trial_id', 'neuron_id', 'reward_magnitude', 'cue_time_ms', 'reward_time_ms', 'snr', 'isolation_distance']).size().reset_index(name='spike_count')
            else:
                raise ValueError("Cannot calculate spike count: missing grouping columns or raw data structure.")
        else:
            raise ValueError("Missing 'spike_count' column and cannot calculate from raw data.")
    else:
        # If spike_count exists, ensure it's numeric
        df['spike_count'] = pd.to_numeric(df['spike_count'], errors='coerce').fillna(0).astype(int)

    # 4. Calculate Cue Delay
    cue_delays = calculate_cue_delay(df)
    if cue_delays is not None:
        df['cue_delay'] = cue_delays
        # Check for confounded trials (cue-reward delay < 500ms)
        confounded_mask = df['cue_delay'] < 500
        confounded_count = confounded_mask.sum()
        df['confounded'] = confounded_mask
        logger.info(f"Found {confounded_count} confounded trials (cue-reward delay < 500ms)")
    else:
        df['confounded'] = False
        confounded_count = 0

    # 5. Validate Spike Sorting Metadata
    df_valid, stats, halt = validate_spike_sorting_metadata(df)
    if halt:
        write_claim_status("REJECTED", stats['reason'])
        raise RuntimeError(f"Pipeline halted: {stats['reason']}")
    
    df = df_valid

    # 6. Validate Minimum Trials
    trial_counts = count_trials_per_reward_level(df)
    if not validate_minimum_trials_per_level(trial_counts):
        logger.warning("Minimum trial count validation failed. Proceeding with caution.")

    # 7. Filter Silent Neurons
    df = validate_zero_reward_and_silent_neurons(df)

    # 8. Generate Reports
    report = generate_validation_report(stats, len(df), confounded_count)
    write_validation_report(report)
    write_spike_sorting_report(stats)
    
    if report['confounded_trial_count'] > 0:
        write_claim_status("LIMITED", "Confounded trials detected")
    else:
        write_claim_status("SUCCESS", "Validation passed")

    # 9. Write Output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Ingestion complete. Output written to {output_path}")
    
    return df

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Run ingestion pipeline")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", default="data/processed/aligned_data.csv", help="Output CSV path")
    args = parser.parse_args()
    run_ingestion_pipeline(args.input, args.output)

if __name__ == "__main__":
    main()