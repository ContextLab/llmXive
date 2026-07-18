import os
import sys
import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def load_subset_size():
    """Load the unified subset size from split_config.json."""
    config_path = project_root / "data" / "split_config.json"
    if not config_path.exists():
        raise FileNotFoundError("split_config.json not found. Run T019 first.")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config["n_unified"]

def create_train_test_split():
    """Create train/test split from final features."""
    final_features_path = project_root / "data" / "processed" / "final_features.parquet"
    if not final_features_path.exists():
        raise FileNotFoundError("final_features.parquet not found. Run T018 first.")
    
    df = pd.read_parquet(final_features_path)
    
    # Downsample if necessary
    n_subset = load_subset_size()
    if len(df) > n_subset:
        df = df.sample(n=n_subset, random_state=42)
    
    # Split
    train, test = train_test_split(df, test_size=0.2, random_state=42)
    
    # Save splits
    data_dir = project_root / "data" / "final"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    train.to_parquet(data_dir / "train_set.parquet")
    test.to_parquet(data_dir / "test_set.parquet")
    
    return train, test

if __name__ == "__main__":
    create_train_test_split()
