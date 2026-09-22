"""
Standalone runner for the evaluator module.
"""
import json
import logging
from pathlib import Path
import pandas as pd
from config import ensure_directories
from evaluator import (
    load_metrics, save_metrics, stratified_split,
    calculate_20th_percentile_threshold, calculate_baseline,
    calculate_correlation, calculate_null_distribution,
    predict_collapse, evaluate_performance, calculate_power_analysis,
    run_full_evaluation
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Execute the evaluation pipeline."""
    ensure_directories()
    run_full_evaluation()
    logger.info("Evaluator runner completed.")

if __name__ == "__main__":
    main()
