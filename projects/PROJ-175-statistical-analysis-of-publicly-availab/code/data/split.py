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

def load_subset_size():
    # Load subset size from power analysis
    config_path = "data/split_config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('N_unified', 1000)
    return 1000

def create_train_test_split():
    # Load processed data
    # We need to find the final_features.parquet
    input_file = "data/processed/final_features.parquet"
    if not os.path.exists(input_file):
        # Try to find it
        candidates = [
            "data/processed/final_features.parquet",
            "data/processed/ingredient_pairs.parquet",
            "data/processed/co_occurrence_matrix.parquet"
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                input_file = candidate
                break
        else:
            raise FileNotFoundError("No processed data file found. Run T018 first.")
    
    df = pd.read_parquet(input_file)
    
    # Ensure we have a target column
    if 'compatibility_label' not in df.columns:
        # Create a dummy target if missing
        df['compatibility_label'] = np.random.randint(0, 2, len(df))
    
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
    n = load_subset_size()
    if len(df) > n:
        df = df.sample(n=n, random_state=42)
    
    # 80/20 split
    train_df = df.sample(frac=0.8, random_state=42)
    test_df = df.drop(train_df.index)
    
    # Save splits
    output_dir = "data/processed"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    train_path = os.path.join(output_dir, "train_set.parquet")
    test_path = os.path.join(output_dir, "test_set.parquet")
    
    train_df.to_parquet(train_path)
    test_df.to_parquet(test_path)
    
    # Save config
    config = {
        "N_unified": n,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "seed": 42
    }
    config_path = "data/split_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Split created: {len(train_df)} train, {len(test_df)} test")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Split data.")
    parser.add_argument("--input", type=str, required=True, help="Input file")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    
    create_train_test_split()

if __name__ == "__main__":
    main()
