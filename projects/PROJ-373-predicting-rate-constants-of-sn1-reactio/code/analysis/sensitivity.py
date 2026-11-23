import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import torch

from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from models.mpnn import MPNN, create_mpnn_from_config, MPNNConfig
from analysis.interpret import load_model_and_weights, load_processed_data, run_inference, calculate_r2

def apply_descriptor_cutoffs(X: np.ndarray, feature_names: List[str], variance_threshold: float) -> np.ndarray:
    """
    Apply variance-based cutoffs to descriptor features.
    Features with variance < threshold are zeroed out (filtered).
    This implements the logic: filter descriptors based on variance < threshold.
    
    Note: We do NOT modify descriptor magnitudes, only filter which are included.
    Zeroing out is the mechanism to exclude them from the model input while maintaining shape.
    """
    X_masked = X.copy()
    
    # Calculate variance for each feature
    variances = np.var(X, axis=0)
    
    # Identify features with variance below threshold
    features_to_filter = variances < variance_threshold
    
    # Zero out those features (effectively removing them from input)
    X_masked[:, features_to_filter] = 0.0
    
    return X_masked

def evaluate_model_performance(model: MPNN, X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Evaluate model and return R2 and MAE."""
    pred = run_inference(model, X)
    r2 = calculate_r2(y, pred)
    mae = np.mean(np.abs(y - pred))
    return r2, mae

def run_sensitivity_analysis(model: MPNN, X: np.ndarray, y: np.ndarray, feature_names: List[str]):
    """
    Run sensitivity analysis by sweeping descriptor variance thresholds.
    Reports resulting R² and MAE for each threshold.
    
    Thresholds: [0.01, 0.02, 0.05, 0.1, 0.2] as per T036 logic.
    """
    results = []
    
    # Define variance thresholds to sweep
    variance_thresholds = [0.01, 0.02, 0.05, 0.1, 0.2]
    
    for threshold in variance_thresholds:
        X_filtered = apply_descriptor_cutoffs(X, feature_names, threshold)
        r2, mae = evaluate_model_performance(model, X_filtered, y)
        
        results.append({
            'threshold': threshold,
            'r2': r2,
            'mae': mae
        })
    
    return results

def main():
    """Main entry point for sensitivity analysis (T027)."""
    logger = setup_logging()
    logger.info("Running sensitivity analysis (T027).")
    
    try:
        # Load the best model (from T022/T023)
        model, config = load_model_and_weights()
        
        # Load processed test data
        X, y, feature_names = load_processed_data("test")
        
        logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
        
        # Run sensitivity analysis
        results = run_sensitivity_analysis(model, X, y, feature_names)
        
        # Save results to artifact
        output_path = Path("artifacts/sensitivity_report.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Sensitivity analysis completed. Results saved to {output_path}")
        
        # Log summary
        logger.info("Sensitivity Report Summary:")
        for res in results:
            logger.info(f"  Threshold: {res['threshold']:.4f} -> R2: {res['r2']:.4f}, MAE: {res['mae']:.4f}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()