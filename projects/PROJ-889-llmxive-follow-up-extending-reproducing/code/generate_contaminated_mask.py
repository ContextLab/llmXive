"""
T025b: Generate `is_contaminated` mask for User Story 2.

This script reads the output of T025a (contaminated segments) and the
aggregated divergence data from T016. It creates a boolean column
`is_contaminated` in the DataFrame, marking all timesteps belonging to
contaminated segments as True, and False otherwise.

Dependency:
    - T025a: Must have produced `data/processed/contaminated_segments.csv`
    - T016: Must have produced `data/processed/trajectories_divergence.csv`
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

from code.config import get_project_root
from code.utils.io_utils import read_csv, write_csv


def load_contaminated_segments(filepath: Path) -> pd.DataFrame:
    """
    Load the contaminated segments identified in T025a.
    Expected columns: seed_id, bias_type, start_timestep, end_timestep
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"Contaminated segments file not found: {filepath}. "
            "Ensure T025a has been run successfully."
        )
    return read_csv(filepath)


def generate_is_contaminated_mask(
    trajectories_df: pd.DataFrame,
    segments_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create a boolean column `is_contaminated` in the trajectories DataFrame.

    Logic:
    1. Initialize `is_contaminated` to False for all rows.
    2. For each segment in segments_df:
       - Filter trajectories_df for matching seed_id and bias_type.
       - Mark rows where timestep is within [start_timestep, end_timestep] as True.
    3. Return the updated DataFrame.
    """
    # Initialize mask
    trajectories_df = trajectories_df.copy()
    trajectories_df['is_contaminated'] = False

    # Apply masks based on segments
    for _, segment in segments_df.iterrows():
        seed_id = segment['seed_id']
        bias_type = segment['bias_type']
        start_ts = int(segment['start_timestep'])
        end_ts = int(segment['end_timestep'])

        mask = (
            (trajectories_df['seed_id'] == seed_id) &
            (trajectories_df['bias_type'] == bias_type) &
            (trajectories_df['timestep'] >= start_ts) &
            (trajectories_df['timestep'] <= end_ts)
        )
        trajectories_df.loc[mask, 'is_contaminated'] = True

    return trajectories_df


def main():
    """Main entry point for T025b."""
    root = get_project_root()
    input_divergence_path = root / "data" / "processed" / "trajectories_divergence.csv"
    input_segments_path = root / "data" / "processed" / "contaminated_segments.csv"
    output_path = root / "data" / "processed" / "trajectories_divergence_masked.csv"

    print(f"Loading divergence data from {input_divergence_path}...")
    try:
        trajectories_df = read_csv(input_divergence_path)
    except Exception as e:
        print(f"ERROR: Failed to load divergence data: {e}")
        sys.exit(1)

    print(f"Loading contaminated segments from {input_segments_path}...")
    try:
        segments_df = load_contaminated_segments(input_segments_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Generating `is_contaminated` mask...")
    masked_df = generate_is_contaminated_mask(trajectories_df, segments_df)

    print(f"Writing output to {output_path}...")
    write_csv(masked_df, output_path)

    # Summary
    contaminated_count = masked_df['is_contaminated'].sum()
    total_count = len(masked_df)
    print(f"Done. Total rows: {total_count}, Contaminated rows: {contaminated_count} "
          f"({100 * contaminated_count / total_count:.2f}%)")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()