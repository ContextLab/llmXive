"""
Aggregation module for merging multiple seed logs into a single processed dataset.

This module implements T016: Aggregation logic to merge multiple seed logs
into data/processed/trajectories_divergence.csv preserving seed_id and bias_type.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Import from existing project modules
from config import get_project_root, ensure_paths_exist
from utils.io_utils import read_csv, write_csv, ensure_dir
from utils.validator import validate_file_against_schema


def aggregate_seed_logs(
    input_dir: Path,
    output_file: Path,
    schema_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Aggregate multiple seed trajectory logs into a single processed CSV.
    
    Reads all CSV files from input_dir (one per seed), combines them,
    and writes the result to output_file. Preserves seed_id and bias_type.
    
    Args:
        input_dir: Directory containing seed log CSV files
        output_file: Path to write the aggregated CSV
        schema_path: Optional path to trajectory schema for validation
    
    Returns:
        DataFrame containing all aggregated trajectories
    
    Raises:
        FileNotFoundError: If input directory is empty or contains no CSV files
        ValueError: If required columns are missing from input files
    """
    input_dir = Path(input_dir)
    output_file = Path(output_file)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    # Find all CSV files in the input directory
    csv_files = list(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")
    
    # Expected columns from T014/T015 processing
    required_columns = {
        'seed_id', 'bias_type', 'timestep', 
        'J_biased', 'J_unbiased', 'J_gold',
        'G_t', 'dG_t'
    }
    
    dataframes = []
    
    for csv_file in csv_files:
        # Read the seed log
        df = read_csv(csv_file)
        
        # Validate required columns exist
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"File {csv_file.name} missing required columns: {missing_cols}"
            )
        
        # Ensure seed_id is preserved (might be in filename or column)
        if 'seed_id' not in df.columns:
            # Extract from filename if not in column
            seed_id = csv_file.stem
            df['seed_id'] = seed_id
        
        # Ensure bias_type is preserved
        if 'bias_type' not in df.columns:
            # Try to extract from filename or set a default
            # Assuming filename format: {seed_id}_{bias_type}.csv or similar
            parts = csv_file.stem.split('_')
            if len(parts) >= 2:
                df['bias_type'] = parts[-1]
            else:
                df['bias_type'] = 'unknown'
        
        # Ensure numeric types for calculations
        numeric_cols = ['timestep', 'J_biased', 'J_unbiased', 'J_gold', 'G_t', 'dG_t']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        dataframes.append(df)
    
    # Concatenate all dataframes
    if not dataframes:
        raise ValueError("No valid dataframes to aggregate")
    
    aggregated_df = pd.concat(dataframes, ignore_index=True)
    
    # Sort by seed_id, bias_type, and timestep for consistent ordering
    aggregated_df = aggregated_df.sort_values(
        by=['seed_id', 'bias_type', 'timestep']
    ).reset_index(drop=True)
    
    # Validate against schema if provided
    if schema_path and schema_path.exists():
        try:
            validate_file_against_schema(
                aggregated_df, 
                schema_path,
                schema_type='trajectory'
            )
        except Exception as e:
            # Log validation warning but continue
            print(f"Warning: Schema validation failed: {e}")
    
    # Ensure output directory exists
    ensure_dir(output_file.parent)
    
    # Write to CSV
    write_csv(aggregated_df, output_file)
    
    print(f"Aggregated {len(csv_files)} seed logs into {output_file}")
    print(f"Total rows: {len(aggregated_df)}")
    print(f"Unique seeds: {aggregated_df['seed_id'].nunique()}")
    print(f"Unique bias types: {aggregated_df['bias_type'].nunique()}")
    
    return aggregated_df


def main():
    """
    Main entry point for trajectory aggregation.
    
    Reads from data/raw/cherrl_logs/ (or configured input) and writes to
    data/processed/trajectories_divergence.csv.
    """
    project_root = get_project_root()
    
    # Default paths
    input_dir = project_root / "data" / "raw" / "cherrl_logs"
    output_file = project_root / "data" / "processed" / "trajectories_divergence.csv"
    schema_path = project_root / "contracts" / "trajectory.schema.yaml"
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    # Ensure paths exist
    ensure_paths_exist()
    
    try:
        # Perform aggregation
        df = aggregate_seed_logs(
            input_dir=input_dir,
            output_file=output_file,
            schema_path=schema_path
        )
        
        print("Aggregation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 2
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during aggregation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
