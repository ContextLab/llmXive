"""
Failure handling logic for inference pipeline.

Handles inference failures by logging errors and appending failure records
to the results CSV with status='failed', error_msg, and NaN scores.
"""
import os
import sys
import json
import traceback
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import from project utilities
from utils.logging import get_logger, log_error, log_exception
from utils.errors import ResourceLimitError, SyntheticFallbackForbiddenError

logger = get_logger(__name__)

RESULTS_CSV_PATH = Path("data/processed/inference_results.csv")

def append_failure_record(
    case_id: str,
    variant_type: str,
    model_id: str,
    error_msg: str,
    output_path: Optional[str] = None
) -> None:
    """
    Append a failure record to the inference results CSV.
    
    Args:
        case_id: The WBench case identifier
        variant_type: The variant type (low/medium/high entropy)
        model_id: The model identifier that failed
        error_msg: The error message describing the failure
        output_path: Path to the output video file (if any was partially created)
    """
    logger.error(f"Recording inference failure: case={case_id}, model={model_id}, error={error_msg}")
    
    # Create failure record
    record = {
        'case_id': case_id,
        'variant_type': variant_type,
        'model_id': model_id,
        'status': 'failed',
        'error_msg': error_msg,
        'output_path': output_path if output_path else '',
        'physics_score': np.nan,
        'consistency_score': np.nan,
        'motion_artifact_score': np.nan,
        'ram_usage_gb': np.nan,
        'duration_seconds': np.nan
    }
    
    # Ensure output directory exists
    RESULTS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data or create new DataFrame
    if RESULTS_CSV_PATH.exists():
        df = pd.read_csv(RESULTS_CSV_PATH)
    else:
        df = pd.DataFrame()
    
    # Append new record
    new_df = pd.DataFrame([record])
    df = pd.concat([df, new_df], ignore_index=True)
    
    # Save updated DataFrame
    df.to_csv(RESULTS_CSV_PATH, index=False)
    logger.info(f"Failure record appended to {RESULTS_CSV_PATH}")

def handle_inference_failure(
    case_id: str,
    variant_type: str,
    model_id: str,
    exception: Exception,
    output_path: Optional[str] = None
) -> None:
    """
    Handle an inference failure by logging and recording it.
    
    This function:
    1. Logs the exception with full traceback
    2. Extracts a meaningful error message
    3. Appends a failure record to the results CSV
    
    Args:
        case_id: The WBench case identifier
        variant_type: The variant type (low/medium/high entropy)
        model_id: The model identifier that failed
        exception: The exception that was raised
        output_path: Path to the output video file (if any was partially created)
    """
    # Log the full exception
    log_exception(logger, exception, f"Inference failed for case {case_id}, model {model_id}")
    
    # Extract error message
    error_msg = str(exception)
    if isinstance(exception, ResourceLimitError):
        error_msg = f"Resource limit exceeded: {error_msg}"
    elif isinstance(exception, MemoryError):
        error_msg = "MemoryError: Insufficient RAM for inference"
    elif isinstance(exception, RuntimeError):
        error_msg = f"RuntimeError: {error_msg}"
    
    # Append failure record
    append_failure_record(
        case_id=case_id,
        variant_type=variant_type,
        model_id=model_id,
        error_msg=error_msg,
        output_path=output_path
    )

def main():
    """
    Main entry point for failure handler module.
    
    This is primarily used for testing the failure handling logic.
    """
    logger.info("Failure handler module loaded successfully")
    
    # Example usage for testing
    try:
        # Simulate a failure
        raise ResourceLimitError("Simulated OOM error for testing")
    except Exception as e:
        handle_inference_failure(
            case_id="test_case_001",
            variant_type="medium",
            model_id="test_model_v1",
            exception=e,
            output_path=None
        )
        logger.info("Test failure record created successfully")

if __name__ == "__main__":
    main()
