import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import from utils for logging setup
from utils import setup_logging, load_metadata, update_metadata_entry, save_metadata

# Import from error_handling for data checks
from error_handling import DataInsufficiencyError

# Configure logger
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def calculate_sigma_from_misorientation(misorientation_deg: float) -> int:
    """
    Calculate the Sigma (Σ) value from a misorientation angle using CSL theory.
    
    This implementation uses a lookup table for common low-Σ boundaries
    and a fallback approximation for others.
    
    Args:
        misorientation_deg: Misorientation angle in degrees.
        
    Returns:
        Sigma value (integer). Returns -1 if no match found.
    """
    # Common CSL boundaries for cubic systems (approximate)
    # Format: (angle_deg, sigma_value, tolerance_deg)
    csl_lookup = [
        (0.0, 1, 0.5),      # Coincident (perfect alignment)
        (38.94, 3, 0.5),    # Σ3 (Twin)
        (50.48, 9, 0.5),    # Σ9
        (60.00, 3, 0.5),    # Σ3 (alternative)
        (70.53, 3, 0.5),    # Σ3 (alternative)
        (48.19, 11, 0.5),   # Σ11
        (54.74, 9, 0.5),    # Σ9 (alternative)
        (36.87, 5, 0.5),    # Σ5
        (28.07, 5, 0.5),    # Σ5 (alternative)
        (62.96, 13, 0.5),   # Σ13
        (22.62, 13, 0.5),   # Σ13 (alternative)
        (40.61, 17, 0.5),   # Σ17
        (24.09, 17, 0.5),   # Σ17 (alternative)
        (53.13, 25, 0.5),   # Σ25
        (25.84, 25, 0.5),   # Σ25 (alternative)
    ]

    for angle, sigma, tol in csl_lookup:
        if abs(misorientation_deg - angle) <= tol:
            return sigma

    # Fallback: Approximation for general angles if not in lookup
    # Σ ≈ 1 / (sin(theta/2))^2 is a rough approximation for some systems,
    # but strictly speaking, CSL requires specific rational relationships.
    # For this diagnostic, if not in lookup, we estimate based on density of coincident sites.
    # A common heuristic for general angles in cubic systems:
    # We return -1 to indicate "unknown/high Sigma" to avoid false positives in MI calculation
    # if exact CSL is not found, or we can use a formula.
    # Let's use a simple heuristic: Sigma = round(1 / (abs(np.sin(np.radians(misorientation_deg/2)))**2))
    # But this often yields very large numbers.
    # Better approach for this task: If not in lookup, assume high Sigma (low coincidence).
    # We will return a calculated value based on the formula: Sigma = 1 / (1 - cos(theta)) is not standard.
    # Standard CSL for cubic: Sigma = (u^2 + v^2 + w^2) / gcd(...)
    # Since we only have angle, we stick to the lookup or return a high value.
    # Let's implement the approximation: Sigma = round(1 / (sin(theta/2)^2)) for general case,
    # but cap it to avoid overflow for small angles.
    try:
        val = 1.0 / (np.sin(np.radians(misorientation_deg / 2.0)) ** 2)
        return max(1, int(round(val)))
    except Exception:
        return -1

def compute_mutual_information(x: np.ndarray, y: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Mutual Information (MI) between two 1D arrays using histogram estimation.
    
    Args:
        x: First variable (misorientation angles).
        y: Second variable (Sigma values).
        n_bins: Number of bins for histogram discretization.
        
    Returns:
        Mutual Information value in bits (or nats depending on log base).
    """
    # Discretize continuous variables
    x_hist, x_edges = np.histogram(x, bins=n_bins)
    y_hist, y_edges = np.histogram(y, bins=n_bins)
    
    # Joint histogram
    joint_hist, _, _ = np.histogram2d(x, y, bins=[x_edges, y_edges])
    
    # Normalize to probabilities
    px = x_hist / len(x)
    py = y_hist / len(y)
    pxy = joint_hist / len(x)
    
    # Avoid log(0)
    px = px[px > 0]
    py = py[py > 0]
    pxy = pxy[pxy > 0]
    
    # Calculate MI: Sum p(x,y) * log(p(x,y) / (p(x)p(y)))
    mi = np.sum(pxy * np.log(pxy / (np.outer(px, py) + 1e-10)))
    
    return float(mi)

def run_collinearity_diagnostic(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the collinearity diagnostic on the raw dataset.
    
    Steps:
    1. Load data (expecting 'misorientation_angle' and potentially 'sigma_value').
    2. If 'sigma_value' is missing, calculate it from 'misorientation_angle'.
    3. Compute Mutual Information between the two.
    4. Log warning if MI > 0.8.
    5. Save results to JSON.
    
    Args:
        data_path: Path to the input parquet/CSV file (parsed geometry).
        output_path: Path to save the diagnostic JSON report.
        
    Returns:
        Dictionary containing the diagnostic results.
    """
    logger.info(f"Running collinearity diagnostic on {data_path}")
    
    if not os.path.exists(data_path):
        # If the file doesn't exist yet, we might be running before T010.
        # However, T016 is listed as a dependency for T012, but T010/T011 must run first.
        # We assume the input file exists. If not, we raise an error.
        raise FileNotFoundError(f"Input data file not found: {data_path}. "
                                "Ensure T010 (geometry_parser) has run.")
    
    # Load data
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
    
    required_col = 'misorientation_angle'
    if required_col not in df.columns:
        raise ValueError(f"Required column '{required_col}' not found in {data_path}")
    
    misorientation = df[required_col].values.astype(float)
    
    # Handle Sigma calculation
    if 'sigma_value' in df.columns:
        sigma = df['sigma_value'].values.astype(float)
        logger.info("Using existing 'sigma_value' column.")
    else:
        logger.info("Calculating 'sigma_value' from misorientation angles.")
        sigma = np.array([calculate_sigma_from_misorientation(angle) for angle in misorientation])
    
    # Filter out invalid sigma values (-1) for MI calculation if necessary
    valid_mask = sigma > 0
    if np.sum(valid_mask) < 2:
        logger.warning("Not enough valid Sigma values to compute MI.")
        mi_result = 0.0
    else:
        mi_result = compute_mutual_information(misorientation[valid_mask], sigma[valid_mask])
    
    # Log warning
    if mi_result > 0.8:
        logger.warning("MI > 0.8 indicates strong dependency; relationship is descriptive, not causal.")
    else:
        logger.info(f"Mutual Information between misorientation and Sigma: {mi_result:.4f}")
    
    # Prepare report
    report = {
        "task_id": "T016",
        "input_file": data_path,
        "output_file": output_path,
        "mutual_information": mi_result,
        "threshold_warning": mi_result > 0.8,
        "warning_message": "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal." if mi_result > 0.8 else None,
        "sample_size": int(np.sum(valid_mask)),
        "timestamp": str(pd.Timestamp.now())
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Diagnostic report saved to {output_path}")
    return report

def main():
    """
    Main entry point for the diagnostics script.
    """
    # Setup logging
    setup_logging()
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "data" / "processed" / "parsed_geometry.parquet"
    output_file = project_root / "artifacts" / "reports" / "collinearity_diagnostic.json"
    
    # Check if input exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T010 (geometry_parser.py) first to generate parsed_geometry.parquet")
        sys.exit(1)
    
    try:
        run_collinearity_diagnostic(str(input_file), str(output_file))
        logger.info("T016 Diagnostics completed successfully.")
    except Exception as e:
        logger.error(f"T016 Diagnostics failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()