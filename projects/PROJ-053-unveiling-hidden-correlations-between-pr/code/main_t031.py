import os
import sys
import json
import logging
import pickle
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.importance_analyzer import setup_importance_logger, run_correlation_analysis
from config import get_models_dir, get_data_dir, get_results_dir, ensure_directories

def setup_pipeline_logging():
    """Setup logging for the T031 pipeline."""
    ensure_directories([get_data_dir() / 'processed', get_results_dir(), get_models_dir()])
    logger = setup_importance_logger()
    return logger

def load_model(model_path: Path):
    """Load the trained GPR model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_processed_test_data(test_csv_path: Path):
    """Load processed test data."""
    import pandas as pd
    if not test_csv_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_csv_path}")
    return pd.read_csv(test_csv_path)

def main():
    """
    Orchestrator for T031: Permutation Importance Correlation Analysis.
    """
    logger = setup_pipeline_logging()
    logger.info("Starting T031: Permutation Importance Correlation Analysis")
    
    try:
        # Paths
        models_dir = get_models_dir()
        model_path = models_dir / 'gpr_model.pkl'
        
        processed_dir = get_data_dir() / 'processed'
        test_csv_path = processed_dir / 'test.csv'
        
        # Load Data
        logger.info(f"Loading model from {model_path}")
        model = load_model(model_path)
        
        logger.info(f"Loading test data from {test_csv_path}")
        df_test = load_processed_test_data(test_csv_path)
        
        # Identify Target
        target_cols = ['yield_strength', 'ductility', 'fatigue_life']
        target = None
        for t in target_cols:
            if t in df_test.columns:
                target = t
                break
        
        if not target:
            logger.error("No target column found in test data.")
            sys.exit(1)
        
        feature_cols = [c for c in df_test.columns if c != target]
        X_test = df_test[feature_cols].values
        y_test = df_test[target].values
        
        logger.info(f"Running analysis on {len(feature_cols)} features, target: {target}")
        
        # Run Correlation Analysis
        # Note: user_baseline_path is optional; if None, it attempts config/literature
        correlation = run_correlation_analysis(
            model, X_test, y_test, feature_cols, logger, user_baseline_path=None
        )
        
        # Update Metrics
        metrics_path = get_results_dir() / 'metrics.json'
        metrics = {}
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        
        metrics['permutation_importance_correlation'] = correlation
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Success. Correlation: {correlation}. Updated {metrics_path}")
        
    except Exception as e:
        logger.error(f"T031 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
