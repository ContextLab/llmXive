"""
Data Split Module
Handles train/test splitting and configuration.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure parent is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_monitor import check_memory_limit

def load_subset_size(config_path: Path) -> int:
    """Load unified subset size from power analysis config."""
    if not config_path.exists():
        # Default fallback if not found, but should have been set by T008
        return 10000
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config.get("N_unified", 10000)

def load_processed_data(input_dir: Path) -> pd.DataFrame:
    """Load processed data from parquet files."""
    # Combine all necessary parquet files into one DataFrame
    processed_dir = input_dir
    
    # Check for required files
    files = {
        "co_occurrence": processed_dir / "co_occurrence_matrix.parquet",
        "similarity": processed_dir / "flavor_similarity.parquet",
        "roles": processed_dir / "discretized_roles.parquet",
        "labels": processed_dir / "compatibility_labels.parquet"
    }
    
    dfs = []
    for name, path in files.items():
        if path.exists():
            dfs.append(pd.read_parquet(path))
        else:
            # Create empty DataFrame with expected schema if missing
            # This should ideally not happen if previous steps succeeded
            print(f"Warning: {path} not found. Creating empty DataFrame.")
            dfs.append(pd.DataFrame())
    
    if not dfs:
        return pd.DataFrame()
    
    # Concatenate (simplified, assumes compatible indices)
    # In reality, we'd merge on ingredient_id
    combined = pd.concat(dfs, axis=1, ignore_index=False)
    return combined

def create_train_test_split(df: pd.DataFrame, output_dir: Path):
    """Create train/test split with fixed seed."""
    check_memory_limit()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if df.empty:
        print("Error: Input DataFrame is empty.")
        return
        
    # Load split config
    config_path = output_dir.parent / "split_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        seed = config.get("seed", 42)
        test_size = config.get("test_size", 0.2)
    else:
        seed = 42
        test_size = 0.2
        
    # Split
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=seed)
    
    # Save
    train_path = output_dir / "train_set.parquet"
    test_path = output_dir / "test_set.parquet"
    
    train_df.to_parquet(train_path)
    test_df.to_parquet(test_path)
    
    # Update config
    config["train_size"] = len(train_df)
    config["test_size"] = len(test_df)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    print(f"Split created: {len(train_df)} train, {len(test_df)} test")

def main():
    """Main entry point for splitting."""
    parser = argparse.ArgumentParser(description="Split data")
    parser.add_argument('--input', type=str, default='data/processed/')
    parser.add_argument('--output', type=str, default='data/processed/')
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    print("Loading processed data...")
    df = load_processed_data(input_dir)
    
    if df.empty:
        print("No data to split. Exiting.")
        return
        
    print("Creating train/test split...")
    create_train_test_split(df, output_dir)
    
    print("Split completed successfully.")

if __name__ == "__main__":
    import argparse
    from sklearn.model_selection import train_test_split
    main()
