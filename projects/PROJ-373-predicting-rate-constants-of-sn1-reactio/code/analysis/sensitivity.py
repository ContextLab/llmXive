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

def apply_descriptor_cutoffs(X: np.ndarray, feature_names: List[str], charge_cutoff: float, topo_cutoff: float) -> np.ndarray:
    """
    Apply cutoffs to Gasteiger charge and topological index features.
    Features with magnitude below cutoff are zeroed out.
    """
    X_masked = X.copy()
    
    # Identify charge and topo features (assuming naming convention or index ranges)
    # Since we don't have explicit mapping here, we assume all features are subject to cutoffs
    # or we filter based on name patterns if available.
    # For this implementation, we apply to all features as a generic sensitivity test.
    # In a real scenario, we would distinguish based on feature metadata.
    
    for i, name in enumerate(feature_names):
        # Check if feature is a charge or topo index (heuristic)
        is_charge = 'charge' in name.lower()
        is_topo = 'topo' in name.lower() or 'index' in name.lower()
        
        if is_charge:
            mask = np.abs(X[:, i]) < charge_cutoff
            X_masked[mask, i] = 0.0
        elif is_topo:
            mask = np.abs(X[:, i]) < topo_cutoff
            X_masked[mask, i] = 0.0
        else:
            # For other features, we might skip or apply a default
            pass
    
    return X_masked

def evaluate_model_performance(model: MPNN, X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Evaluate model and return R2 and MAE."""
    pred = run_inference(model, X)
    r2 = calculate_r2(y, pred)
    mae = np.mean(np.abs(y - pred))
    return r2, mae

def run_sensitivity_analysis(model: MPNN, X: np.ndarray, y: np.ndarray, feature_names: List[str]):
    """
    Run sensitivity analysis by sweeping descriptor cutoffs.
    """
    results = []
    
    # Define cutoff ranges
    charge_cutoffs = [0.0, 0.05, 0.1, 0.2, 0.5]
    topo_cutoffs = [0.0, 0.05, 0.1, 0.2, 0.5]
    
    for c_cutoff in charge_cutoffs:
        for t_cutoff in topo_cutoffs:
            X_masked = apply_descriptor_cutoffs(X, feature_names, c_cutoff, t_cutoff)
            r2, mae = evaluate_model_performance(model, X_masked, y)
            
            results.append({
                'charge_cutoff': c_cutoff,
                'topo_cutoff': t_cutoff,
                'r2': r2,
                'mae': mae
            })
    
    return results

def main():
    """Main entry point for sensitivity analysis."""
    logger = setup_logging()
    logger.info("Running sensitivity analysis (T027).")
    
    try:
        model, config = load_model_and_weights()
        X, y, feature_names = load_processed_data("test")
        
        results = run_sensitivity_analysis(model, X, y, feature_names)
        
        # Save results to artifact
        output_path = Path("artifacts/sensitivity_report.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Sensitivity analysis completed. Results saved to {output_path}")
        return results
        
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()