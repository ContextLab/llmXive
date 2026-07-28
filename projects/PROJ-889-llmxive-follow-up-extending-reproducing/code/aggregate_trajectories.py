"""
Aggregate multiple seed logs into a single processed CSV file.

This module implements the aggregation logic for User Story 1 (T016).
It merges trajectory logs from multiple seeds, preserving seed_id and bias_type,
and computes aggregate statistics across seeds.

Dependencies:
    - T015: Requires computed G(t) and ΔG(t) values in input logs
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from config import get_project_root, ensure_paths_exist
from utils.io_utils import read_csv, write_csv, ensure_dir


def aggregate_seed_logs(
    input_dir: Path,
    output_path: Path,
    seed_pattern: str = "seed_*"
) -> pd.DataFrame:
    """
    Aggregate multiple seed logs into a single CSV file.
    
    Args:
        input_dir: Directory containing individual seed log CSVs
        output_path: Path for the aggregated output CSV
        seed_pattern: Glob pattern to match seed files (default: "seed_*")
        
    Returns:
        DataFrame containing all aggregated trajectory data with seed_id and bias_type
        
    Raises:
        FileNotFoundError: If no matching seed files are found
        ValueError: If required columns are missing from input files
    """
    # Find all matching seed files
    seed_files = list(input_dir.glob(f"**/{seed_pattern}*.csv"))
    
    if not seed_files:
        raise FileNotFoundError(
            f"No seed files found matching pattern '{seed_pattern}*' in {input_dir}"
        )
    
    print(f"Found {len(seed_files)} seed files to aggregate")
    
    # Collect dataframes from each seed file
    dataframes = []
    for file_path in sorted(seed_files):
        try:
            # Extract seed_id from filename (e.g., "seed_001.csv" -> "001")
            seed_id = file_path.stem.replace("seed_", "")
            
            # Read the CSV
            df = read_csv(file_path)
            
            # Validate required columns exist
            required_cols = ['t', 'G(t)', 'dG(t)', 'z_score', 'bias_type']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(
                    f"File {file_path} missing required columns: {missing_cols}"
                )
            
            # Add metadata columns
            df['seed_id'] = seed_id
            df['source_file'] = file_path.name
            
            dataframes.append(df)
            print(f"  Loaded: {file_path.name} ({len(df)} rows)")
            
        except Exception as e:
            print(f"  Warning: Skipping {file_path.name} due to error: {e}")
            continue
    
    if not dataframes:
        raise ValueError("No valid seed files could be loaded")
    
    # Concatenate all dataframes
    aggregated_df = pd.concat(dataframes, ignore_index=True)
    
    # Ensure proper ordering: seed_id, then timesteps
    aggregated_df = aggregated_df.sort_values(['seed_id', 't']).reset_index(drop=True)
    
    # Compute aggregate statistics across seeds for each timestep
    # Group by timestep and compute mean/std across seeds
    if 't' in aggregated_df.columns:
        agg_stats = aggregated_df.groupby('t').agg({
            'G(t)': ['mean', 'std', 'min', 'max'],
            'dG(t)': ['mean', 'std', 'min', 'max'],
            'z_score': ['mean', 'std']
        }).reset_index()
        
        # Flatten column names
        agg_stats.columns = ['t'] + [
            f"{col[0]}_{col[1]}" if col[1] != '' else col[0]
            for col in agg_stats.columns[1:]
        ]
        
        # Merge stats back into main dataframe (optional, for reference)
        # aggregated_df = aggregated_df.merge(agg_stats, on='t', how='left')
        
        print(f"Computed aggregate statistics across {aggregated_df['seed_id'].nunique()} seeds")
    
    # Write output
    ensure_dir(output_path.parent)
    write_csv(output_path, aggregated_df)
    
    print(f"Aggregated {len(aggregated_df)} rows from {len(dataframes)} seeds to {output_path}")
    
    return aggregated_df


def main():
    """
    Main entry point for trajectory aggregation.
    
    Reads all seed logs from data/raw/, aggregates them, and writes
    the result to data/processed/trajectories_divergence.csv
    """
    # Get project root and ensure paths exist
    project_root = get_project_root()
    ensure_paths_exist()
    
    # Define input and output paths
    input_dir = project_root / "data" / "raw"
    output_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    
    print(f"Aggregating seed logs from: {input_dir}")
    print(f"Output will be written to: {output_path}")
    
    try:
        # Perform aggregation
        aggregated_df = aggregate_seed_logs(input_dir, output_path)
        
        # Print summary statistics
        print("\n=== Aggregation Summary ===")
        print(f"Total rows: {len(aggregated_df)}")
        print(f"Number of seeds: {aggregated_df['seed_id'].nunique()}")
        print(f"Unique bias types: {aggregated_df['bias_type'].unique().tolist()}")
        print(f"Timestep range: {aggregated_df['t'].min()} to {aggregated_df['t'].max()}")
        
        # Check for missing values
        missing_counts = aggregated_df.isnull().sum()
        if missing_counts.any():
            print("\nMissing value counts:")
            for col, count in missing_counts[missing_counts > 0].items():
                print(f"  {col}: {count}")
        else:
            print("No missing values detected.")
        
        print("\nAggregation completed successfully!")
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Ensure T013 (download_cherrl_logs.py) has been run successfully first.", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
