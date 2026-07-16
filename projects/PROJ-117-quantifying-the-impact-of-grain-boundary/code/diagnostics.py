import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.preprocessing import KBinsDiscretizer

# Import project utilities
from utils import setup_logging, load_metadata
from error_handling import DataInsufficiencyError

# Configure logging
logger = setup_logging("diagnostics")

def calculate_sigma_from_misorientation(misorientation_angle: float) -> float:
    """
    Calculate Sigma (Σ) value from misorientation angle for simple cubic/lattice systems.
    Note: This is a simplified heuristic. For rigorous CSL calculation, use pymatgen.
    However, for diagnostic purposes on scalar angles, we use the standard approximation:
    Σ ≈ 1 / (1 - cos(θ/2)) for low angles, but typically Σ is an integer derived from
    specific coincidence site lattice conditions.
    
    For this diagnostic, if the angle doesn't map cleanly to a known low-Σ CSL,
    we return NaN to indicate the value is not strictly available/valid for that specific
    geometric configuration without full lattice matching.
    """
    if np.isnan(misorientation_angle) or misorientation_angle <= 0:
        return np.nan
    
    # Common low-angle CSL boundaries (approximate thresholds for simple cubic)
    # This is a heuristic fallback if explicit calculation failed in T010
    # Real implementation in T010 should have used pymatgen CSL.
    # Here we just check if it's a "valid" integer Σ candidate based on angle.
    # Since we don't have the full lattice here, we return NaN if not obvious.
    # The task requires computing it in T010, so this function is mostly for
    # fallback or verification. If T010 already computed it, this is redundant.
    # We will rely on the 'sigma_value' column from the dataset.
    return np.nan

def compute_mutual_information(x: np.ndarray, y: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Mutual Information (MI) between two 1D arrays.
    Since sklearn's mutual_info_regression is for continuous targets and
    mutual_info_classif is for discrete, and we are checking dependency
    between two continuous/semi-continuous features (angle and Sigma),
    we discretize both using KBinsDiscretizer and calculate MI manually.
    
    MI(X; Y) = Sum p(x,y) * log(p(x,y) / (p(x)*p(y)))
    """
    if len(x) == 0 or len(y) == 0:
        return 0.0
    
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")
    
    # Discretize continuous variables
    discretizer = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='uniform')
    
    try:
        x_disc = discretizer.fit_transform(x.reshape(-1, 1)).flatten()
        y_disc = discretizer.fit_transform(y.reshape(-1, 1)).flatten()
    except ValueError:
        # If all values are identical, MI is 0
        return 0.0
    
    # Compute joint probability distribution
    # Create a 2D histogram
    joint_counts, _, _ = np.histogram2d(x_disc, y_disc, bins=n_bins)
    joint_prob = joint_counts / np.sum(joint_counts)
    
    # Marginal probabilities
    p_x = np.sum(joint_prob, axis=1)
    p_y = np.sum(joint_prob, axis=0)
    
    # Avoid log(0)
    joint_prob = joint_prob[joint_prob > 0]
    p_x = p_x[p_x > 0]
    p_y = p_y[p_y > 0]
    
    # Calculate MI
    mi = np.sum(joint_prob * np.log(joint_prob / (np.outer(p_x, p_y)[joint_prob > 0])))
    
    return float(mi)

def run_collinearity_diagnostic(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Compute Mutual Information between misorientation angle and Σ value.
    
    Args:
        data_path: Path to the cleaned dataset (parquet).
        output_path: Path to write the diagnostic JSON report.
        
    Returns:
        Dictionary containing the diagnostic results.
    """
    logger.info(f"Loading dataset from {data_path}")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset file not found: {data_path}. "
                                "Ensure T011 (preprocess) has run successfully.")
    
    df = pd.read_parquet(data_path)
    
    required_cols = ['misorientation_angle', 'sigma_value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Filter for valid sigma values (non-NaN)
    valid_mask = df['sigma_value'].notna()
    valid_count = valid_mask.sum()
    total_count = len(df)
    
    result: Dict[str, Any] = {}
    
    if valid_count == 0:
        logger.warning("No valid Σ values found in the dataset after preprocessing.")
        result = {
            "status": "unavailable",
            "message": "No valid Σ values in dataset after preprocessing.",
            "count": int(total_count),
            "mutual_information": None,
            "interpretation": "Cannot compute MI without valid Σ values."
        }
    else:
        logger.info(f"Computing MI for {valid_count} records with valid Σ values.")
        
        misorientation = df.loc[valid_mask, 'misorientation_angle'].to_numpy()
        sigma = df.loc[valid_mask, 'sigma_value'].to_numpy()
        
        # Handle cases where all values are identical (MI undefined/0)
        if len(np.unique(misorientation)) < 2 or len(np.unique(sigma)) < 2:
            mi_value = 0.0
            logger.warning("Low variance in features; MI set to 0.0.")
        else:
            mi_value = compute_mutual_information(misorientation, sigma)
        
        logger.info(f"Calculated Mutual Information: {mi_value:.4f}")
        
        # Interpretation logic
        if mi_value > 0.8:
            interpretation = "Strong dependency detected. Relationship is descriptive, not causal."
        elif mi_value > 0.4:
            interpretation = "Moderate dependency detected. Relationship is descriptive, not causal."
        else:
            interpretation = "Weak or no dependency detected. Relationship is descriptive, not causal."
        
        result = {
            "status": "computed",
            "total_records": int(total_count),
            "valid_sigma_count": int(valid_count),
            "mutual_information": float(mi_value),
            "interpretation": interpretation,
            "note": "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal.",
            "fr007_framing": "The relationship between misorientation and Σ value is descriptive, not causal, as Σ is derived from misorientation."
        }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Diagnostic report written to {output_path}")
    return result

def main():
    """Main entry point for the diagnostics script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "processed" / "cleaned_dataset.parquet"
    output_path = project_root / "artifacts" / "reports" / "collinearity_diagnostic.json"
    
    try:
        run_collinearity_diagnostic(str(data_path), str(output_path))
        logger.info("Diagnostics completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during diagnostics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()