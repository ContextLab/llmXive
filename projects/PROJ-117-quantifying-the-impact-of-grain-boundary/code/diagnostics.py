"""
Diagnostics module for grain boundary analysis.
Implements mutual information calculations and collinearity diagnostics.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.metrics import mutual_info_regression

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sigma_from_misorientation(misorientation_angle_deg: float) -> int:
    """
    Calculate the Sigma (Σ) value from misorientation angle using CSL definition.
    
    For cubic systems, common Σ values correspond to specific misorientation angles:
    Σ3: 60° around <111>
    Σ5: 36.87° around <100>
    Σ9: 38.94° around <110>
    Σ11: 50.48° around <110>
    Σ13: 27.80° around <110>
    Σ17: 28.07° around <100>
    Σ19: 26.53° around <111>
    Σ21: 39.12° around <110>
    Σ25: 36.87° around <110> (different axis)
    
    This is an approximation based on common CSL boundaries in FCC/BCC metals.
    
    Args:
        misorientation_angle_deg: Misorientation angle in degrees
        
    Returns:
        Sigma value (integer) or -1 if no match found
    """
    # Define common CSL boundaries with their characteristic angles (approximate)
    # Format: (angle_deg, tolerance, sigma_value)
    csl_boundaries = [
        (60.0, 1.0, 3),      # Σ3 twin boundary
        (36.87, 1.0, 5),     # Σ5
        (38.94, 1.0, 9),     # Σ9
        (50.48, 1.0, 11),    # Σ11
        (27.80, 1.0, 13),    # Σ13
        (28.07, 1.0, 17),    # Σ17
        (26.53, 1.0, 19),    # Σ19
        (39.12, 1.0, 21),    # Σ21
        (36.87, 0.5, 25),    # Σ25 (different axis than Σ5)
        (43.61, 1.0, 27),    # Σ27
        (31.32, 1.0, 31),    # Σ31
        (32.21, 1.0, 33),    # Σ33
        (46.83, 1.0, 35),    # Σ35
        (40.21, 1.0, 37),    # Σ37
        (49.80, 1.0, 39),    # Σ39
        (42.56, 1.0, 41),    # Σ41
        (36.00, 1.0, 43),    # Σ43
        (33.22, 1.0, 45),    # Σ45
        (38.21, 1.0, 47),    # Σ47
    ]
    
    for angle, tolerance, sigma in csl_boundaries:
        if abs(misorientation_angle_deg - angle) <= tolerance:
            return sigma
    
    # If no exact match, return -1 to indicate non-CSL boundary
    return -1

def compute_mutual_information(data: pd.DataFrame, feature1: str, feature2: str) -> float:
    """
    Compute Mutual Information (MI) between two features.
    
    Args:
        data: DataFrame containing the features
        feature1: Name of first feature column
        feature2: Name of second feature column
        
    Returns:
        Mutual information value (float)
    """
    if feature1 not in data.columns or feature2 not in data.columns:
        raise ValueError(f"Features {feature1} or {feature2} not found in data")
    
    # Remove rows with missing values in either feature
    valid_data = data[[feature1, feature2]].dropna()
    
    if len(valid_data) < 2:
        logger.warning(f"Insufficient data points for MI calculation: {len(valid_data)}")
        return 0.0
    
    # Calculate MI using sklearn's mutual_info_regression
    # Reshape feature1 to 2D array as required by sklearn
    X = valid_data[feature1].values.reshape(-1, 1)
    y = valid_data[feature2].values
    
    mi = mutual_info_regression(X, y, random_state=42)
    return float(mi[0])

def run_collinearity_diagnostic(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run collinearity diagnostic on the dataset.
    
    Computes Mutual Information between misorientation angle and Σ value,
    logs warnings for strong dependencies, and saves results to a JSON file.
    
    Args:
        data_path: Path to the input dataset (Parquet or CSV)
        output_path: Path where the diagnostic JSON will be saved
        
    Returns:
        Dictionary containing diagnostic results
    """
    # Load data
    logger.info(f"Loading data from {data_path}")
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    elif data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path}")
    
    # Ensure required columns exist
    required_cols = ['misorientation_angle', 'sigma_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # Try to calculate sigma_value if it doesn't exist but misorientation_angle does
        if 'misorientation_angle' in df.columns and 'sigma_value' not in df.columns:
            logger.info("Calculating sigma_value from misorientation_angle")
            df['sigma_value'] = df['misorientation_angle'].apply(calculate_sigma_from_misorientation)
        else:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Compute Mutual Information
    logger.info("Computing Mutual Information between misorientation_angle and sigma_value")
    mi_value = compute_mutual_information(df, 'misorientation_angle', 'sigma_value')
    
    # Prepare results
    results = {
        "feature1": "misorientation_angle",
        "feature2": "sigma_value",
        "mutual_information": mi_value,
        "threshold_warning": mi_value > 0.8,
        "sample_size": len(df),
        "message": "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
    }
    
    # Log warning if strong dependency detected
    if mi_value > 0.8:
        logger.warning(f"MI > 0.8 indicates strong dependency; relationship is descriptive, not causal. MI = {mi_value:.4f}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Diagnostic results saved to {output_path}")
    
    return results

def main():
    """
    Main entry point for running collinearity diagnostics.
    """
    # Default paths - can be overridden by environment variables or command line args
    data_path = os.environ.get('DIAGNOSTIC_DATA_PATH', 'data/processed/parsed_geometry.parquet')
    output_path = os.environ.get('DIAGNOSTIC_OUTPUT_PATH', 'artifacts/reports/collinearity_diagnostic.json')
    
    # Check if data file exists
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please run T010 (geometry_parser) and T011 (preprocess) first to generate the dataset.")
        sys.exit(1)
    
    try:
        results = run_collinearity_diagnostic(data_path, output_path)
        logger.info("Collinearity diagnostic completed successfully")
        logger.info(f"Mutual Information: {results['mutual_information']:.4f}")
        
        if results['threshold_warning']:
            logger.warning(results['message'])
        
        return 0
    except Exception as e:
        logger.error(f"Error during collinearity diagnostic: {str(e)}")
        raise

if __name__ == "__main__":
    main()