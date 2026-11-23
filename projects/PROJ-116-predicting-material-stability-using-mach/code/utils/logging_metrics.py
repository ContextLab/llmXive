import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import OUTPUTS_LOGS_DIR
from utils.logging import setup_logger

def log_dataset_metrics(
    dataset_name: str,
    total_entries: int,
    valid_entries: int,
    skipped_entries: int,
    feature_columns: Optional[list] = None,
    target_column: str = "formation_energy_per_atom",
) -> Dict[str, Any]:
    """
    Logs dataset size and composition metrics.

    Args:
        dataset_name: Name of the dataset being processed.
        total_entries: Total number of raw entries.
        valid_entries: Number of entries that passed validation.
        skipped_entries: Number of entries skipped due to validation failures.
        feature_columns: List of feature column names if available.
        target_column: Name of the target variable.

    Returns:
        Dictionary containing the logged metrics.
    """
    logger = setup_logger("dataset_metrics")

    timestamp = datetime.now().isoformat()
    metrics = {
        "timestamp": timestamp,
        "dataset_name": dataset_name,
        "total_entries": total_entries,
        "valid_entries": valid_entries,
        "skipped_entries": skipped_entries,
        "validity_rate": valid_entries / total_entries if total_entries > 0 else 0.0,
        "feature_count": len(feature_columns) if feature_columns else 0,
        "target_column": target_column,
    }

    logger.info(
        f"Dataset '{dataset_name}': {total_entries} total, "
        f"{valid_entries} valid, {skipped_entries} skipped. "
        f"Features: {metrics['feature_count']}"
    )

    # Ensure log directory exists
    OUTPUTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = OUTPUTS_LOGS_DIR / "dataset_metrics.json"

    # Append to existing log file or create new one
    all_metrics = []
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                all_metrics = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_metrics = []

    all_metrics.append(metrics)

    with open(log_file, "w") as f:
        json.dump(all_metrics, f, indent=2)

    return metrics

def log_training_metrics(
    model_name: str,
    training_samples: int,
    validation_samples: int,
    test_samples: int,
    best_params: Dict[str, Any],
    validation_scores: Dict[str, float],
    test_scores: Optional[Dict[str, float]] = None,
    runtime_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Logs training metrics including split sizes, hyperparameters, and scores.

    Args:
        model_name: Name of the model being trained.
        training_samples: Number of samples in training set.
        validation_samples: Number of samples in validation set.
        test_samples: Number of samples in test set.
        best_params: Best hyperparameters found during tuning.
        validation_scores: Scores on validation set.
        test_scores: Optional scores on test set.
        runtime_seconds: Optional total training runtime.

    Returns:
        Dictionary containing the logged metrics.
    """
    logger = setup_logger("training_metrics")

    timestamp = datetime.now().isoformat()
    metrics = {
        "timestamp": timestamp,
        "model_name": model_name,
        "dataset_splits": {
            "train": training_samples,
            "validation": validation_samples,
            "test": test_samples,
        },
        "best_params": best_params,
        "validation_scores": validation_scores,
        "test_scores": test_scores,
        "runtime_seconds": runtime_seconds,
    }

    logger.info(
        f"Model '{model_name}': Train={training_samples}, "
        f"Val={validation_samples}, Test={test_samples}. "
        f"Best params: {best_params}"
    )

    if test_scores:
        logger.info(f"Test scores: {test_scores}")

    if runtime_seconds:
        logger.info(f"Training runtime: {runtime_seconds:.2f} seconds")

    # Ensure log directory exists
    OUTPUTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = OUTPUTS_LOGS_DIR / "training_metrics.json"

    # Append to existing log file or create new one
    all_metrics = []
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                all_metrics = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_metrics = []

    all_metrics.append(metrics)

    with open(log_file, "w") as f:
        json.dump(all_metrics, f, indent=2)

    return metrics

def log_feature_engineering_summary(
    stage_name: str,
    input_rows: int,
    output_rows: int,
    imputed_count: int,
    dropped_count: int,
    feature_names: Optional[list] = None,
    imputation_strategy: str = "median",
) -> Dict[str, Any]:
    """
    Logs feature engineering summary including imputation and dropping counts.

    Args:
        stage_name: Name of the feature engineering stage (e.g., 'Magpie', 'Voronoi').
        input_rows: Number of rows before feature engineering.
        output_rows: Number of rows after feature engineering.
        imputed_count: Number of values imputed.
        dropped_count: Number of rows dropped.
        feature_names: List of generated feature names.
        imputation_strategy: Strategy used for imputation.

    Returns:
        Dictionary containing the logged metrics.
    """
    logger = setup_logger("feature_engineering")

    timestamp = datetime.now().isoformat()
    metrics = {
        "timestamp": timestamp,
        "stage_name": stage_name,
        "input_rows": input_rows,
        "output_rows": output_rows,
        "rows_kept": input_rows - dropped_count,
        "imputed_count": imputed_count,
        "dropped_count": dropped_count,
        "imputation_strategy": imputation_strategy,
        "feature_count": len(feature_names) if feature_names else 0,
    }

    logger.info(
        f"Feature Engineering '{stage_name}': "
        f"Input={input_rows}, Output={output_rows}, "
        f"Imputed={imputed_count}, Dropped={dropped_count}"
    )

    if feature_names:
        logger.debug(f"Generated features: {feature_names}")

    # Ensure log directory exists
    OUTPUTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = OUTPUTS_LOGS_DIR / "feature_engineering_summary.json"

    # Append to existing log file or create new one
    all_metrics = []
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                all_metrics = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_metrics = []

    all_metrics.append(metrics)

    with open(log_file, "w") as f:
        json.dump(all_metrics, f, indent=2)

    return metrics
