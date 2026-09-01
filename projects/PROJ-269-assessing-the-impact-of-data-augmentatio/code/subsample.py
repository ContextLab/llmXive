"""
Stratified subsampling module for small-sample statistical power analysis.

This module provides functions to create stratified subsamples of datasets
for N=15, 25, and 40. It includes logic for target column detection,
class balance validation, and logging of skipped configurations.
"""

import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for sample sizes
TARGET_SIZES: List[int] = [15, 25, 40]

def detect_target_column(df: pd.DataFrame) -> str:
    """
    Detect the target column in a DataFrame based on priority.

    Priority order: 'target', 'class', 'label', then the last column.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        str: The name of the detected target column.
    """
    priority_names = ['target', 'class', 'label']
    columns_lower = [c.lower() for c in df.columns]

    for name in priority_names:
        if name in columns_lower:
            # Return original case
            idx = columns_lower.index(name)
            return df.columns[idx]

    # Default to last column
    return df.columns[-1]

def validate_class_counts(
    df: pd.DataFrame,
    target_col: str,
    min_class_count: int = 5
) -> bool:
    """
    Validate that each class in the target column has sufficient counts.

    Args:
        df (pd.DataFrame): The input DataFrame.
        target_col (str): The name of the target column.
        min_class_count (int): Minimum required count per class.

    Returns:
        bool: True if all classes meet the minimum count, False otherwise.
    """
    value_counts = df[target_col].value_counts()
    return all(count >= min_class_count for count in value_counts)

def create_stratified_subsample(
    df: pd.DataFrame,
    target_col: str,
    n: int,
    random_state: int = 42
) -> Optional[pd.DataFrame]:
    """
    Create a stratified subsample of the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        target_col (str): The name of the target column.
        n (int): The total number of samples to draw.
        random_state (int): Random seed for reproducibility.

    Returns:
        Optional[pd.DataFrame]: The subsampled DataFrame, or None if
            stratification is not possible (e.g., class imbalance).
    """
    try:
        # Use sklearn's train_test_split for stratification if available
        # Otherwise, implement manual stratification
        from sklearn.model_selection import train_test_split

        # Calculate class proportions
        total = len(df)
        class_counts = df[target_col].value_counts()

        # Determine samples per class
        samples_per_class = {}
        for cls, count in class_counts.items():
            # Proportional allocation, ensuring at least 1 if possible
            # But strictly, we need to sum to n.
            # Simple proportional:
            prop = count / total
            samples = int(prop * n)
            if samples < 1 and count > 0:
                samples = 1
            samples_per_class[cls] = samples

        # Adjust for rounding errors to ensure sum == n
        current_sum = sum(samples_per_class.values())
        if current_sum != n:
            # Add or remove from the largest class to match n
            diff = n - current_sum
            largest_cls = class_counts.idxmax()
            samples_per_class[largest_cls] += diff

        # Validate if we have enough data for the requested split
        for cls, needed in samples_per_class.items():
            if df[target_col].value_counts()[cls] < needed:
                logger.warning(f"Not enough samples for class {cls} in stratified split.")
                return None

        # Perform split
        _, subsample = train_test_split(
            df,
            train_size=n,
            stratify=df[target_col],
            random_state=random_state
        )

        return subsample

    except ImportError:
        logger.error("scikit-learn is required for stratified subsampling.")
        return None
    except Exception as e:
        logger.error(f"Error creating stratified subsample: {e}")
        return None

def log_skipped_configuration(
    dataset: str,
    size: int,
    reason: str,
    log_path: Path,
    timestamp: Optional[str] = None
) -> None:
    """
    Log a skipped configuration to a JSON log file.

    Args:
        dataset (str): The name of the dataset.
        size (int): The requested sample size.
        reason (str): The reason for skipping.
        log_path (Path): The path to the log file.
        timestamp (Optional[str]): ISO format timestamp.
    """
    if timestamp is None:
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()

    record = {
        "dataset": dataset,
        "size": size,
        "reason": reason,
        "timestamp": timestamp
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    records = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Existing log file {log_path} is not valid JSON. Overwriting.")
            records = []

    records.append(record)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

def process_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    target_sizes: List[int] = TARGET_SIZES,
    log_path: Optional[Path] = None,
    random_state: int = 42
) -> Dict[int, pd.DataFrame]:
    """
    Process a dataset by generating stratified subsamples for target sizes.

    Args:
        df (pd.DataFrame): The input DataFrame.
        dataset_name (str): The name of the dataset.
        target_sizes (List[int]): List of sample sizes to generate.
        log_path (Optional[Path]): Path to the skipped configurations log.
        random_state (int): Random seed.

    Returns:
        Dict[int, pd.DataFrame]: A dictionary mapping sample size to the subsampled DataFrame.
    """
    if log_path is None:
        log_path = Path(__file__).parent.parent / "data" / "derived" / "skipped_configurations.json"

    target_col = detect_target_column(df)
    results = {}

    for n in target_sizes:
        if not validate_class_counts(df, target_col, min_class_count=5):
            reason = f"Class count < 5 for configuration N={n}"
            logger.warning(f"Skipping {dataset_name} (N={n}): {reason}")
            if log_path:
                log_skipped_configuration(dataset_name, n, reason, log_path)
            continue

        subsample = create_stratified_subsample(df, target_col, n, random_state)
        if subsample is None:
            reason = f"Stratification failed for N={n}"
            logger.warning(f"Skipping {dataset_name} (N={n}): {reason}")
            if log_path:
                log_skipped_configuration(dataset_name, n, reason, log_path)
            continue

        results[n] = subsample
        logger.info(f"Successfully created subsample for {dataset_name} (N={n})")

    return results

def main() -> None:
    """
    Main entry point for the subsampling script.

    Note: This script is typically called by the simulation pipeline.
    Direct execution is for testing purposes.
    """
    logger.info("Subsampling module ready.")
    # Example usage would require a dataset path
    # This is a placeholder for direct execution logic if needed

if __name__ == "__main__":
    main()
