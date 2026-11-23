"""
Diagnostics module for grain boundary data analysis.

This module computes mutual information between misorientation angle and Σ value
to assess collinearity before model training.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.metrics import mutual_info_score
from utils import setup_logging

logger = setup_logging("diagnostics", logging.INFO)

def calculate_sigma_from_misorientation(misorientation_angle: float) -> float:
    """
    Calculate Σ value from misorientation angle (simplified approximation).
    
    Note: In production, this should use full CSL calculations.
    For diagnostics, we use a simplified mapping for demonstration.
    
    Args:
        misorientation_angle: Misorientation angle in degrees.
    
    Returns:
        Approximate Σ value or NaN if calculation fails.
    """
    # Simplified mapping for common CSL boundaries
    # This is a placeholder; real implementation uses pymatgen CSL
    mapping = {
        38.94: 3,
        28.07: 5,
        36.87: 9,
        43.60: 11,
        50.48: 13,
        21.80: 17,
        31.59: 21,
        25.24: 25
    }
    
    # Find closest match within tolerance
    tolerance = 2.0
    for angle, sigma in mapping.items():
        if abs(misorientation_angle - angle) < tolerance:
            return float(sigma)
    
    # Fallback: estimate based on angle (not physically rigorous)
    if misorientation_angle < 15:
        return float('nan')  # Low angle boundary
    elif misorientation_angle < 30:
        return 5.0 + (misorientation_angle - 15) / 15.0 * 10.0
    else:
        return 15.0 + (misorientation_angle - 30) / 30.0 * 10.0

def compute_mutual_information(data: pd.DataFrame, feature1: str, feature2: str) -> float:
    """
    Compute mutual information between two features.
    
    Args:
        data: DataFrame containing the features.
        feature1: Name of the first feature (e.g., 'misorientation_angle').
        feature2: Name of the second feature (e.g., 'sigma_value').
    
    Returns:
        Mutual information score.
    """
    # Drop rows with NaN values for these features
    valid_data = data[[feature1, feature2]].dropna()
    
    if len(valid_data) < 2:
        return 0.0
    
    # Discretize continuous variables for MI calculation
    # Use quantile-based binning
    n_bins = 10
    
    x = valid_data[feature1].values
    y = valid_data[feature2].values
    
    # Discretize
    x_bins = np.digitize(x, np.linspace(x.min(), x.max(), n_bins))
    y_bins = np.digitize(y, np.linspace(y.min(), y.max(), n_bins))
    
    # Compute mutual information
    mi = mutual_info_score(x_bins, y_bins)
    return mi

def run_collinearity_diagnostic(data_path: str = "data/processed/cleaned_dataset.parquet",
                                output_path: str = "artifacts/reports/collinearity_diagnostic.json") -> Dict[str, Any]:
    """
    Run collinearity diagnostic for misorientation angle and Σ value.
    
    Args:
        data_path: Path to the cleaned dataset.
        output_path: Path to save the diagnostic report.
    
    Returns:
        Diagnostic report dictionary.
    """
    logger.info(f"Loading data from {data_path}")
    
    # Check if data exists
    if not Path(data_path).exists():
        logger.error(f"Data file not found: {data_path}")
        report = {
            "status": "error",
            "message": f"Data file not found: {data_path}",
            "mi_score": None
        }
        save_report(report, output_path)
        return report
    
    # Load data
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        report = {
            "status": "error",
            "message": f"Failed to load data: {str(e)}",
            "mi_score": None
        }
        save_report(report, output_path)
        return report
    
    logger.info(f"Loaded {len(df)} records")
    
    # Check for required columns
    required_cols = ['misorientation_angle', 'sigma_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        report = {
            "status": "error",
            "message": f"Missing required columns: {missing_cols}",
            "mi_score": None
        }
        save_report(report, output_path)
        return report
    
    # Check for valid Σ values
    valid_sigma_count = df['sigma_value'].notna().sum()
    total_count = len(df)
    
    if valid_sigma_count == 0:
        logger.warning("No valid Σ values found in dataset")
        report = {
            "status": "unavailable",
            "message": "No valid Σ values in dataset after preprocessing.",
            "count": int(total_count)
        }
        save_report(report, output_path)
        return report
    
    logger.info(f"Found {valid_sigma_count} valid Σ values out of {total_count} records")
    
    # Compute Mutual Information
    try:
        mi_score = compute_mutual_information(df, 'misorientation_angle', 'sigma_value')
    except Exception as e:
        logger.error(f"Failed to compute mutual information: {e}")
        report = {
            "status": "error",
            "message": f"Failed to compute mutual information: {str(e)}",
            "mi_score": None
        }
        save_report(report, output_path)
        return report
    
    # Log descriptive note
    logger.info(f"Mutual Information (MI) between misorientation and Σ: {mi_score:.4f}")
    logger.info("MI > 0.8 indicates strong dependency; relationship is descriptive, not causal.")
    
    # Determine strength
    if mi_score > 0.8:
        strength = "strong"
    elif mi_score > 0.4:
        strength = "moderate"
    else:
        strength = "weak"
    
    report = {
        "status": "success",
        "feature1": "misorientation_angle",
        "feature2": "sigma_value",
        "mi_score": float(mi_score),
        "strength": strength,
        "valid_sigma_count": int(valid_sigma_count),
        "total_count": int(total_count),
        "note": "The relationship between misorientation and Σ value is descriptive, not causal, as Σ is derived from misorientation."
    }
    
    save_report(report, output_path)
    return report

def save_report(report: Dict[str, Any], output_path: str) -> None:
    """Save diagnostic report to JSON file."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    with open(p, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {output_path}")

def main():
    """Main entry point for diagnostics."""
    logger.info("Starting collinearity diagnostic analysis")
    
    # Run diagnostic
    report = run_collinearity_diagnostic()
    
    logger.info("Diagnostic analysis complete")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
