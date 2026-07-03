import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mutual_info_regression

# Import shared utilities to ensure consistency
from utils import setup_logging, set_random_seed

# Configure logging
logger = setup_logging(__name__)

def calculate_sigma_value(misorientation_angle_deg: float) -> int:
    """
    Calculate the Sigma (Σ) value from a misorientation angle using the
    Coincidence Site Lattice (CSL) definition for cubic systems.
    
    This uses a lookup table for common low-angle boundaries and an
    approximation for others based on the relationship between angle
    and CSL density.
    
    Args:
        misorientation_angle_deg: Misorientation angle in degrees.
        
    Returns:
        The calculated Sigma value (integer). Returns -1 if no simple
        CSL relationship is found or angle is invalid.
    """
    if not (0 < misorientation_angle_deg <= 180):
        logger.warning(f"Invalid misorientation angle: {misorientation_angle_deg}")
        return -1

    # Common CSL angles for cubic crystals (approximate)
    # These are derived from the relationship between rotation angle and CSL
    common_csl = {
        60.0: 3,   # <111> rotation
        36.87: 5,  # <100> rotation
        53.13: 5,  # <100> rotation (alternative)
        28.07: 13, # <100> rotation
        22.62: 13, # <110> rotation
        14.25: 17, # <100> rotation
        13.17: 25, # <100> rotation
        90.0: 1,   # Special case
        180.0: 1,  # Special case
    }

    # Check for exact matches first (with tolerance)
    tolerance = 0.5
    for angle, sigma in common_csl.items():
        if abs(misorientation_angle_deg - angle) < tolerance:
            return sigma

    # For other angles, we use a heuristic approximation
    # In real research, this would involve a full CSL lookup or calculation
    # based on the specific rotation axis and crystallography.
    # Here we map to the nearest common CSL or return a calculated estimate.
    
    # Simple heuristic: map to nearest low-Sigma value
    angles = sorted(common_csl.keys())
    if not angles:
        return -1
        
    # Find nearest angle
    nearest_angle = min(angles, key=lambda x: abs(x - misorientation_angle_deg))
    return common_csl[nearest_angle]


def compute_mutual_information(data: pd.DataFrame, feature_x: str, feature_y: str) -> float:
    """
    Compute Mutual Information (MI) between two features.
    
    Args:
        data: DataFrame containing the features.
        feature_x: Name of the first feature (misorientation angle).
        feature_y: Name of the second feature (Σ value).
        
    Returns:
        The calculated Mutual Information value.
        
    Raises:
        ValueError: If features are missing or contain non-numeric data.
    """
    if feature_x not in data.columns or feature_y not in data.columns:
        raise ValueError(f"Features {feature_x} and/or {feature_y} not found in data.")
    
    # Drop rows with NaN in either column
    valid_data = data[[feature_x, feature_y]].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data points to compute Mutual Information.")
        return 0.0
    
    X = valid_data[feature_x].values.reshape(-1, 1)
    y = valid_data[feature_y].values
    
    # Use sklearn's mutual_info_regression
    # k=3 is a reasonable default for continuous variables
    mi_score = mutual_info_regression(X, y, k=3, random_state=42)
    
    return float(mi_score[0])


def run_diagnostics(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run collinearity diagnostics on the raw dataset.
    
    This function:
    1. Loads the parsed geometry data.
    2. Computes Sigma values if not present.
    3. Calculates Mutual Information between misorientation angle and Sigma value.
    4. Logs a warning if MI > 0.8.
    5. Saves the diagnostic report to JSON.
    
    Args:
        data_path: Path to the input data file (parquet).
        output_path: Path to save the diagnostic report (JSON).
        
    Returns:
        Dictionary containing the diagnostic results.
    """
    logger.info(f"Loading data from {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise
    
    # Ensure required columns exist
    required_cols = ['misorientation_angle']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in data.")
    
    # Calculate Sigma values if not present
    if 'sigma_value' not in df.columns:
        logger.info("Calculating Sigma values from misorientation angles...")
        df['sigma_value'] = df['misorientation_angle'].apply(calculate_sigma_value)
    
    # Compute Mutual Information
    logger.info("Computing Mutual Information between misorientation angle and Sigma value...")
    try:
        mi_score = compute_mutual_information(df, 'misorientation_angle', 'sigma_value')
    except Exception as e:
        logger.error(f"Failed to compute Mutual Information: {e}")
        raise
    
    # Log warning if strong dependency detected
    if mi_score > 0.8:
        logger.warning(
            "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
        )
    
    # Prepare report
    report = {
        "feature_x": "misorientation_angle",
        "feature_y": "sigma_value",
        "mutual_information": mi_score,
        "threshold_warning": mi_score > 0.8,
        "message": "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal." if mi_score > 0.8 else "MI <= 0.8 indicates weak to moderate dependency.",
        "data_points_analyzed": len(df),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save report
    logger.info(f"Saving diagnostic report to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report


def main():
    """
    Main entry point for the diagnostics script.
    
    Usage:
        python code/diagnostics.py --input data/processed/parsed_geometry.parquet --output artifacts/reports/collinearity_diagnostic.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run collinearity diagnostics on grain boundary data.")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True, 
        help="Path to the input parquet file (parsed geometry data)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=True, 
        help="Path to save the diagnostic report (JSON)."
    )
    
    args = parser.parse_args()
    
    set_random_seed(42)
    
    try:
        report = run_diagnostics(args.input, args.output)
        logger.info("Diagnostics completed successfully.")
        logger.info(f"Mutual Information: {report['mutual_information']:.4f}")
        if report['threshold_warning']:
            logger.warning(report['message'])
        return 0
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
