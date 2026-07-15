"""
Data Split Module.

Creates stratified train/test splits by ingredient frequency.
Reads the power analysis results to determine the subset size N if provided,
otherwise processes the full input file.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Add parent to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"

def load_subset_size(logistic_path: Path, bayesian_path: Path) -> int:
    """
    Load the subset size N from the power analysis results.
    Prefers the Bayesian size if both exist, otherwise falls back to Logistic.
    Raises FileNotFoundError if neither exists.
    """
    n_logistic = None
    n_bayesian = None

    if logistic_path.exists():
        with open(logistic_path, 'r') as f:
            data = json.load(f)
            n_logistic = data.get('required_sample_size')
    
    if bayesian_path.exists():
        with open(bayesian_path, 'r') as f:
            data = json.load(f)
            n_bayesian = data.get('required_sample_size')

    # Prefer Bayesian for overall model fitting if available, else Logistic
    if n_bayesian is not None:
        return n_bayesian
    if n_logistic is not None:
        return n_logistic
    
    raise FileNotFoundError(
        f"Could not find subset size N. Expected either {logistic_path} or {bayesian_path}."
    )

def create_train_test_split(input_path: Path, subset_size: int = None):
    """
    Create stratified train/test splits ensuring stratified sampling by ingredient frequency.
    
    Args:
        input_path: Path to the input CSV (e.g., cooccurrence_features.csv)
        subset_size: Optional integer to downsample the dataset to this size
                     before splitting, as determined by power analysis (T008a/T008b).
    
    Returns:
        bool: True if successful.
    
    Raises:
        FileNotFoundError: If input file or power analysis files are missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} not found.")
    
    # Determine N from power analysis if not explicitly passed
    if subset_size is None:
        logistic_path = DATA_DIR / "power_analysis_logistic.json"
        bayesian_path = DATA_DIR / "power_analysis_bayesian.json"
        subset_size = load_subset_size(logistic_path, bayesian_path)
    
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    original_len = len(df)
    
    # Downsample if requested and data is larger than N
    if subset_size and len(df) > subset_size:
        print(f"Downsampling from {len(df)} to {subset_size} samples based on power analysis.")
        # Randomly sample to ensure reproducibility
        df = df.sample(n=subset_size, random_state=42).reset_index(drop=True)
    elif subset_size and len(df) < subset_size:
        print(f"Warning: Dataset size ({len(df)}) is smaller than required sample size ({subset_size}). Proceeding with available data.")
    
    # Calculate frequency for stratification
    # Frequency = count of ingredient_a occurrences
    freq = df['ingredient_a'].value_counts()
    df['frequency_bin'] = df['ingredient_a'].map(freq)
    
    # Ensure we have enough samples per bin for stratification
    # If a bin has fewer than 2 samples (1 train, 1 test), stratify will fail
    min_samples_per_bin = 2
    valid_bins = freq[freq >= min_samples_per_bin].index
    if len(valid_bins) < len(freq):
        print(f"Warning: {len(freq) - len(valid_bins)} frequency bins have fewer than {min_samples_per_bin} samples. Removing them from stratification.")
        # Filter to only valid bins for stratification logic, or fallback
        # We will try stratify first on the full set. If it fails due to small bins, we fallback.
    
    try:
        train, test = train_test_split(
            df, 
            test_size=0.2, 
            random_state=42, 
            stratify=df['frequency_bin']
        )
    except ValueError as e:
        # If stratification fails due to small bins, fallback to random split
        print(f"Stratification failed ({e}), falling back to random split.")
        train, test = train_test_split(
            df, 
            test_size=0.2, 
            random_state=42
        )
    
    # Drop the helper column
    train = train.drop(columns=['frequency_bin'])
    test = test.drop(columns=['frequency_bin'])
    
    # Save splits
    train_path = PROCESSED_DIR / "train_split.csv"
    test_path = PROCESSED_DIR / "test_split.csv"
    
    # Ensure directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)
    
    print(f"Train split saved to {train_path} ({len(train)} rows)")
    print(f"Test split saved to {test_path} ({len(test)} rows)")
    
    return True

if __name__ == "__main__":
    # Example usage
    input_file = FINAL_DIR / "cooccurrence_features.csv"
    if input_file.exists():
        create_train_test_split(input_file)
    else:
        print(f"Input file {input_file} not found. Run preprocessing first.")