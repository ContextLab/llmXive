"""
Robustness checks for the exoplanet atmosphere analysis pipeline.

This module implements robustness checks on the statistical results,
specifically calculating confidence interval widths for both the
water mixing ratio distribution and the Kendall's tau coefficient.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_retrieval_results(input_path: Path) -> np.ndarray:
    """
    Load the water mixing ratio samples from the bootstrap analysis.
    
    Args:
        input_path: Path to the .npy file containing mixing ratio samples.
        
    Returns:
        numpy array of mixing ratio samples.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {input_path}")
    
    logger.info(f"Loading retrieval results from {input_path}")
    try:
        data = np.load(input_path, allow_pickle=True)
        if isinstance(data, np.ndarray) and data.ndim == 0:
            # Handle case where it might be a scalar or single value
            return np.array([data.item()])
        return data.flatten()
    except Exception as e:
        logger.error(f"Failed to load retrieval results: {e}")
        raise

def load_bootstrap_ci(input_path: Path) -> Tuple[float, float]:
    """
    Load the bootstrap confidence interval for Kendall's tau.
    
    Args:
        input_path: Path to the JSON file containing bootstrap CI data.
        
    Returns:
        Tuple of (ci_lower, ci_upper) for the tau coefficient.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Bootstrap CI file not found: {input_path}")
    
    logger.info(f"Loading bootstrap CI from {input_path}")
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        ci_lower = data.get('ci_lower')
        ci_upper = data.get('ci_upper')
        
        if ci_lower is None or ci_upper is None:
            raise ValueError("Bootstrap CI file missing 'ci_lower' or 'ci_upper' keys")
            
        return float(ci_lower), float(ci_upper)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse bootstrap CI JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load bootstrap CI: {e}")
        raise

def compute_ci_width_variable(mixing_ratios: np.ndarray) -> float:
    """
    Calculate the 95% CI width of the water mixing ratio distribution.
    
    This is derived from the bootstrapped mixing ratio samples.
    
    Args:
        mixing_ratios: Array of bootstrapped mixing ratio values.
        
    Returns:
        Width of the 95% confidence interval.
    """
    if len(mixing_ratios) == 0:
        raise ValueError("Cannot compute CI width from empty array")
        
    # Calculate 2.5th and 97.5th percentiles for 95% CI
    ci_lower = np.percentile(mixing_ratios, 2.5)
    ci_upper = np.percentile(mixing_ratios, 97.5)
    
    width = ci_upper - ci_lower
    logger.info(f"Mixing ratio 95% CI: [{ci_lower:.6f}, {ci_upper:.6f}], width: {width:.6f}")
    return width

def compute_ci_width_tau(ci_lower: float, ci_upper: float) -> float:
    """
    Calculate the 95% CI width of the Kendall's tau coefficient.
    
    Args:
        ci_lower: Lower bound of the 95% CI for tau.
        ci_upper: Upper bound of the 95% CI for tau.
        
    Returns:
        Width of the 95% confidence interval for tau.
    """
    width = ci_upper - ci_lower
    logger.info(f"Tau 95% CI: [{ci_lower:.6f}, {ci_upper:.6f}], width: {width:.6f}")
    return width

def determine_threshold_met(ci_width: float, threshold: float = 0.2) -> bool:
    """
    Determine if the CI width meets the robustness threshold.
    
    Args:
        ci_width: The calculated confidence interval width.
        threshold: The maximum acceptable width (default 0.2 dex).
        
    Returns:
        Boolean indicating if width <= threshold.
    """
    met = ci_width <= threshold
    status = "PASSED" if met else "FAILED"
    logger.info(f"Robustness check {status}: CI width {ci_width:.4f} vs threshold {threshold}")
    return met

def save_robustness_report_tau(output_path: Path, ci_width_tau: float, threshold_met: bool) -> None:
    """
    Save the robustness report for the Kendall's tau coefficient.
    
    Args:
        output_path: Path where the JSON report will be saved.
        ci_width_tau: The calculated CI width for tau.
        threshold_met: Boolean indicating if the threshold was met.
    """
    report = {
        "ci_width_tau": ci_width_tau,
        "threshold_met": threshold_met
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved robustness report (Tau) to {output_path}")

def main() -> None:
    """
    Main entry point for the robustness check (Tau) task.
    
    This function:
    1. Loads the bootstrap CI data for Kendall's tau.
    2. Calculates the CI width.
    3. Checks against the threshold (0.2).
    4. Saves the report to results/robustness_report_tau.json.
    """
    config = get_config()
    setup_logging(config)
    
    # Define paths
    bootstrap_ci_path = config.data_processed_dir / "bootstrap_ci.json"
    output_path = config.results_dir / "robustness_report_tau.json"
    
    logger.info("Starting robustness check for Kendall's tau coefficient")
    
    try:
        # Load bootstrap CI for tau
        ci_lower, ci_upper = load_bootstrap_ci(bootstrap_ci_path)
        
        # Calculate CI width
        ci_width_tau = compute_ci_width_tau(ci_lower, ci_upper)
        
        # Check threshold
        threshold_met = determine_threshold_met(ci_width_tau, threshold=0.2)
        
        # Save report
        save_robustness_report_tau(output_path, ci_width_tau, threshold_met)
        
        logger.info("Robustness check (Tau) completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data in input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during robustness check: {e}")
        raise

if __name__ == "__main__":
    main()