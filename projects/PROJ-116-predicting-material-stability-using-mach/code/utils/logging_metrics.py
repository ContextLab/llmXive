"""
Logging utilities for dataset and training metrics.
Implements T017: Add logging for dataset size, feature count, and training metrics.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import OUTPUTS_LOGS_DIR
from utils.logging import setup_logger


def log_dataset_metrics(
    logger_name: str,
    dataset_size: int,
    feature_count: int,
    source: str = "unknown",
    filter_criteria: Optional[str] = None
) -> None:
    """
    Log dataset statistics including size and feature dimensions.

    Args:
        logger_name: Name of the logger instance to use.
        dataset_size: Total number of entries in the dataset.
        feature_count: Number of features in the feature matrix.
        source: Source of the data (e.g., 'OQMD', 'filtered').
        filter_criteria: Optional description of filters applied.
    """
    logger = setup_logger(logger_name)

    log_msg = (
        f"Dataset Metrics | Source: {source} | "
        f"Size: {dataset_size} entries | Features: {feature_count}"
    )

    if filter_criteria:
        log_msg += f" | Filter: {filter_criteria}"

    logger.info(log_msg)

    # Also write a structured JSON record for programmatic consumption
    log_file_path = OUTPUTS_LOGS_DIR / "dataset_metrics.json"

    try:
        # Load existing records if file exists
        if log_file_path.exists():
            with open(log_file_path, "r") as f:
                records = json.load(f)
        else:
            records = []

        record = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "dataset_size": dataset_size,
            "feature_count": feature_count,
            "filter_criteria": filter_criteria
        }
        records.append(record)

        with open(log_file_path, "w") as f:
            json.dump(records, f, indent=2)

    except Exception as e:
        logger.warning(f"Failed to write structured dataset metrics to JSON: {e}")


def log_training_metrics(
    logger_name: str,
    model_name: str,
    metrics: Dict[str, Any],
    hyperparameters: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log training performance metrics and hyperparameters.

    Args:
        logger_name: Name of the logger instance to use.
        model_name: Identifier for the model (e.g., 'baseline', 'augmented').
        metrics: Dictionary of performance metrics (MAE, RMSE, R2, etc.).
        hyperparameters: Optional dictionary of model hyperparameters used.
    """
    logger = setup_logger(logger_name)

    # Format metrics string
    metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
    log_msg = f"Training Metrics | Model: {model_name} | {metrics_str}"

    if hyperparameters:
        hp_str = ", ".join([f"{k}={v}" for k, v in list(hyperparameters.items())[:5]])
        log_msg += f" | HP: {hp_str}..."

    logger.info(log_msg)

    # Write structured JSON record
    log_file_path = OUTPUTS_LOGS_DIR / "training_metrics.json"

    try:
        if log_file_path.exists():
            with open(log_file_path, "r") as f:
                records = json.load(f)
        else:
            records = []

        record = {
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "metrics": metrics,
            "hyperparameters": hyperparameters
        }
        records.append(record)

        with open(log_file_path, "w") as f:
            json.dump(records, f, indent=2)

    except Exception as e:
        logger.warning(f"Failed to write structured training metrics to JSON: {e}")


def log_feature_engineering_summary(
    logger_name: str,
    input_size: int,
    output_size: int,
    features_added: list,
    skipped_entries: int = 0,
    imputed_entries: int = 0
) -> None:
    """
    Log summary of feature engineering process.

    Args:
        logger_name: Name of the logger instance to use.
        input_size: Number of entries before feature engineering.
        output_size: Number of entries after feature engineering.
        features_added: List of feature names added.
        skipped_entries: Count of entries skipped due to validation failures.
        imputed_entries: Count of entries with imputed values.
    """
    logger = setup_logger(logger_name)

    log_msg = (
        f"Feature Engineering Summary | Input: {input_size} | Output: {output_size} | "
        f"Features: {len(features_added)} | Skipped: {skipped_entries} | Imputed: {imputed_entries}"
    )

    logger.info(log_msg)

    # Write structured JSON record
    log_file_path = OUTPUTS_LOGS_DIR / "fe_summary.json"

    try:
        if log_file_path.exists():
            with open(log_file_path, "r") as f:
                records = json.load(f)
        else:
            records = []

        record = {
            "timestamp": datetime.now().isoformat(),
            "input_size": input_size,
            "output_size": output_size,
            "features_added": features_added,
            "skipped_entries": skipped_entries,
            "imputed_entries": imputed_entries
        }
        records.append(record)

        with open(log_file_path, "w") as f:
            json.dump(records, f, indent=2)

    except Exception as e:
        logger.warning(f"Failed to write structured FE summary to JSON: {e}")
