"""
Task T012c: Compute Relative Power and Join with Behavioral Metrics.

Implements FR-010: Calculate relative power (band / total power) for each band and channel.
Joins with behavioral metrics using an INNER JOIN, filtered by the feasibility gate.
Aggregates across channels (global mean) per participant.
Output: data/processed/features.csv
"""
import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path to ensure imports work if run from subdirectory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_path, ensure_dirs

def load_band_powers(input_path: str) -> pd.DataFrame:
    """Load the aggregated band powers from T012b."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Band powers file not found: {input_path}")
    df = pd.read_csv(input_path)
    required_cols = ['participant_id', 'channel_id', 'delta', 'theta', 'alpha', 
                     'low_beta', 'high_beta', 'gamma']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Band powers file missing columns: {missing}")
    return df

def load_behavioral_metrics(input_path: str) -> pd.DataFrame:
    """Load behavioral metrics from T013."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Behavioral metrics file not found: {input_path}")
    df = pd.read_csv(input_path)
    required_cols = ['participant_id', 'median_rt']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Behavioral metrics file missing columns: {missing}")
    return df

def load_feasibility_metadata(input_path: str) -> pd.DataFrame:
    """Load the joined metadata from T008a to filter valid participants."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Feasibility metadata file not found: {input_path}")
    df = pd.read_csv(input_path)
    if 'participant_id' not in df.columns:
        raise ValueError(f"Feasibility metadata missing 'participant_id' column")
    return df[['participant_id']]

def compute_relative_power(band_powers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate relative power for each band and channel.
    Relative Power = Band Power / Total Power (sum of all bands).
    """
    band_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    
    # Calculate total power per row (participant, channel)
    band_powers_df['total_power'] = band_powers_df[band_cols].sum(axis=1)
    
    # Avoid division by zero
    band_powers_df['total_power'] = band_powers_df['total_power'].replace(0, np.nan)
    
    # Compute relative power
    relative_power_df = band_powers_df.copy()
    for band in band_cols:
        relative_power_df[f'{band}_rel'] = band_powers_df[band] / band_powers_df['total_power']
    
    # Drop the total_power column as it's not needed in the final aggregation
    relative_power_df = relative_power_df.drop(columns=['total_power'])
    
    return relative_power_df

def aggregate_across_channels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate relative power across channels (global mean) per participant.
    """
    rel_cols = ['delta_rel', 'theta_rel', 'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    
    aggregated = df.groupby('participant_id')[rel_cols].mean().reset_index()
    return aggregated

def join_features(
    rel_power_df: pd.DataFrame,
    behavioral_df: pd.DataFrame,
    feasibility_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Join relative power with behavioral metrics using INNER JOIN.
    Filter by feasibility gate participants.
    """
    # First, join with behavioral metrics (INNER JOIN)
    # This ensures we only keep participants present in both datasets
    merged = pd.merge(
        rel_power_df,
        behavioral_df[['participant_id', 'median_rt']],
        on='participant_id',
        how='inner'
    )
    
    # Then, filter by feasibility gate participants (INNER JOIN)
    # This ensures consistency with the feasibility gate from T008a
    final_df = pd.merge(
        merged,
        feasibility_df,
        on='participant_id',
        how='inner'
    )
    
    return final_df

def main():
    parser = argparse.ArgumentParser(description="Compute relative power and join with behavioral metrics.")
    parser.add_argument(
        "--band-powers", 
        type=str, 
        default=str(get_path("interim", "band_powers.csv")),
        help="Path to band_powers.csv from T012b"
    )
    parser.add_argument(
        "--behavioral", 
        type=str, 
        default=str(get_path("interim", "behavioral_metrics.csv")),
        help="Path to behavioral_metrics.csv from T013"
    )
    parser.add_argument(
        "--feasibility", 
        type=str, 
        default=str(get_path("interim", "joined_metadata.csv")),
        help="Path to joined_metadata.csv from T008a"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(get_path("processed", "features.csv")),
        help="Path for output features.csv"
    )
    
    args = parser.parse_args()
    
    print(f"Loading band powers from: {args.band_powers}")
    band_powers_df = load_band_powers(args.band_powers)
    print(f"  Loaded {len(band_powers_df)} rows")
    
    print(f"Loading behavioral metrics from: {args.behavioral}")
    behavioral_df = load_behavioral_metrics(args.behavioral)
    print(f"  Loaded {len(behavioral_df)} rows")
    
    print(f"Loading feasibility metadata from: {args.feasibility}")
    feasibility_df = load_feasibility_metadata(args.feasibility)
    print(f"  Loaded {len(feasibility_df)} rows")
    
    print("Computing relative power...")
    rel_power_df = compute_relative_power(band_powers_df)
    print(f"  Computed relative power for {len(rel_power_df)} rows")
    
    print("Aggregating across channels (global mean per participant)...")
    aggregated_df = aggregate_across_channels(rel_power_df)
    print(f"  Aggregated to {len(aggregated_df)} participants")
    
    print("Joining with behavioral metrics and filtering by feasibility gate...")
    final_df = join_features(aggregated_df, behavioral_df, feasibility_df)
    print(f"  Final dataset has {len(final_df)} participants after inner joins")
    
    if len(final_df) == 0:
        raise RuntimeError("No participants remain after joining. Check feasibility and data availability.")
    
    # Ensure output directory exists
    output_path = Path(args.output)
    ensure_dirs(output_path.parent)
    
    # Write output
    print(f"Writing output to: {args.output}")
    final_df.to_csv(args.output, index=False)
    
    # Verify output
    output_df = pd.read_csv(args.output)
    expected_cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 'alpha_rel', 
                     'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    if list(output_df.columns) != expected_cols:
        raise ValueError(f"Output columns mismatch. Expected: {expected_cols}, Got: {list(output_df.columns)}")
    
    print("Success! Features file written.")
    print(f"  Columns: {list(output_df.columns)}")
    print(f"  Participants: {len(output_df)}")

if __name__ == "__main__":
    main()
