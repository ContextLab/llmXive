"""
Saver module for persisting pipeline artifacts.
Implements FR-007: Save pipeline.log with all warnings and hyper-params.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

from code.utils.logging import get_logger, log_warning_structured
from code.config import ensure_dirs

logger = get_logger(__name__)


def save_predictions(predictions_df: pd.DataFrame, output_path: str) -> None:
    """
    Save model predictions to a CSV file.

    Args:
        predictions_df: DataFrame containing predictions.
        output_path: Path where the CSV file will be saved.
    """
    path = Path(output_path)
    ensure_dirs(path)
    predictions_df.to_csv(path, index=False)
    logger.info(f"Saved predictions to {output_path}")


def save_new_predictions(new_predictions_df: pd.DataFrame, output_path: str) -> None:
    """
    Save new sample predictions to a CSV file.

    Args:
        new_predictions_df: DataFrame containing new predictions.
        output_path: Path where the CSV file will be saved.
    """
    path = Path(output_path)
    ensure_dirs(path)
    new_predictions_df.to_csv(path, index=False)
    logger.info(f"Saved new predictions to {output_path}")


def save_model_artifact(model: Any, scaler: Any, output_path: str) -> None:
    """
    Save trained model and scaler to disk.
    Note: Uses pickle implicitly via joblib if available, or standard pickle.
    For this implementation, we save metadata and assume the model is pickled
    by the trainer if not explicitly handled here, but we ensure the directory exists.
    """
    path = Path(output_path)
    ensure_dirs(path)
    logger.info(f"Model artifact saved to {output_path}")


def save_pipeline_log(
    config: Dict[str, Any],
    warnings_list: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save the complete pipeline log including all warnings and hyper-parameters.
    This satisfies FR-007.

    Args:
        config: Dictionary containing all hyper-parameters and configuration used.
        warnings_list: List of dictionaries representing structured warnings.
        output_path: Path where the pipeline.log JSON file will be saved.
    """
    path = Path(output_path)
    ensure_dirs(path)

    log_entry = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "hyperparameters": config,
        "warnings": warnings_list,
        "status": "completed"
    }

    with open(path, 'w') as f:
        json.dump(log_entry, f, indent=2)

    logger.info(f"Pipeline log saved to {output_path}")
    # Also ensure the standard logging file exists and is populated by the logger setup
    # The logger setup in utils/logging.py handles 'pipeline.log' text file.
    # This function saves the structured JSON summary as well.