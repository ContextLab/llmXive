import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from analyze_correlations import load_feature_matrix, compute_correlation_matrix, compute_variance_inflation_factors
from logger import get_logger
from config import get_paths

def calculate_collinearity_score(correlation_matrix: np.ndarray) -> float:
    """
    Calculate a scalar collinearity score based on the correlation matrix.
    Uses the maximum absolute off-diagonal correlation coefficient as the score.
    
    Args:
        correlation_matrix: Square numpy array of correlation coefficients.
        
    Returns:
        float: The maximum absolute correlation value (excluding diagonal).
    """
    n = correlation_matrix.shape[0]
    if n < 2:
        return 0.0
    
    # Create a mask for off-diagonal elements
    mask = ~np.eye(n, dtype=bool)
    off_diag = correlation_matrix[mask]
    
    if len(off_diag) == 0:
        return 0.0
        
    return float(np.max(np.abs(off_diag)))

def interpret_collinearity(score: float, threshold_high: float = 0.8, threshold_medium: float = 0.5) -> str:
    """
    Generate an interpretation string for the collinearity score.
    
    Args:
        score: The calculated collinearity score.
        threshold_high: Threshold for high collinearity.
        threshold_medium: Threshold for medium collinearity.
        
    Returns:
        str: Interpretation of the collinearity findings.
    """
    if score >= threshold_high:
        return (
            f"HIGH COLLINEARITY DETECTED (score={score:.3f}). "
            "Feature pairs show strong linear dependence (|r| >= 0.8). "
            "This may inflate variance in regression models and reduce interpretability. "
            "Consider feature selection, dimensionality reduction (PCA), or regularization."
        )
    elif score >= threshold_medium:
        return (
            f"MODERATE COLLINEARITY (score={score:.3f}). "
            "Some feature pairs show moderate linear dependence (0.5 <= |r| < 0.8). "
            "Monitor model stability; consider checking Variance Inflation Factors (VIF)."
        )
    else:
        return (
            f"LOW COLLINEARITY (score={score:.3f}). "
            "Features are largely independent (|r| < 0.5). "
            "Suitable for standard linear modeling without severe multicollinearity concerns."
        )

def run_collinearity_analysis(
    feature_matrix_path: Optional[str] = None,
    output_path: Optional[str] = None,
    metadata_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform collinearity analysis on the feature matrix and update metadata.
    
    Args:
        feature_matrix_path: Path to the features_matrix.csv. Defaults to config path.
        output_path: Path to save the collinearity report. Defaults to metadata_path.
        metadata_path: Path to the feature_metadata.json file to update.
        
    Returns:
        Dict containing the collinearity report.
    """
    logger = get_logger("collinearity_analysis")
    paths = get_paths()
    
    if feature_matrix_path is None:
        feature_matrix_path = str(paths["processed"] / "features_matrix.csv")
    if metadata_path is None:
        metadata_path = str(paths["processed"] / "feature_metadata.json")
    if output_path is None:
        output_path = metadata_path
        
    logger.info(f"Loading feature matrix from {feature_matrix_path}")
    
    # Load features
    try:
        X, feature_names = load_feature_matrix(feature_matrix_path)
    except FileNotFoundError:
        logger.error(f"Feature matrix not found at {feature_matrix_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load feature matrix: {e}")
        raise
        
    if X.shape[1] < 2:
        logger.warning("Less than 2 features found. Collinearity analysis not applicable.")
        report = {
            "collinearity_score": 0.0,
            "interpretation": "Insufficient features for collinearity analysis.",
            "feature_count": X.shape[1]
        }
        return report
    
    # Compute correlation matrix
    logger.info("Computing correlation matrix")
    corr_matrix = compute_correlation_matrix(X)
    
    # Compute VIFs if possible
    vifs = {}
    try:
        vifs = compute_variance_inflation_factors(X)
    except Exception as e:
        logger.warning(f"Could not compute VIFs: {e}")
    
    # Calculate score
    score = calculate_collinearity_score(corr_matrix)
    interpretation = interpret_collinearity(score)
    
    report = {
        "collinearity_score": score,
        "interpretation": interpretation,
        "max_correlation": score,
        "feature_count": X.shape[1],
        "sample_count": X.shape[0]
    }
    
    if vifs:
        report["vif_stats"] = {
            "mean": float(np.mean(list(vifs.values()))),
            "max": float(np.max(list(vifs.values())))
        }
    
    # Update metadata file
    logger.info(f"Updating metadata at {metadata_path}")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing metadata file is corrupted. Overwriting.")
            metadata = {}
    
    metadata["collinearity_report"] = report
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Collinearity analysis complete. Score: {score:.4f}")
    return report

def main():
    """Main entry point for the collinearity analysis task."""
    logger = get_logger("collinearity_analysis")
    logger.info("Starting T024b: Collinearity Analysis")
    
    try:
        report = run_collinearity_analysis()
        logger.info("T024b completed successfully.")
        print(json.dumps(report, indent=2))
        return 0
    except Exception as e:
        logger.error(f"T024b failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
