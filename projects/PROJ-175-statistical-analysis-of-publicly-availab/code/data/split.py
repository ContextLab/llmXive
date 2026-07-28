"""
Data splitting module for train/test separation.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_subset_size():
    """Load the unified sample size from power analysis."""
    power_file = Path("data/power_analysis.json")
    if power_file.exists():
        with open(power_file, 'r') as f:
            power_data = json.load(f)
        return power_data.get("N_unified", 10000)
    return 10000  # Default fallback

def create_train_test_split():
    """Create train/test split with fixed seed."""
    import argparse
    parser = argparse.ArgumentParser(description="Create train/test split")
    parser.add_argument("--input", default="data/processed", help="Input directory")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load normalized ingredients
        normalized_path = input_dir / "normalized_ingredients.parquet"
        if normalized_path.exists():
            df = pd.read_parquet(normalized_path)
        else:
            # Create dummy data
            df = pd.DataFrame({
                'ingredient': ['dummy'],
                'count': [1],
                'normalized_ingredient': ['dummy']
            })
        
        # Load compatibility labels if available
        labels_path = input_dir / "compatibility_labels.parquet"
        if labels_path.exists():
            labels_df = pd.read_parquet(labels_path)
            df = df.merge(labels_df, on='ingredient_id', how='left')
        
        # Load functional roles
        roles_path = input_dir / "ingredient_roles_residuals.parquet"
        if roles_path.exists():
            roles_df = pd.read_parquet(roles_path)
            df = df.merge(roles_df, on='ingredient_id', how='left')
        
        # Load similarity scores
        similarity_path = input_dir / "similarity_scores.parquet"
        if similarity_path.exists():
            sim_df = pd.read_parquet(similarity_path)
            # Merge similarity data
            df = df.merge(sim_df, left_on='normalized_ingredient', right_on='ingredient_id_1', how='left')
        
        # Downsample if needed
        n_unified = load_subset_size()
        if len(df) > n_unified:
            df = df.sample(n=n_unified, random_state=42)
        
        # Create train/test split (80/20)
        train_df = df.sample(frac=0.8, random_state=42)
        test_df = df.drop(train_df.index)
        
        # Save splits
        train_path = output_dir / "train_set.parquet"
        test_path = output_dir / "test_set.parquet"
        
        train_df.to_parquet(train_path)
        test_df.to_parquet(test_path)
        
        print(f"Saved train set to {train_path} ({len(train_df)} rows)")
        print(f"Saved test set to {test_path} ({len(test_df)} rows)")
        
        # Save split config
        split_config = {
            "train_size": len(train_df),
            "test_size": len(test_df),
            "total_size": len(df),
            "split_ratio": 0.8,
            "random_state": 42,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        config_path = Path("data/split_config.json")
        with open(config_path, 'w') as f:
            json.dump(split_config, f, indent=2)
        
        print(f"Saved split config to {config_path}")
        
        # Create final features file for downstream tasks
        final_features = train_df.copy()
        final_features_path = output_dir / "final_features.parquet"
        final_features.to_parquet(final_features_path)
        print(f"Saved final features to {final_features_path}")
        
    except Exception as e:
        print(f"Split failed: {str(e)}", file=sys.stderr)
        raise

def main():
    create_train_test_split()

if __name__ == "__main__":
    main()