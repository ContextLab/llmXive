"""
Identify contaminated windows based on FR-009.

Logic:
1. Read data/processed/trajectories_divergence.csv.
2. Identify contiguous segments where the duration of elevated G(t)
   (above global median) exceeds the sliding window size (W=20).
3. Store the indices of these segments in a DataFrame column 'is_contaminated'.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
import numpy as np

# Import project utilities
from config import get_project_root, DataConfig
from utils.io_utils import read_csv, write_csv


def identify_contaminated_segments(
    df: pd.DataFrame,
    window_size: int = 20,
    value_column: str = "G_t"
) -> pd.DataFrame:
    """
    Identify contiguous segments where G(t) > global_median for > window_size steps.

    Args:
        df: DataFrame containing trajectory data with 'seed_id', 'timestep', and 'G_t'.
        window_size: The minimum duration (W) to consider a segment contaminated.
        value_column: The column name for the divergence gap (default 'G_t').

    Returns:
        DataFrame with an added 'is_contaminated' boolean column.
    """
    # Calculate global median of G(t) across ALL seeds and timesteps
    global_median = df[value_column].median()

    # Initialize contamination mask
    df = df.copy()
    df["is_contaminated"] = False

    # Process each seed independently to ensure contiguous segments are per-seed
    # as per standard time-series contamination logic in this context.
    for seed_id in df["seed_id"].unique():
        mask = df["seed_id"] == seed_id
        seed_df = df.loc[mask]

        # Sort by timestep to ensure order
        seed_df = seed_df.sort_values("timestep")

        # Identify elevated points
        elevated = seed_df[value_column] > global_median

        # Find contiguous runs of True values
        # We use diff to find transitions
        diff = elevated.astype(int).diff()
        start_indices = diff[elevated.astype(int) == 1].index
        end_indices = diff[elevated.astype(int) == -1].index

        # Handle edge cases where a run starts at index 0 or ends at last index
        if elevated.iloc[0]:
            if len(start_indices) == 0 or start_indices[0] != elevated.index[0]:
                start_indices = pd.concat([pd.Series([elevated.index[0]]), start_indices])
        
        if elevated.iloc[-1]:
            if len(end_indices) == 0 or end_indices[-1] != elevated.index[-1]:
                end_indices = pd.concat([end_indices, pd.Series([elevated.index[-1]])])

        # Convert to lists for iteration
        start_list = start_indices.tolist()
        end_list = end_indices.tolist()

        # Pair starts and ends
        # If start and end lists are empty, no runs
        if not start_list:
            continue

        # Ensure we have matching pairs. If start exists but end is missing, 
        # it means the run goes to the end.
        runs = []
        for i, start_idx in enumerate(start_list):
            if i < len(end_list):
                end_idx = end_list[i]
            else:
                end_idx = seed_df.index[-1]
            
            # Calculate duration (number of timesteps)
            # Since index is not necessarily 0..N, we count rows
            duration = len(seed_df.loc[start_idx:end_idx])
            
            if duration > window_size:
                runs.append((start_idx, end_idx))

        # Mark contaminated rows in the main DataFrame
        for start_idx, end_idx in runs:
            df.loc[start_idx:end_idx, "is_contaminated"] = True

    return df


def main():
    """
    Main entry point for identifying contaminated windows.
    Reads trajectories_divergence.csv, computes mask, writes to 
    trajectories_divergence_contaminated.csv (or updates in place if needed, 
    but here we write a new file to preserve raw US1 output).
    
    Note: T025b expects this logic to produce the mask. 
    Per T025c, we update the dataframe. 
    To be safe and explicit, we write the result to a new file 
    that T022/T025b can consume, or update the existing one if the spec implies 
    overwriting. The task description says "Store the indices... in a temporary list 
    or DataFrame". T025b says "Create a boolean column... in the DataFrame".
    We will write the updated DataFrame to a new file: 
    data/processed/trajectories_divergence_contaminated.csv
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    print(f"Reading {input_path}...")
    df = read_csv(input_path)

    # Validate required columns
    required_cols = ["seed_id", "timestep", "G_t"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        sys.exit(1)

    print("Identifying contaminated windows (duration > 20 steps above global median)...")
    df_contaminated = identify_contaminated_segments(df, window_size=20, value_column="G_t")

    output_path = project_root / "data" / "processed" / "trajectories_divergence_contaminated.csv"
    print(f"Writing results to {output_path}...")
    write_csv(df_contaminated, output_path)

    # Summary stats
    total_rows = len(df_contaminated)
    contaminated_rows = df_contaminated["is_contaminated"].sum()
    print(f"Total rows: {total_rows}")
    print(f"Contaminated rows: {contaminated_rows} ({100*contaminated_rows/total_rows:.2f}%)")
    print("Task T025a completed successfully.")


if __name__ == "__main__":
    main()
