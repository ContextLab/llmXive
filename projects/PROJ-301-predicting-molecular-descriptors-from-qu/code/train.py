"""
Wrapper script for Model Training (User Story 2).

This script reconciles the run-book (quickstart.md) with the implementation.
It delegates to the actual implementation in code/03_model_training.py.

Execution: python code/train.py
Output:
  - artifacts/models/model_2d.pkl
  - artifacts/models/model_3d.pkl
  - artifacts/metrics/cv_metrics.json
  - artifacts/metrics/stability_report.json
  - artifacts/metrics/runtime_failure.json (if applicable)
"""
import sys
import os
import logging

# Add project root to path to ensure relative imports work if needed,
# though we will import the specific module directly.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code_03_model_training import main as training_main
from utils.logger import configure_logging_for_pipeline, get_logger

def main():
    """Entry point for the training pipeline."""
    configure_logging_for_pipeline("training")
    logger = get_logger("train")
    
    logger.info("Starting Model Training Pipeline (Wrapper: code/train.py)")
    logger.info("Delegating to code/03_model_training.py implementation...")
    
    try:
        # Execute the actual training logic
        training_main()
        logger.info("Model Training Pipeline completed successfully.")
    except Exception as e:
        logger.exception(f"Model Training Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()