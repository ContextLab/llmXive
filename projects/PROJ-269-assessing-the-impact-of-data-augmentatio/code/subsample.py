import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for sample sizes
TARGET_SIZES = [15, 25, 40]
MIN_CLASS_COUNT = 5
SKIPPED_LOG_PATH = Path("data/derived/skipped_configurations.log")

def detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the target column based on priority: 'target', 'class', 'label', or last column.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Name of the target column.
    """
    priority_names = ['target', 'class', 'label']
    
    for name in priority_names:
        if name in df.columns:
            logger.info(f"Detected target column via priority name: '{name}'")
            return name
    
    # Default to the last column
    target_col = df.columns[-1]
    logger.info(f"No priority target found. Defaulting to last column: '{target_col}'")
    return target_col

def validate_class_counts(df: pd.DataFrame, target_col: str, n: int) -> Tuple[bool, Dict[str, int]]:
    """
    Validate that each class has at least MIN_CLASS_COUNT samples in the subsample.
    Since we are subsampling to 'n', we check if the distribution in the full set
    allows for a stratified sample of size 'n' where every class gets >= MIN_CLASS_COUNT.
    However, the strict requirement is usually about the resulting subsample.
    Here we check the full dataset first to see if it's even possible.
    
    Args:
        df: Full dataset.
        target_col: Target column name.
        n: Desired subsample size.
        
    Returns:
        Tuple of (is_valid, class_counts_in_full)
    """
    counts = df[target_col].value_counts()
    num_classes = len(counts)
    
    # To have at least MIN_CLASS_COUNT in a subsample of size n,
    # we need n >= num_classes * MIN_CLASS_COUNT.
    if n < num_classes * MIN_CLASS_COUNT:
        return False, counts.to_dict()
    
    # Also check if any class in the full dataset has fewer than MIN_CLASS_COUNT
    if any(counts < MIN_CLASS_COUNT):
        return False, counts.to_dict()
        
    return True, counts.to_dict()

def create_stratified_subsample(df: pd.DataFrame, target_col: str, n: int, seed: int = 42) -> pd.DataFrame:
    """
    Create a stratified subsample of size n.
    
    Args:
        df: Input DataFrame.
        target_col: Target column name.
        n: Desired subsample size.
        seed: Random seed for reproducibility.
        
    Returns:
        Stratified subsample DataFrame.
    """
    # Ensure the target column is treated as categorical for stratification
    # to avoid issues with numeric types if not already
    if not pd.api.types.is_categorical_dtype(df[target_col]):
        df[target_col] = df[target_col].astype('category')
    
    # Calculate the number of samples per class
    counts = df[target_col].value_counts()
    num_classes = len(counts)
    samples_per_class = n // num_classes
    
    # Check if we can get enough samples
    if any(counts < samples_per_class):
        # Fallback: use the minimum available if strict stratification fails,
        # but for this task, we assume validation happens before this or we handle it.
        # We will try to balance as best as possible.
        pass
    
    subsamples = []
    for class_label in df[target_col].unique():
        class_df = df[df[target_col] == class_label]
        # Determine how many to take. Ideally n/num_classes.
        # If a class is small, take all.
        take_count = min(samples_per_class, len(class_df))
        
        # If we need to adjust because of integer division remainder,
        # we can add 1 to some classes, but simple random is fine for now.
        # We'll stick to equal distribution for simplicity unless impossible.
        
        sampled = class_df.sample(n=take_count, random_state=seed)
        subsamples.append(sampled)
    
    result = pd.concat(subsamples, ignore_index=True)
    
    # If the total is not exactly n (due to class constraints), shuffle and take n
    if len(result) > n:
        result = result.sample(n=n, random_state=seed)
    
    logger.info(f"Created stratified subsample of size {len(result)}")
    return result

def log_skipped_configuration(dataset_name: str, size: int, reason: str):
    """
    Log a skipped configuration to the derived log file.
    
    Args:
        dataset_name: Name of the dataset.
        size: Attempted sample size.
        reason: Reason for skipping.
    """
    # Ensure the directory exists
    SKIPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    log_entry = f"[SKIPPED] Dataset: {dataset_name}, Size: {size}, Reason: {reason}\n"
    
    with open(SKIPPED_LOG_PATH, 'a') as f:
        f.write(log_entry)
    
    logger.warning(f"Skipped configuration: {dataset_name} (N={size}) - {reason}")

def process_dataset(dataset_path: Path, dataset_name: str, sizes: List[int] = TARGET_SIZES) -> List[Dict]:
    """
    Process a single dataset: detect target, validate, and create subsamples.
    
    Args:
        dataset_path: Path to the CSV file.
        dataset_name: Name identifier for the dataset.
        sizes: List of sample sizes to attempt.
        
    Returns:
        List of dictionaries containing metadata and paths for successful subsamples.
    """
    logger.info(f"Processing dataset: {dataset_name} at {dataset_path}")
    
    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        return []
    
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        logger.error(f"Failed to read dataset {dataset_path}: {e}")
        return []
    
    if df.empty:
        logger.warning(f"Dataset {dataset_name} is empty.")
        return []
    
    target_col = detect_target_column(df)
    results = []
    
    for n in sizes:
        # Validate if this configuration is possible
        is_valid, counts = validate_class_counts(df, target_col, n)
        
        if not is_valid:
            reason = f"Cannot stratify to N={n}. Classes: {dict(counts)}. Min required per class: {MIN_CLASS_COUNT}."
            log_skipped_configuration(dataset_name, n, reason)
            continue
        
        try:
            subsample = create_stratified_subsample(df, target_col, n)
            
            # Save the subsample
            output_dir = Path("data/derived")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filename = f"{dataset_name}_n{n}.csv"
            output_path = output_dir / output_filename
            
            subsample.to_csv(output_path, index=False)
            logger.info(f"Saved subsample to {output_path}")
            
            results.append({
                "dataset": dataset_name,
                "size": n,
                "target_column": target_col,
                "output_path": str(output_path),
                "row_count": len(subsample),
                "class_distribution": dict(subsample[target_col].value_counts())
            })
            
        except Exception as e:
            reason = f"Subsampling error: {str(e)}"
            log_skipped_configuration(dataset_name, n, reason)
            logger.error(f"Error creating subsample for {dataset_name} (N={n}): {e}")
            continue
    
    return results

def main():
    """
    Main entry point to process all datasets in data/raw/.
    """
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        logger.error("data/raw/ directory not found. Please run download_data.py first.")
        return
    
    dataset_files = list(raw_dir.glob("*.csv"))
    if not dataset_files:
        logger.warning("No CSV files found in data/raw/.")
        return
    
    all_results = []
    
    for file_path in dataset_files:
        # Derive dataset name from filename (remove extension)
        dataset_name = file_path.stem
        results = process_dataset(file_path, dataset_name)
        all_results.extend(results)
    
    # Save summary of all processed subsamples
    summary_path = Path("data/derived/subsample_summary.json")
    import json
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Subsampling complete. Summary saved to {summary_path}")
    logger.info(f"Skipped configurations logged to {SKIPPED_LOG_PATH}")

if __name__ == "__main__":
    main()
