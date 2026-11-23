import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from code.config import get_project_root, ensure_paths_exist
from code.utils.io_utils import read_csv, write_csv
from code.utils.math_utils import interpolate_missing_timesteps, safe_z_score, handle_nan
from code.ingestion import compute_divergence_gap, compute_derivative_and_zscore


def aggregate_seed_logs(
    processed_logs_dir: Path,
    output_path: Path,
    required_columns: List[str]
) -> pd.DataFrame:
    """
    Aggregate multiple seed logs into a single DataFrame.

    This function iterates over all CSV files in the `processed_logs_dir`,
    loads them, validates the presence of required columns, and concatenates
    them into a single DataFrame. It ensures `seed_id` and `bias_type` are preserved.

    Args:
        processed_logs_dir: Directory containing per-seed processed CSVs.
        output_path: Path where the aggregated CSV will be written.
        required_columns: List of column names that must be present in each input file.

    Returns:
        The aggregated DataFrame.
    """
    if not processed_logs_dir.exists():
        raise FileNotFoundError(f"Processed logs directory not found: {processed_logs_dir}")

    log_files = list(processed_logs_dir.glob("*.csv"))
    if not log_files:
        raise ValueError(f"No CSV files found in {processed_logs_dir}")

    dataframes = []
    for log_file in log_files:
        try:
            df = read_csv(log_file)
            
            # Validate required columns
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                raise ValueError(f"File {log_file.name} missing columns: {missing}")
            
            # Ensure seed_id is present (often derived from filename if not in content)
            if 'seed_id' not in df.columns:
                # Infer seed_id from filename if not present
                seed_name = log_file.stem
                df['seed_id'] = seed_name
            
            dataframes.append(df)
            print(f"Loaded {len(df)} rows from {log_file.name}")
        except Exception as e:
            print(f"Warning: Skipping {log_file.name} due to error: {e}")
            continue

    if not dataframes:
        raise RuntimeError("No valid dataframes were loaded for aggregation.")

    # Concatenate all dataframes
    aggregated_df = pd.concat(dataframes, ignore_index=True)

    # Sort by seed_id and timestep for consistency
    if 'timestep' in aggregated_df.columns:
        aggregated_df['timestep'] = pd.to_numeric(aggregated_df['timestep'], errors='coerce')
        aggregated_df = aggregated_df.sort_values(by=['seed_id', 'timestep']).reset_index(drop=True)
    else:
        aggregated_df = aggregated_df.sort_values(by=['seed_id']).reset_index(drop=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    write_csv(aggregated_df, output_path)
    print(f"Aggregated {len(aggregated_df)} rows into {output_path}")

    return aggregated_df


def main():
    """
    Main entry point for T016: Aggregate seed logs into trajectories_divergence.csv.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    output_file = processed_dir / "trajectories_divergence.csv"

    # Ensure paths exist
    ensure_paths_exist()

    # Define required columns based on T015 output and T016 schema
    # T015 produces: seed_id, bias_type, timestep, J_biased, J_unbiased, J_gold, G_t, dG_t
    required_cols = [
        'seed_id', 'bias_type', 'timestep', 
        'J_biased', 'J_unbiased', 'J_gold', 
        'G_t', 'dG_t'
    ]

    try:
        # The ingestion pipeline (T015) should have populated processed_dir with per-seed files
        # We aggregate them here.
        df = aggregate_seed_logs(processed_dir, output_file, required_cols)
        
        # Final validation
        if df.empty:
            raise RuntimeError("Aggregated dataframe is empty.")
        
        # Verify schema
        for col in required_cols:
            if col not in df.columns:
                raise RuntimeError(f"Final output missing required column: {col}")
        
        print("T016 Aggregation completed successfully.")
        return 0

    except Exception as e:
        print(f"T016 Aggregation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
