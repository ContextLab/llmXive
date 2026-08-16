import os
import sys
import json
import logging
import pickle
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from config import get_project_root, get_results_dir, get_models_dir, get_processed_data_dir, ensure_directories, get_random_seed
from utils.logger import setup_logging
from utils.importance_analyzer import run_correlation_analysis, setup_importance_logger

def setup_pipeline_logging():
    """Set up logging for the T031 pipeline."""
    return setup_logging("t031_pipeline")

def load_model(model_path: str):
    """Load the trained GPR model."""
    logger = logging.getLogger("t031_pipeline")
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_processed_test_data():
    """
    Load processed test data (X_test, y_test, feature_names).
    Assumes data is saved in standard locations by T016.
    """
    logger = logging.getLogger("t031_pipeline")
    processed_dir = get_processed_data_dir()
    
    # Assuming T016 saves these files or they are accessible
    # Standard names based on typical pipeline outputs
    x_test_path = os.path.join(processed_dir, "X_test.npy")
    y_test_path = os.path.join(processed_dir, "y_test.npy")
    feature_names_path = os.path.join(processed_dir, "feature_names.json")
    
    if not all(os.path.exists(p) for p in [x_test_path, y_test_path, feature_names_path]):
        logger.error("Test data files not found. Ensure T016 (preprocess) has completed successfully.")
        sys.exit(1)
    
    import numpy as np
    X_test = np.load(x_test_path)
    y_test = np.load(y_test_path)
    
    with open(feature_names_path, 'r') as f:
        feature_names = json.load(f)
    
    logger.info(f"Loaded test data: X_test shape {X_test.shape}, y_test shape {y_test.shape}")
    return X_test, y_test, feature_names

def main():
    """
    Orchestrates T031: Permutation Importance Correlation Analysis.
    1. Load Model.
    2. Load Test Data.
    3. Run Correlation Analysis (loads baseline, computes importance, saves to metrics).
    """
    logger = setup_pipeline_logging()
    logger.info("Starting T031 Pipeline")
    
    ensure_directories()
    results_dir = get_results_dir()
    models_dir = get_models_dir()
    
    # Paths
    model_path = os.path.join(models_dir, "gpr_model.pkl")
    
    if not os.path.exists(model_path):
        logger.error(f"GPR Model not found at {model_path}. Run T026 first.")
        sys.exit(1)
    
    try:
        # Load Data
        model = load_model(model_path)
        X_test, y_test, feature_names = load_processed_test_data()
        
        # Run Analysis
        # This function handles loading the baseline (and failing if missing),
        # calculating importance, and updating metrics.json
        results = run_correlation_analysis(
            model=model,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            results_dir=results_dir,
            logger=logger
        )
        
        logger.info("T031 Pipeline completed successfully.")
        print(json.dumps(results, indent=2))
        
    except FileNotFoundError as e:
        logger.critical(f"Critical Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
