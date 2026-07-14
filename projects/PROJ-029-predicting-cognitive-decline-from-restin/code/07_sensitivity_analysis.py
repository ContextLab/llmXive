"""
T030a: Sensitivity Analysis (Part 1) - Decision Threshold Sweep
---------------------------------------------------------------
Performs a decision threshold sweep over {0.45, 0.50, 0.55} on the trained model.
Reports false-positive and false-negative rates for each threshold.

This script assumes:
1. The model has been trained and saved to data/processed/model.pkl
2. The graph metrics and labels are available in data/processed/graph_metrics.csv
3. The model was trained using a Random Forest classifier

Output:
- data/processed/sensitivity_report.json: Contains FP/FN rates for each threshold
"""

import os
import sys
import json
import argparse
import warnings
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logger import get_logger
from utils.io import load_csv, save_json
from config import get_config

# Suppress specific warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def get_logger_wrapper(name: str) -> logging.Logger:
    """Create a logger with file and console handlers."""
    return get_logger(name, log_file=str(project_root / "data" / "artifacts" / f"{name}.log"))

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        return 0.0

def check_memory_limit(limit_gb: float = 7.0, logger: logging.Logger = None) -> bool:
    """Check if memory usage is within limit."""
    usage = get_memory_usage_gb()
    if logger:
        logger.info(f"Current memory usage: {usage:.2f} GB (Limit: {limit_gb} GB)")
    return usage < limit_gb

def load_model_and_data(model_path: str, data_path: str, logger: logging.Logger) -> Tuple[Any, pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load the trained model and data for sensitivity analysis.
    
    Args:
        model_path: Path to the saved model (PKL)
        data_path: Path to the graph metrics CSV
        logger: Logger instance
        
    Returns:
        Tuple of (model, dataframe, X, y)
    """
    logger.info(f"Loading model from {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}")
    
    df = load_csv(data_path)
    
    # Identify feature columns (all numeric columns except 'subject_id' and 'decline_label')
    feature_cols = [col for col in df.columns if col not in ['subject_id', 'decline_label'] and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in the dataset")
    
    X = df[feature_cols].values
    y = df['decline_label'].values
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
    return model, df, X, y

def define_decline_label(df: pd.DataFrame, threshold: int = 3) -> pd.Series:
    """
    Define cognitive decline label based on MMSE/MOCA score drop.
    This is a wrapper to ensure consistency with training.
    
    Args:
        df: DataFrame with MMSE/MOCA scores
        threshold: Minimum drop to be considered decline
        
    Returns:
        Series of decline labels (0: no decline, 1: decline)
    """
    if 'mmse_t1' in df.columns and 'mmse_t2' in df.columns:
        drop = df['mmse_t1'] - df['mmse_t2']
    elif 'moca_t1' in df.columns and 'moca_t2' in df.columns:
        drop = df['moca_t1'] - df['moca_t2']
    else:
        # If columns don't exist, assume the label is already present
        if 'decline_label' in df.columns:
            return df['decline_label']
        else:
            raise ValueError("Cannot determine decline label: missing score columns")
    
    return (drop >= threshold).astype(int)

def run_threshold_sweep(model: Any, X: np.ndarray, y: np.ndarray, 
                        thresholds: List[float] = [0.45, 0.50, 0.55],
                        logger: logging.Logger = None) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping decision thresholds.
    
    Args:
        model: Trained classifier model
        X: Feature matrix
        y: True labels
        thresholds: List of decision thresholds to evaluate
        logger: Logger instance
        
    Returns:
        Dictionary containing metrics for each threshold
    """
    if logger:
        logger.info(f"Running threshold sweep over {thresholds}")
    
    # Get probability predictions
    if hasattr(model, 'predict_proba'):
        y_prob = model.predict_proba(X)[:, 1]
    else:
        # Fallback to decision function if predict_proba not available
        if hasattr(model, 'decision_function'):
            y_score = model.decision_function(X)
            # Convert to probabilities using sigmoid (approximation)
            y_prob = 1 / (1 + np.exp(-y_score))
        else:
            raise AttributeError("Model does not have predict_proba or decision_function")
    
    results = {}
    
    for threshold in thresholds:
        logger.info(f"Evaluating threshold: {threshold}")
        
        # Apply threshold to get binary predictions
        y_pred = (y_prob >= threshold).astype(int)
        
        # Calculate metrics
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
        
        # Calculate rates
        fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, zero_division=0)
        recall = recall_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)
        
        results[str(threshold)] = {
            "threshold": threshold,
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "false_positive_rate": float(fp_rate),
            "false_negative_rate": float(fn_rate),
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1)
        }
        
        if logger:
            logger.info(f"  FP Rate: {fp_rate:.4f}, FN Rate: {fn_rate:.4f}")
            logger.info(f"  Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
    
    return results

def write_outputs(results: Dict[str, Any], output_path: str, logger: logging.Logger) -> None:
    """Write sensitivity analysis results to JSON file."""
    logger.info(f"Writing results to {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    save_json(results, output_path)
    logger.info("Results written successfully")

def main():
    """Main entry point for sensitivity analysis."""
    # Setup logging
    logger = get_logger_wrapper("07_sensitivity_analysis")
    logger.info("Starting T030a: Sensitivity Analysis (Part 1) - Threshold Sweep")
    
    # Configuration
    config = get_config()
    model_path = str(project_root / "data" / "processed" / "model.pkl")
    data_path = str(project_root / "data" / "processed" / "graph_metrics.csv")
    output_path = str(project_root / "data" / "processed" / "sensitivity_report.json")
    
    # Check memory limit
    if not check_memory_limit(limit_gb=7.0, logger=logger):
        logger.error("Memory limit exceeded. Aborting.")
        sys.exit(1)
    
    try:
        # Load model and data
        model, df, X, y = load_model_and_data(model_path, data_path, logger)
        
        # Define thresholds for sweep
        thresholds = [0.45, 0.50, 0.55]
        
        # Run threshold sweep
        results = run_threshold_sweep(model, X, y, thresholds, logger)
        
        # Add metadata
        results["metadata"] = {
            "analysis_type": "threshold_sweep",
            "total_samples": int(len(X)),
            "positive_class_ratio": float(np.mean(y)),
            "thresholds_evaluated": thresholds,
            "config": config
        }
        
        # Write outputs
        write_outputs(results, output_path, logger)
        
        logger.info("Sensitivity analysis completed successfully")
        print(f"Sensitivity report written to: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()