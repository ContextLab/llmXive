import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from config import LOGS_DIR, PROJECT_ROOT

def get_log_file_path() -> Path:
    """
    Get the path to the log file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"ingestion_{timestamp}.log"
    return LOGS_DIR / log_filename

def log_data_drop_counts(step_name: str, dropped_counts: Dict[str, int]):
    """
    Log the counts of dropped records for a specific step.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Data drop counts for {step_name}: {dropped_counts}")

def log_model_convergence(model_name: str, converged: bool, metrics: Optional[Dict[str, Any]] = None):
    """
    Log model convergence status and metrics.
    """
    logger = logging.getLogger(__name__)
    status = "Converged" if converged else "Did not converge"
    logger.info(f"Model {model_name} {status}")
    if metrics:
        logger.info(f"Metrics: {metrics}")

def log_processing_step(step_name: str, details: Dict[str, Any]):
    """
    Log details of a processing step.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing step: {step_name}")
    for key, value in details.items():
        logger.info(f"  {key}: {value}")
