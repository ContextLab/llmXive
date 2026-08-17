"""
Preprocessing module for regression datasets.

Handles missing value imputation, train-test splitting with fixed seeds,
and target variable validation.
"""
import logging
from typing import Tuple, Optional, Dict, Any, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer

from utils.logging import get_logger

logger = get_logger(__name__)


def validate_target(
    target: pd.Series,
    min_samples: int = 10,
    min_variance: float = 1e-6
) -> Dict[str, Any]:
    """
    Validate the target variable for regression tasks.

    Checks:
      1. No NaN values remaining
      2. Minimum number of samples
      3. Non-zero variance (to avoid constant targets)

    Args:
        target: The target variable series.
        min_samples: Minimum required samples.
        min_variance: Minimum required variance.

    Returns:
        Dictionary with validation status and details.

    Raises:
        ValueError: If validation fails.
    """
    issues = []

    if target.isna().any():
        issues.append(f"Target contains {target.isna().sum()} missing values.")

    if len(target) < min_samples:
        issues.append(f"Target has {len(target)} samples, minimum is {min_samples}.")

    var = target.var()
    if var < min_variance:
        issues.append(f"Target variance is {var:.6e}, minimum is {min_variance}.")

    if issues:
        error_msg = "Target validation failed:\n" + "\n".join(f"  - {i}" for i in issues)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(
        "Target validation passed",
        extra={
            "n_samples": len(target),
            "variance": float(var),
            "dtype": str(target.dtype)
        }
    )
    return {
        "valid": True,
        "n_samples": len(target),
        "variance": float(var),
        "dtype": str(target.dtype)
    }


def handle_missing_values(
    X: pd.DataFrame,
    y: Optional[pd.Series] = None,
    strategy: str = "mean",
    impute_y: bool = False
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Handle missing values in features and optionally in the target.

    Args:
        X: Feature DataFrame.
        y: Target Series (optional).
        strategy: Imputation strategy ('mean', 'median', 'most_frequent', 'constant').
        impute_y: Whether to impute missing values in y (drops rows if False).

    Returns:
        Tuple of (cleaned X, cleaned y).

    Raises:
        ValueError: If y has missing values and impute_y is False.
    """
    logger.info("Handling missing values", extra={"strategy": strategy, "impute_y": impute_y})

    # Handle features
    if X.isna().any().any():
        n_missing = X.isna().sum().sum()
        logger.info(f"Found {n_missing} missing values in features")

        imputer = SimpleImputer(strategy=strategy)
        X_imputed = pd.DataFrame(
            imputer.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        logger.info("Features imputed successfully")
    else:
        X_imputed = X

    # Handle target
    if y is not None:
        if y.isna().any():
            if not impute_y:
                # Drop rows where target is missing
                mask = ~y.isna()
                y_clean = y[mask].reset_index(drop=True)
                X_imputed = X_imputed[mask].reset_index(drop=True)
                logger.info(f"Dropped {mask.sum() - len(y)} rows with missing target values")
            else:
                # Impute target
                y_imputer = SimpleImputer(strategy=strategy)
                y_clean = pd.Series(
                    y_imputer.fit_transform(y.values.reshape(-1, 1)).flatten(),
                    index=y.index,
                    name=y.name
                )
                logger.info("Target imputed successfully")
        else:
            y_clean = y
    else:
        y_clean = None

    return X_imputed, y_clean


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train and test sets.

    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Proportion of data for test set.
        random_state: Seed for reproducibility.
        stratify: Whether to stratify (only meaningful for classification,
                  ignored for regression but kept for API consistency).

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    logger.info(
        "Splitting data",
        extra={
            "test_size": test_size,
            "random_state": random_state,
            "total_samples": len(X)
        }
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y if stratify else None
    )

    # Reset indices for clean dataframes
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    logger.info(
        "Data split complete",
        extra={
            "train_size": len(X_train),
            "test_size": len(X_test),
            "train_ratio": len(X_train) / len(X)
        }
    )

    return X_train, X_test, y_train, y_test


def preprocess_dataset(
    data: Dict[str, Any],
    test_size: float = 0.2,
    random_state: int = 42,
    impute_strategy: str = "mean",
    target_min_variance: float = 1e-6,
    target_min_samples: int = 10
) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for a regression dataset.

    Steps:
      1. Handle missing values in features and target.
      2. Validate target variable.
      3. Split into train and test sets.

    Args:
        data: Dictionary from loader with keys:
              - 'X': Feature DataFrame
              - 'y': Target Series
              - 'name': Dataset name (for logging)
        test_size: Proportion for test set.
        random_state: Seed for splitting.
        impute_strategy: Strategy for imputation.
        target_min_variance: Minimum variance for target validation.
        target_min_samples: Minimum samples for target validation.

    Returns:
        Dictionary with keys:
          - 'X_train', 'X_test': Feature splits
          - 'y_train', 'y_test': Target splits
          - 'metadata': Preprocessing metadata
    """
    dataset_name = data.get("name", "unknown")
    logger.info(f"Starting preprocessing for dataset: {dataset_name}")

    X = data["X"]
    y = data["y"]

    # Step 1: Handle missing values
    X_clean, y_clean = handle_missing_values(
        X, y, strategy=impute_strategy, impute_y=False
    )

    # Step 2: Validate target
    validation_info = validate_target(
        y_clean,
        min_samples=target_min_samples,
        min_variance=target_min_variance
    )

    # Step 3: Split data
    X_train, X_test, y_train, y_test = split_data(
        X_clean, y_clean, test_size=test_size, random_state=random_state
    )

    result = {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "metadata": {
            "dataset_name": dataset_name,
            "original_size": len(data["X"]),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "test_ratio": len(X_test) / len(data["X"]),
            "random_state": random_state,
            "impute_strategy": impute_strategy,
            "validation": validation_info
        }
    }

    logger.info(
        f"Preprocessing complete for {dataset_name}",
        extra={
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }
    )

    return result
