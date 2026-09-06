"""
Null Model Baseline Implementation.

Implements a robust null model baseline that predicts the mean of the target
variable for each fold, providing a baseline for comparison against trained models.
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/null_model.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
TRAINED_MODELS_DIR = DATA_DIR / "trained_models"
FOLDS_FILE = RESULTS_DIR / "folds.json"
OUTPUT_FILE = RESULTS_DIR / "null_model_fold_rmses.json"
TARGET_COLUMN = "langmuir_capacity"


def load_folds(folds_path: Path = FOLDS_FILE) -> Dict[str, Any]:
    """
    Load the fold indices from the folds.json file.

    Args:
        folds_path: Path to the folds.json file.

    Returns:
        Dictionary containing fold information with keys:
            - 'train_indices': List of lists of training indices for each fold
            - 'test_indices': List of lists of test indices for each fold
            - 'n_folds': Number of folds

    Raises:
        FileNotFoundError: If the folds file does not exist.
        ValueError: If the folds file is malformed.
    """
    if not folds_path.exists():
        raise FileNotFoundError(f"Folds file not found: {folds_path}")

    with open(folds_path, 'r') as f:
        folds_data = json.load(f)

    if 'train_indices' not in folds_data or 'test_indices' not in folds_data:
        raise ValueError(f"Malformed folds file: missing train_indices or test_indices")

    if 'n_folds' not in folds_data:
        folds_data['n_folds'] = len(folds_data['train_indices'])

    logger.info(f"Loaded {folds_data['n_folds']} folds from {folds_path}")
    return folds_data


def load_dataset(dataset_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the preprocessed dataset.

    Args:
        dataset_path: Path to the dataset. Defaults to data/processed/imputed_dataset.parquet.

    Returns:
        DataFrame containing the preprocessed dataset.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    if dataset_path is None:
        # Try multiple possible locations
        possible_paths = [
            PROCESSED_DIR / "imputed_dataset.parquet",
            PROCESSED_DIR / "target_filtered.parquet",
            PROCESSED_DIR / "final_dataset.parquet"
        ]
        for path in possible_paths:
            if path.exists():
                dataset_path = path
                break
        else:
            raise FileNotFoundError(
                f"No preprocessed dataset found. Expected one of: {possible_paths}"
            )

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_parquet(dataset_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")

    # Check for target column
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset. "
                       f"Available columns: {list(df.columns)}")

    # Remove rows with missing target values
    initial_count = len(df)
    df = df.dropna(subset=[TARGET_COLUMN])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with missing target values")

    return df


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Root Mean Squared Error.

    Args:
        y_true: True target values.
        y_pred: Predicted target values.

    Returns:
        RMSE value.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")

    if len(y_true) == 0:
        logger.warning("Empty arrays provided to RMSE calculation, returning 0.0")
        return 0.0

    mse = np.mean((y_true - y_pred) ** 2)
    rmse = np.sqrt(mse)
    return float(rmse)


def run_null_model_baseline(
    folds: Dict[str, Any],
    dataset: pd.DataFrame,
    target_column: str = TARGET_COLUMN
) -> List[Dict[str, Any]]:
    """
    Run the null model baseline for each fold.

    For each fold:
    1. Calculate the mean of the target variable in the training set.
    2. Predict this mean for all samples in the test set.
    3. Calculate RMSE between predictions and actual values.

    Args:
        folds: Dictionary containing fold indices.
        dataset: Preprocessed dataset.
        target_column: Name of the target column.

    Returns:
        List of dictionaries containing fold results:
            - fold: Fold number (0-indexed)
            - train_size: Number of samples in training set
            - test_size: Number of samples in test set
            - train_mean: Mean of target in training set
            - rmse: RMSE on test set
    """
    n_folds = folds['n_folds']
    train_indices_list = folds['train_indices']
    test_indices_list = folds['test_indices']

    if len(train_indices_list) != n_folds or len(test_indices_list) != n_folds:
        raise ValueError(f"Number of train/test index lists ({len(train_indices_list)}/{len(test_indices_list)}) "
                       f"does not match n_folds ({n_folds})")

    results = []

    for fold_idx in range(n_folds):
        logger.info(f"Processing fold {fold_idx + 1}/{n_folds}")

        train_indices = train_indices_list[fold_idx]
        test_indices = test_indices_list[fold_idx]

        # Extract training and test data
        y_train = dataset[target_column].iloc[train_indices].values
        y_test = dataset[target_column].iloc[test_indices].values

        if len(y_train) == 0:
            logger.warning(f"Fold {fold_idx} has empty training set, skipping")
            continue

        if len(y_test) == 0:
            logger.warning(f"Fold {fold_idx} has empty test set, skipping")
            continue

        # Null model: predict the mean of the training set
        train_mean = float(np.mean(y_train))
        y_pred = np.full(len(y_test), train_mean)

        # Calculate RMSE
        rmse = calculate_rmse(y_test, y_pred)

        fold_result = {
            "fold": fold_idx,
            "train_size": len(y_train),
            "test_size": len(y_test),
            "train_mean": train_mean,
            "rmse": rmse
        }

        results.append(fold_result)
        logger.info(f"Fold {fold_idx}: train_mean={train_mean:.4f}, test_rmse={rmse:.4f}")

    return results


def save_results(results: List[Dict[str, Any]], output_path: Path = OUTPUT_FILE) -> None:
    """
    Save the null model results to a JSON file.

    Args:
        results: List of fold result dictionaries.
        output_path: Path to the output JSON file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate summary statistics
    if results:
        rmse_values = [r['rmse'] for r in results]
        summary = {
            "n_folds": len(results),
            "mean_rmse": float(np.mean(rmse_values)),
            "std_rmse": float(np.std(rmse_values)),
            "min_rmse": float(np.min(rmse_values)),
            "max_rmse": float(np.max(rmse_values))
        }
    else:
        summary = {
            "n_folds": 0,
            "mean_rmse": None,
            "std_rmse": None,
            "min_rmse": None,
            "max_rmse": None
        }

    output_data = {
        "summary": summary,
        "fold_results": results
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Saved null model results to {output_path}")
    logger.info(f"Summary: mean_rmse={summary['mean_rmse']:.4f}, std_rmse={summary['std_rmse']:.4f}")


def main() -> None:
    """
    Main entry point for the null model baseline script.
    """
    logger.info("Starting null model baseline calculation")

    try:
        # Load folds
        folds = load_folds(FOLDS_FILE)

        # Load dataset
        dataset = load_dataset()

        # Run null model baseline
        results = run_null_model_baseline(folds, dataset)

        # Save results
        save_results(results, OUTPUT_FILE)

        logger.info("Null model baseline calculation completed successfully")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
