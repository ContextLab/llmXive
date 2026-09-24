import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Attempt to import numpy/pandas for potential future analysis,
# but the core logic here is deterministic based on input p-values.
try:
    import pandas as pd
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("numpy/pandas not available; sensitivity analysis will rely on raw input counts.")

def setup_logger_module(name: str = "sensitivity_analysis", level: int = logging.INFO) -> logging.Logger:
    """
    Setup a module-level logger.
    
    Args:
        name: Logger name.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def run_sensitivity_analysis(p_values: List[float], threshold_values: List[float] = None) -> Dict[str, Dict[str, Union[int, float]]]:
    """
    Perform p-value threshold sensitivity analysis.
    
    Calculates the rate and count of significant results for each specified threshold.
    'Significant' is defined as p_value < threshold.
    
    Args:
        p_values: List of observed p-values from the correlation/regression analysis.
        threshold_values: List of significance thresholds to test (e.g., [0.01, 0.05, 0.1]).
                        If None, defaults to [0.01, 0.05, 0.1].
                        
    Returns:
        Dictionary with keys as stringified thresholds and values containing 'rate' and 'count'.
    """
    if not p_values:
        raise ValueError("Input list of p-values cannot be empty.")
    
    if threshold_values is None:
        threshold_values = [0.01, 0.05, 0.1]
        
    total_count = len(p_values)
    results = {}
    
    logger = setup_logger_module()
    logger.info(f"Running sensitivity analysis on {total_count} p-values against thresholds: {threshold_values}")
    
    for threshold in threshold_values:
        # Count how many p-values are strictly less than the threshold
        significant_count = sum(1 for p in p_values if p < threshold)
        rate = significant_count / total_count if total_count > 0 else 0.0
        
        # Format key as string to match JSON requirements
        key = f"{threshold}"
        results[key] = {
            "count": significant_count,
            "rate": round(rate, 4)
        }
        
        logger.info(f"Threshold {threshold}: {significant_count} significant out of {total_count} (rate: {rate:.4f})")
        
    return results

def save_sensitivity_report(results: Dict[str, Dict[str, Union[int, float]]], output_path: Union[str, Path]) -> None:
    """
    Save the sensitivity analysis results to a JSON file.
    
    Args:
        results: Dictionary of analysis results.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logging.info(f"Sensitivity report saved to {output_path}")

def main():
    """
    CLI entry point for sensitivity analysis.
    Expects --p-values as a space-separated list of floats.
    """
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on p-values.")
    parser.add_argument(
        "--p-values", 
        type=float, 
        nargs='+', 
        required=True, 
        help="Space-separated list of p-values to analyze."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/sensitivity_analysis.json",
        help="Output path for the JSON report."
    )
    
    args = parser.parse_args()
    
    logger = setup_logger_module()
    logger.info(f"Processing {len(args.p_values)} p-values.")
    
    try:
        results = run_sensitivity_analysis(args.p_values)
        save_sensitivity_report(results, args.output)
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Failed to run sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()