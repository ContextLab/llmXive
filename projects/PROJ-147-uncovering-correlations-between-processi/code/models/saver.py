import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

from code.config import ensure_dirs
from code.utils.logging import get_logger

logger = get_logger(__name__)


def save_predictions(predictions_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the main predictions DataFrame to CSV.

    Args:
        predictions_df: DataFrame containing predictions.
        output_path: Full path to the output CSV file.
    """
    ensure_dirs(output_path)
    logger.info(f"Saving predictions to {output_path}")
    predictions_df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(predictions_df)} predictions to {output_path}")


def save_new_predictions(predictions_df: pd.DataFrame, output_path: str) -> None:
    """
    Save new predictions (for unseen samples) to CSV.

    Args:
        predictions_df: DataFrame containing new predictions.
        output_path: Full path to the output CSV file.
    """
    ensure_dirs(output_path)
    logger.info(f"Saving new predictions to {output_path}")
    predictions_df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(predictions_df)} new predictions to {output_path}")


def save_pipeline_log(log_path: str, hyperparameters: Dict[str, Any], warnings: List[str]) -> None:
    """
    Save a summary of the pipeline execution, including hyperparameters and warnings,
    to a JSON log file. This satisfies FR-007 by capturing all warnings and hyper-params.

    Args:
        log_path: Full path to the output log file (e.g., 'data/pipeline.log').
        hyperparameters: Dictionary of hyperparameters used during training.
        warnings: List of warning messages captured during execution.
    """
    ensure_dirs(log_path)
    
    logger.info(f"Compiling pipeline log to {log_path}")
    
    log_data = {
        "status": "completed",
        "hyperparameters": hyperparameters,
        "warnings": warnings,
        "warning_count": len(warnings)
    }

    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        logger.info(f"Pipeline log successfully written to {log_path}")
    except Exception as e:
        logger.error(f"Failed to write pipeline log: {e}")
        raise


def save_model_artifact(model: Any, output_path: str) -> None:
    """
    Save the trained model to disk using joblib (standard for sklearn).

    Args:
        model: The trained model object.
        output_path: Full path to the output file.
    """
    import joblib
    ensure_dirs(output_path)
    logger.info(f"Saving model to {output_path}")
    joblib.dump(model, output_path)
    logger.info(f"Model successfully saved to {output_path}")