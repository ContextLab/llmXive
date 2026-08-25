import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, KFold
from sklearn.linear_model import LinearRegression
from utils.logging import AnalysisError, get_logger
from config import get_config

def run_cross_validation(data_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Perform 5-fold cross-validation to assess out-of-sample R² for both
    baseline (coupling functions only) and full (coupling + composition) models.
    
    Args:
        data_path: Path to the aligned CSV data file.
        output_path: Path to save the JSON results artifact.
        
    Returns:
        Dictionary containing cross-validation metrics for each target variable.
    """
    logger = get_logger()
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Input data file not found: {data_path}")
        
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    
    # Define feature sets
    composition_cols = ["O_Fe", "He_H", "C_O"]
    coupling_cols = ["epsilon", "newell", "v_bs", "v_bt"]
    targets = ["Dst", "Kp"]
    
    # Validate required columns exist
    missing_cols = [col for col in composition_cols + coupling_cols + targets if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
    
    results = {}
    
    for target in targets:
        logger.info(f"Processing target: {target}")
        
        # Prepare baseline model data (coupling functions only)
        # Drop rows with any NaN in coupling columns or target
        mask_baseline = df[coupling_cols + [target]].notna().all(axis=1)
        X_baseline = df.loc[mask_baseline, coupling_cols]
        y_baseline = df.loc[mask_baseline, target]
        
        if len(X_baseline) == 0:
            logger.warning(f"No valid data for baseline model on target {target}")
            continue
            
        # Prepare full model data (coupling + composition)
        # Drop rows with any NaN in all predictor columns or target
        mask_full = df[coupling_cols + composition_cols + [target]].notna().all(axis=1)
        X_full = df.loc[mask_full, coupling_cols + composition_cols]
        y_full = df.loc[mask_full, target]
        
        if len(X_full) == 0:
            logger.warning(f"No valid data for full model on target {target}")
            continue
        
        # Initialize models
        model_baseline = LinearRegression()
        model_full = LinearRegression()
        
        # Setup 5-fold cross-validation
        # shuffle=True ensures random split, random_state=42 for reproducibility
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        
        # Compute cross-validation scores (R²)
        logger.info(f"Running 5-fold CV for baseline model on {target} (n={len(X_baseline)})")
        try:
            scores_baseline = cross_val_score(
                model_baseline, X_baseline, y_baseline, 
                cv=kfold, scoring="r2"
            )
        except Exception as e:
            raise AnalysisError(f"Cross-validation failed for baseline model: {e}") from e
            
        logger.info(f"Running 5-fold CV for full model on {target} (n={len(X_full)})")
        try:
            scores_full = cross_val_score(
                model_full, X_full, y_full, 
                cv=kfold, scoring="r2"
            )
        except Exception as e:
            raise AnalysisError(f"Cross-validation failed for full model: {e}") from e
        
        # Calculate metrics
        mean_baseline_r2 = float(np.mean(scores_baseline))
        std_baseline_r2 = float(np.std(scores_baseline))
        mean_full_r2 = float(np.mean(scores_full))
        std_full_r2 = float(np.std(scores_full))
        delta_r2 = mean_full_r2 - mean_baseline_r2
        
        results[target] = {
            "baseline_cv_r2_mean": mean_baseline_r2,
            "baseline_cv_r2_std": std_baseline_r2,
            "baseline_cv_r2_scores": scores_baseline.tolist(),
            "full_cv_r2_mean": mean_full_r2,
            "full_cv_r2_std": std_full_r2,
            "full_cv_r2_scores": scores_full.tolist(),
            "delta_cv_r2": delta_r2,
            "n_samples": len(X_full),
            "n_splits": 5
        }
        
        logger.info(f"Target {target}: Baseline R²={mean_baseline_r2:.4f} (+/- {std_baseline_r2:.4f}), "
                    f"Full R²={mean_full_r2:.4f} (+/- {std_full_r2:.4f}), ΔR²={delta_r2:.4f}")
    
    if not results:
        logger.warning("No results generated; no valid targets processed.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results to JSON
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Cross-validation results saved to {output_path}")
    return results

def main():
    """Entry point for running cross-validation analysis."""
    logger = get_logger()
    cfg = get_config()
    
    # Define paths based on configuration
    input_path = cfg["data_processed"] / "aligned_data.csv"
    output_path = cfg["data_artifacts"] / "cross_validation_results.json"
    
    logger.info("Starting cross-validation analysis...")
    try:
        results = run_cross_validation(input_path, output_path)
        logger.info("Cross-validation analysis completed successfully.")
    except Exception as e:
        logger.error(f"Cross-validation analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()