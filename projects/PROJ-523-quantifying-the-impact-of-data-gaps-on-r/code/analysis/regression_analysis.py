"""
Linear Regression Model for bias analysis with interaction terms.
Optimized for memory by using float32 for design matrices and results.
"""
import os
import sys
import csv
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from config import DATA_RESULTS_DIR, get_dtype, FORCE_FLOAT32

logger = logging.getLogger(__name__)

def load_bias_summary() -> List[Dict[str, Any]]:
    """
    Loads the bias summary CSV file.
    """
    path = DATA_RESULTS_DIR / "bias_summary.csv"
    if not path.exists():
        raise FileNotFoundError(f"Bias summary not found at {path}")
    
    results = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float32 if configured
            new_row = {}
            for k, v in row.items():
                try:
                    val = float(v)
                    if FORCE_FLOAT32:
                        new_row[k] = np.float32(val)
                    else:
                        new_row[k] = val
                except ValueError:
                    new_row[k] = v
            results.append(new_row)
    return results

def prepare_regression_data(data: List[Dict[str, Any]]) -> tuple:
    """
    Prepares data for regression: X (features) and y (target).
    Features: Gap Fraction, Algorithm (encoded), Morphology (encoded), interactions, quadratics.
    Target: Bias magnitude (e.g., bias_H0).
    """
    # Simplified feature extraction for demonstration
    # In a real scenario, we would parse algorithm and morphology from the data
    X = []
    y = []
    
    for row in data:
        # Extract gap fraction (assuming it's in the row or can be derived)
        # For this example, we assume 'gap_fraction' is a key
        gap_frac = row.get('gap_fraction', 0.0)
        
        # One-hot encode algorithm (simplified)
        algo = row.get('algorithm', 'unknown')
        algo_vec = [1.0 if algo == 'harmonic_interp' else 0.0,
                    1.0 if algo == 'wiener_filter' else 0.0,
                    1.0 if algo == 'iterative_synthesis' else 0.0]
        
        # Features: [gap_frac, gap_frac^2, algo1, algo2, algo3, gap_frac*algo1, ...]
        features = [
            float(gap_frac),
            float(gap_frac) ** 2,
            *algo_vec,
            float(gap_frac) * algo_vec[0], # Interaction
            float(gap_frac) * algo_vec[1],
            float(gap_frac) * algo_vec[2]
        ]
        
        if FORCE_FLOAT32:
            features = [np.float32(f) for f in features]
        
        X.append(features)
        
        # Target: bias_H0
        target = row.get('bias_H0', 0.0)
        if FORCE_FLOAT32:
            target = np.float32(target)
        y.append(target)
    
    return np.array(X, dtype=np.float32 if FORCE_FLOAT32 else np.float64), np.array(y, dtype=np.float32 if FORCE_FLOAT32 else np.float64)

def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Fits a linear regression model using least squares.
    """
    # Add intercept
    n_samples = X.shape[0]
    X_with_intercept = np.hstack([np.ones((n_samples, 1), dtype=X.dtype), X])
    
    # Solve (X^T X)^-1 X^T y
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
    except np.linalg.LinAlgError:
        logger.error("Linear algebra error during regression fit.")
        return {}
    
    result = {
        "coefficients": coeffs.tolist(),
        "residuals": residuals.tolist() if len(residuals) > 0 else [],
        "rank": int(rank),
        "singular_values": s.tolist() if len(s) > 0 else []
    }
    
    if FORCE_FLOAT32:
        result["coefficients"] = [np.float32(c) for c in result["coefficients"]]
    
    return result

def save_regression_results(results: Dict[str, Any], filepath: Path):
    """
    Saves regression results to a CSV/JSON file.
    """
    # Convert to JSON for simplicity
    import json
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Regression results saved to {filepath}")

def run_regression_analysis():
    """
    Runs the full regression analysis pipeline.
    """
    logger.info("Starting regression analysis...")
    
    data = load_bias_summary()
    X, y = prepare_regression_data(data)
    
    if X.shape[0] == 0:
        logger.warning("No data for regression.")
        return
    
    results = fit_linear_regression(X, y)
    
    output_path = DATA_RESULTS_DIR / "regression_results.json"
    save_regression_results(results, output_path)
    
    logger.info("Regression analysis completed.")

def main():
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.INFO)
    run_regression_analysis()

if __name__ == "__main__":
    main()
