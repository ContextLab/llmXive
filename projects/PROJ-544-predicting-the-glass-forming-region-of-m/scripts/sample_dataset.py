"""
Sample dataset for glass-forming alloy classification.

Performs stratified sampling to create a dataset suitable for model training
while respecting memory constraints (<= 7GB).
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
SAMPLES_DIR = DATA_DIR / "samples"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DERIVED_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
RANDOM_SEED = 42
MAX_MEMORY_GB = 7.0
# Approximate bytes per row (conservative estimate for CSV with numeric and string data)
# Assuming ~20 features + composition string + label + metadata ~ 500 bytes per row
BYTES_PER_ROW_ESTIMATE = 500 
MAX_ROWS = int((MAX_MEMORY_GB * 1024 * 1024 * 1024) / BYTES_PER_ROW_ESTIMATE)

def get_input_file_path():
    """
    Determines the input file path.
    Prefers data/derived/filtered_alloys.csv (from T018) if it exists,
    otherwise falls back to data/samples/synthetic_alloys.csv (from T005).
    """
    filtered_path = DERIVED_DIR / "filtered_alloys.csv"
    synthetic_path = SAMPLES_DIR / "synthetic_alloys.csv"
    
    if filtered_path.exists():
        logger.info(f"Using filtered dataset: {filtered_path}")
        return filtered_path
    elif synthetic_path.exists():
        logger.info(f"Using synthetic dataset: {synthetic_path}")
        return synthetic_path
    else:
        raise FileNotFoundError(
            "No input dataset found. Please run T005 (generate_synthetic_data.py) "
            "or T018 (filter_labels.py) first to create data/samples/synthetic_alloys.csv "
            "or data/derived/filtered_alloys.csv."
        )

def main():
    parser = argparse.ArgumentParser(
        description="Perform stratified sampling on alloy dataset."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input CSV. Defaults to derived/filtered_alloys.csv or samples/synthetic_alloys.csv."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="sample_dataset.csv",
        help="Output filename in data/samples/."
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to include in the test split (default: 0.2)."
    )
    parser.add_argument(
        "--target-rows",
        type=int,
        default=None,
        help="Target number of rows for the final dataset. If None, uses max memory limit."
    )
    
    args = parser.parse_args()

    # Determine input file
    input_path = Path(args.input) if args.input else get_input_file_path()
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading dataset from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    # Identify label column
    label_col = "phase_label"
    if label_col not in df.columns:
        # Fallback to common alternatives if exact name missing
        if "label" in df.columns:
            label_col = "label"
        elif "class" in df.columns:
            label_col = "class"
        else:
            logger.error(f"Could not find label column. Expected '{label_col}' or 'label'/'class'.")
            sys.exit(1)

    logger.info(f"Using '{label_col}' as the target label column.")

    # Calculate target rows
    target_rows = args.target_rows if args.target_rows else MAX_ROWS
    
    # Ensure we don't sample more than we have
    if target_rows >= len(df):
        logger.warning(f"Target rows ({target_rows}) >= dataset size ({len(df)}). Using full dataset.")
        sampled_df = df
        sampling_ratio = 1.0
    else:
        # Calculate ratio for stratified sampling
        # We want the final size to be target_rows
        # StratifiedShuffleSplit splits into train/test. 
        # If we want total rows = target_rows, and test_size = 0.2, then train = 0.8 * target_rows.
        # So we need to sample a fraction of the original such that:
        # original_size * sample_fraction = target_rows
        sample_fraction = target_rows / len(df)
        
        logger.info(f"Performing stratified sampling. Target rows: {target_rows}, Fraction: {sample_fraction:.4f}")

        sss = StratifiedShuffleSplit(
            n_splits=1, 
            test_size=args.test_size, 
            random_state=RANDOM_SEED
        )

        # We need to sample the whole dataset first to get train+test split of the target size
        # Strategy: 
        # 1. Calculate the split indices for the FULL dataset using a fraction that yields target_rows.
        #    Actually, StratifiedShuffleSplit splits the data provided.
        #    If we pass the whole DF, it splits into train/test of the WHOLE DF size.
        #    We want the OUTPUT (train + test) to be target_rows.
        #    So we need to sample a subset of the original DF of size `target_rows` first?
        #    No, that breaks stratification if we just take random rows.
        #    Correct approach: 
        #    We want to keep a fraction `f` of the data such that `len(df) * f = target_rows`.
        #    Then we split that subset.
        #    But StratifiedShuffleSplit splits the input.
        #    So we can set `test_size` relative to the subset?
        #    Let's just sample a subset of size `target_rows` using StratifiedShuffleSplit on the whole data?
        #    No, SSS splits into train/test. 
        #    If we set n_train = 0.8 * target_rows, n_test = 0.2 * target_rows.
        #    We can do:
        #    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        #    for train_idx, test_idx in sss.split(df, df[label_col]):
        #        subset = df.iloc[train_idx].append(df.iloc[test_idx])
        #        This gives us 100% of the data split into train/test.
        #    We need to downsample.
        #    
        #    Alternative: Use a two-step approach.
        #    1. Determine the number of samples to keep: `n_samples = target_rows`.
        #    2. Use `train_test_split` with `stratify` and `train_size`?
        #       `train_test_split` can return a single subset if we don't ask for both? No.
        #    3. Use `StratifiedShuffleSplit` but adjust the split?
        #    
        #    Let's use `train_test_split` from sklearn which is simpler for a single split.
        from sklearn.model_selection import train_test_split
        
        # We want the TOTAL kept data to be `target_rows`.
        # So we need to select `target_rows` rows from `df` preserving class ratios.
        # We can do this by splitting the whole dataset into train/test, but we only want a fraction of it.
        # Actually, we just want a stratified sample of size `target_rows`.
        # We can use `train_test_split` with `train_size` and `test_size`?
        # No, `train_test_split` splits the input into two parts.
        # If we set `train_size` to a fraction, it returns that fraction.
        # But we want a specific number of rows.
        # Let's calculate the fraction needed to get `target_rows`.
        # fraction = target_rows / len(df)
        # Then we can use `train_test_split` with `train_size=fraction`?
        # No, `train_test_split` splits into train and test. If we set `train_size=0.5`, we get 50% train, 50% test? No.
        # `train_size` is the number of samples in the train set.
        # If we want a single sample of size N, we can do:
        # train, test = train_test_split(df, train_size=N, stratify=df[label_col], random_state=42)
        # Then `train` will have N rows. `test` will have the rest.
        # This works perfectly.
        
        train, _ = train_test_split(
            df,
            train_size=target_rows,
            stratify=df[label_col],
            random_state=RANDOM_SEED
        )
        sampled_df = train
        sampling_ratio = len(sampled_df) / len(df)

    logger.info(f"Sampled {len(sampled_df)} rows (ratio: {sampling_ratio:.4f})")

    # Reset index
    sampled_df = sampled_df.reset_index(drop=True)

    # Save output
    output_path = SAMPLES_DIR / args.output
    logger.info(f"Writing sample dataset to {output_path}...")
    sampled_df.to_csv(output_path, index=False)

    # Write metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "output_file": str(output_path),
        "original_rows": len(df),
        "sampled_rows": len(sampled_df),
        "sampling_ratio": sampling_ratio,
        "random_seed": RANDOM_SEED,
        "test_size": args.test_size,
        "label_column": label_col,
        "memory_limit_gb": MAX_MEMORY_GB,
        "target_rows": target_rows
    }

    log_path = LOGS_DIR / "sampling_log.json"
    with open(log_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Sampling complete. Metadata written to {log_path}")
    logger.info(f"Output saved to {output_path}")

if __name__ == "__main__":
    main()
