"""
Sensitivity Analysis for SN1 Rate Constant Prediction.

This module implements a sensitivity analysis by sweeping descriptor inclusion cutoffs
for both Gasteiger charge magnitude and topological index thresholds. It evaluates
how model performance (R² and MAE) varies as features are progressively filtered
based on these thresholds.

Dependencies:
- Requires T022 (model output) to be complete so that predictions and ground truth
  are available for evaluation.
- Uses the MPNN model architecture and evaluation logic from code/models/.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import r2_score, mean_absolute_error

# Project imports
from config import ensure_dirs
from utils.logger import get_logger
from models.mpnn import MPNN, MPNNConfig
from models.evaluate import load_processed_data, prepare_features, load_model_predictions

# Configure logging
logger = get_logger(__name__)

# Constants
ARTIFACTS_DIR = Path("artifacts")
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"

def load_model_and_weights(config_path: Path, weights_path: Path) -> Tuple[MPNN, MPNNConfig]:
    """Load the MPNN model and its configuration."""
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    model_config = MPNNConfig(**config_dict)
    model = MPNN(model_config)
    
    if weights_path.exists():
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
        logger.info(f"Loaded model weights from {weights_path}")
    else:
        logger.warning(f"Model weights file {weights_path} not found. Using random weights.")
    
    model.eval()
    return model, model_config

def apply_descriptor_cutoffs(
    feature_matrix: np.ndarray,
    gasteiger_cols: List[int],
    topological_cols: List[int],
    gasteiger_threshold: float,
    topological_threshold: float
) -> np.ndarray:
    """
    Apply inclusion cutoffs to descriptors.
    
    Features are included if:
    - Gasteiger charges: absolute value >= threshold
    - Topological indices: absolute value >= threshold
    
    Returns a masked feature matrix where excluded features are zeroed out.
    """
    masked_features = feature_matrix.copy()
    
    # Apply Gasteiger charge cutoff
    for col_idx in gasteiger_cols:
        mask = np.abs(feature_matrix[:, col_idx]) < gasteiger_threshold
        masked_features[mask, col_idx] = 0.0
    
    # Apply topological index cutoff
    for col_idx in topological_cols:
        mask = np.abs(feature_matrix[:, col_idx]) < topological_threshold
        masked_features[mask, col_idx] = 0.0
    
    return masked_features

def evaluate_model_performance(
    model: MPNN,
    feature_matrix: np.ndarray,
    target_values: np.ndarray,
    device: str = 'cpu'
) -> Tuple[float, float]:
    """
    Evaluate model performance on given features and targets.
    
    Returns:
        Tuple of (R² score, MAE)
    """
    model.to(device)
    model.eval()
    
    with torch.no_grad():
        # Convert to tensor
        X = torch.FloatTensor(feature_matrix).to(device)
        
        # Get predictions
        predictions = model(X).cpu().numpy().flatten()
    
    # Calculate metrics
    r2 = r2_score(target_values, predictions)
    mae = mean_absolute_error(target_values, predictions)
    
    return r2, mae

def run_sensitivity_analysis(
    model: MPNN,
    feature_matrix: np.ndarray,
    target_values: np.ndarray,
    gasteiger_cols: List[int],
    topological_cols: List[int],
    gasteiger_thresholds: List[float],
    topological_thresholds: List[float],
    device: str = 'cpu'
) -> pd.DataFrame:
    """
    Run sensitivity analysis by sweeping descriptor cutoffs.
    
    Args:
        model: Trained MPNN model
        feature_matrix: Full feature matrix (n_samples, n_features)
        target_values: Ground truth rate constants
        gasteiger_cols: Indices of Gasteiger charge features
        topological_cols: Indices of topological index features
        gasteiger_thresholds: List of thresholds to test for Gasteiger charges
        topological_thresholds: List of thresholds to test for topological indices
        device: Device to run inference on
    
    Returns:
        DataFrame with columns: gasteiger_threshold, topological_threshold, r2, mae
    """
    results = []
    
    logger.info(f"Running sensitivity analysis with {len(gasteiger_thresholds)} Gasteiger "
               f"thresholds and {len(topological_thresholds)} topological thresholds")
    
    for g_thresh in gasteiger_thresholds:
        for t_thresh in topological_thresholds:
            # Apply cutoffs
            masked_features = apply_descriptor_cutoffs(
                feature_matrix,
                gasteiger_cols,
                topological_cols,
                g_thresh,
                t_thresh
            )
            
            # Evaluate
            r2, mae = evaluate_model_performance(
                model, masked_features, target_values, device
            )
            
            results.append({
                'gasteiger_threshold': g_thresh,
                'topological_threshold': t_thresh,
                'r2': r2,
                'mae': mae
            })
            
            logger.debug(f"Thresholds: G={g_thresh:.4f}, T={t_thresh:.4f} -> R²={r2:.4f}, MAE={mae:.4f}")
    
    return pd.DataFrame(results)

def identify_feature_indices(
    feature_names: List[str],
    gasteiger_prefix: str = "gasteiger_",
    topological_prefix: str = "topological_"
) -> Tuple[List[int], List[int]]:
    """
    Identify indices of Gasteiger and topological features in the feature matrix.
    
    Args:
        feature_names: List of feature column names
        gasteiger_prefix: Prefix for Gasteiger charge features
        topological_prefix: Prefix for topological index features
    
    Returns:
        Tuple of (gasteiger_indices, topological_indices)
    """
    gasteiger_indices = []
    topological_indices = []
    
    for i, name in enumerate(feature_names):
        if name.startswith(gasteiger_prefix):
            gasteiger_indices.append(i)
        elif name.startswith(topological_prefix):
            topological_indices.append(i)
    
    logger.info(f"Found {len(gasteiger_indices)} Gasteiger features and "
               f"{len(topological_indices)} topological features")
    
    return gasteiger_indices, topological_indices

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on descriptor cutoffs")
    parser.add_argument("--model-config", type=str, default="artifacts/model_config.json",
                      help="Path to model configuration file")
    parser.add_argument("--model-weights", type=str, default="artifacts/best_model.pt",
                      help="Path to model weights file")
    parser.add_argument("--test-data", type=str, default="data/processed/test.csv",
                      help="Path to test dataset")
    parser.add_argument("--output", type=str, default="artifacts/sensitivity_report.csv",
                      help="Path to output sensitivity report")
    parser.add_argument("--gasteiger-range", type=float, nargs=2, default=[0.0, 0.5],
                      help="Range of Gasteiger thresholds [min, max]")
    parser.add_argument("--topological-range", type=float, nargs=2, default=[0.0, 0.5],
                      help="Range of topological thresholds [min, max]")
    parser.add_argument("--num-steps", type=int, default=10,
                      help="Number of steps in each threshold range")
    parser.add_argument("--device", type=str, default="cpu",
                      help="Device to run inference on (cpu or cuda)")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    ensure_dirs([Path(args.output).parent])
    
    # Load model
    logger.info("Loading model...")
    model, _ = load_model_and_weights(Path(args.model_config), Path(args.model_weights))
    
    # Load test data
    logger.info(f"Loading test data from {args.test_data}...")
    if not Path(args.test_data).exists():
        logger.error(f"Test data file not found: {args.test_data}")
        sys.exit(1)
    
    test_df = pd.read_csv(args.test_data)
    
    # Prepare features
    logger.info("Preparing features...")
    feature_matrix, target_values, feature_names = prepare_features(test_df)
    
    # Identify feature indices
    gasteiger_cols, topological_cols = identify_feature_indices(feature_names)
    
    if not gasteiger_cols:
        logger.error("No Gasteiger features found in the dataset")
        sys.exit(1)
    
    if not topological_cols:
        logger.error("No topological features found in the dataset")
        sys.exit(1)
    
    # Generate threshold ranges
    gasteiger_thresholds = np.linspace(
        args.gasteiger_range[0],
        args.gasteiger_range[1],
        args.num_steps
    ).tolist()
    
    topological_thresholds = np.linspace(
        args.topological_range[0],
        args.topological_range[1],
        args.num_steps
    ).tolist()
    
    logger.info(f"Testing {len(gasteiger_thresholds)} Gasteiger thresholds and "
               f"{len(topological_thresholds)} topological thresholds")
    
    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    results_df = run_sensitivity_analysis(
        model,
        feature_matrix,
        target_values,
        gasteiger_cols,
        topological_cols,
        gasteiger_thresholds,
        topological_thresholds,
        args.device
    )
    
    # Save results
    logger.info(f"Saving sensitivity report to {args.output}")
    results_df.to_csv(args.output, index=False)
    
    # Log summary
    best_r2 = results_df['r2'].max()
    worst_r2 = results_df['r2'].min()
    best_row = results_df.loc[results_df['r2'].idxmax()]
    
    logger.info(f"Sensitivity analysis complete. R² range: [{worst_r2:.4f}, {best_r2:.4f}]")
    logger.info(f"Best performance: R²={best_row['r2']:.4f}, MAE={best_row['mae']:.4f} "
               f"at G_thresh={best_row['gasteiger_threshold']:.4f}, "
               f"T_thresh={best_row['topological_threshold']:.4f}")
    
    print(f"Sensitivity report saved to: {args.output}")
    return results_df

if __name__ == "__main__":
    main()