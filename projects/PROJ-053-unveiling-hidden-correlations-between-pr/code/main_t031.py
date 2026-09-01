import os
import sys
import json
import logging
import pickle
from pathlib import Path

from config import (
    get_project_root,
    get_models_dir,
    get_results_dir,
    get_processed_data_dir,
    ensure_directories,
    get_logger
)
from utils.importance_analyzer import run_correlation_analysis

def setup_pipeline_logging():
    """Setup logging for the T031 execution."""
    ensure_directories()
    logger = get_logger("main_t031")
    return logger

def load_model(model_path: str):
    """Load the trained GPR model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_processed_test_data(csv_path: str, target_col: str):
    """Load test data and split into X, y."""
    import pandas as pd
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Test data file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Identify feature columns (exclude known targets)
    known_targets = ['yield_strength', 'ductility', 'fatigue_life']
    features = [c for c in df.columns if c not in known_targets]
    
    if target_col not in df.columns:
        # Fallback to first known target found
        for t in known_targets:
            if t in df.columns:
                target_col = t
                break
        else:
            raise ValueError("No valid target column found in dataset.")
    
    X = df[features].values
    y = df[target_col].values
    
    return X, y, features

def main():
    logger = setup_pipeline_logging()
    logger.info("Starting T031: Permutation Importance Correlation Analysis")
    
    # Paths
    model_path = os.path.join(get_models_dir(), "gpr_model.pkl")
    test_data_path = os.path.join(get_processed_data_dir(), "test.csv")
    results_path = os.path.join(get_results_dir(), "metrics.json")
    
    try:
        # 1. Load Model
        logger.info(f"Loading model from {model_path}")
        model = load_model(model_path)
        
        # 2. Load Data
        logger.info(f"Loading test data from {test_data_path}")
        X_test, y_test, feature_names = load_processed_test_data(test_data_path, 'yield_strength')
        
        # 3. Run Analysis
        logger.info("Running correlation analysis...")
        importance_scores, correlation, model_ranking = run_correlation_analysis(
            model, X_test, y_test, feature_names, logger
        )
        
        # 4. Save to Metrics
        metrics = {}
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                metrics = json.load(f)
        
        metrics["permutation_importance_correlation"] = correlation
        metrics["permutation_importance_rankings"] = model_ranking
        
        with open(results_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Successfully updated {results_path}")
        logger.info(f"Spearman Correlation: {correlation:.4f}")
        
    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed with error: {e}")
        raise

if __name__ == "__main__":
    main()