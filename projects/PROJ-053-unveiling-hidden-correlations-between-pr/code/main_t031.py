import os
import sys
import json
import logging
import pickle
from pathlib import Path

from config import get_results_dir, get_models_dir, get_project_root
from utils.logger import setup_logging
from utils.importance_analyzer import run_correlation_analysis, setup_importance_logger

def setup_pipeline_logging():
    """Setup logging for T031 pipeline."""
    return setup_logging("t031_pipeline")

def main():
    """Main entry point for T031 execution."""
    logger = setup_pipeline_logging()
    logger.info("Starting T031: Permutation Importance Correlation Analysis Pipeline")
    
    # 1. Load GPR Model
    models_dir = get_models_dir()
    model_path = models_dir / "gpr_model.pkl"
    
    if not model_path.exists():
        logger.error("GPR model not found at {}. Please run T026 first.".format(model_path))
        sys.exit(1)
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info("GPR model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load GPR model: {e}")
        sys.exit(1)
    
    # 2. Load Test Data
    # We expect the test data to be saved by the preprocessing/training pipeline.
    # Common location: data/processed/test_data.pkl
    processed_dir = get_project_root() / "data" / "processed"
    test_data_path = processed_dir / "test_data.pkl"
    
    if not test_data_path.exists():
        logger.error("Test data not found at {}. Please ensure T016/T018 have run.".format(test_data_path))
        sys.exit(1)
    
    try:
        with open(test_data_path, 'rb') as f:
            test_data = pickle.load(f)
            X_test = test_data['X_test']
            y_test = test_data['y_test']
            feature_names = test_data['feature_names']
        logger.info("Test data loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        sys.exit(1)
    
    # 3. Run Correlation Analysis
    try:
        results = run_correlation_analysis(model, X_test, y_test, feature_names, logger)
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        sys.exit(1)
    
    # 4. Save Results to metrics.json
    results_dir = get_results_dir()
    metrics_path = results_dir / "metrics.json"
    
    # Load existing metrics
    metrics = {}
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing metrics.json is invalid. Overwriting.")
            metrics = {}
    
    # Append T031 results
    metrics["t031_correlation_analysis"] = results
    
    # Write back
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Results appended to {metrics_path}")
    logger.info("T031 completed successfully.")

if __name__ == "__main__":
    main()
