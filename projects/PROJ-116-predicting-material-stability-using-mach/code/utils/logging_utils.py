import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import OUTPUTS_LOGS_DIR, LOG_LEVEL
from utils.logging import setup_logger

def log_training_metrics(
    dataset_size: int,
    feature_count: int,
    training_metrics: Dict[str, Any],
    model_type: str = "baseline"
) -> Path:
    """
    Logs dataset statistics and training metrics to a JSON file in the logs directory.
    
    Args:
        dataset_size: Number of samples in the dataset.
        feature_count: Number of features used for training.
        training_metrics: Dictionary containing metrics like MAE, RMSE, R2, etc.
        model_type: Type of model (e.g., 'baseline', 'augmented').
        
    Returns:
        Path to the created log file.
    """
    logger = setup_logger("training_metrics")
    
    log_entry = {
        "model_type": model_type,
        "dataset_size": dataset_size,
        "feature_count": feature_count,
        "metrics": training_metrics,
        "timestamp": logging.Formatter("%Y-%m-%d %H:%M:%S").format(logging.LogRecord("", 0, "", 0, "", (), None))
    }
    
    # Ensure directory exists
    OUTPUTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file_path = OUTPUTS_LOGS_DIR / f"{model_type}_training_metrics.json"
    
    # Write to file
    with open(log_file_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
        
    logger.info(f"Logged training metrics for {model_type} model to {log_file_path}")
    return log_file_path
