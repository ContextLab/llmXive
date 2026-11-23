import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def load_gradient_norms(path: str) -> Dict[str, Any]:
    """
    Load gradient norms from a JSON file.
    
    Args:
        path: Path to the JSON file containing gradient norms.
        
    Returns:
        Dictionary containing the gradient norms data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Gradient norms file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if "steps" not in data or len(data["steps"]) == 0:
        raise ValueError(f"Gradient norms file is empty or malformed: {path}")
    
    return data

def compare_gradient_stability(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Perform statistical test for gradient stability (T032).
    
    Logic:
    1. Load gradient norms from input_path (produced by T012b).
    2. Calculate mean and standard deviation of gradient norms.
    3. Determine stability based on coefficient of variation (std/mean).
       - Stable if std < 0.2 * mean (CV < 20%)
    4. Write results to output_path with schema:
       {"mean_norm": float, "std_norm": float, "is_stable": bool}
    
    Args:
        input_path: Path to gradient_norms.json (baseline).
        output_path: Path to write gradient_stability_baseline.json.
        
    Returns:
        Dictionary with stability metrics.
    """
    data = load_gradient_norms(input_path)
    
    # Extract norms
    norms = np.array([step["norm"] for step in data["steps"]])
    
    if len(norms) == 0:
        raise ValueError("No gradient norms found in input file")
    
    mean_norm = float(np.mean(norms))
    std_norm = float(np.std(norms))
    
    # Stability criterion: coefficient of variation < 20%
    is_stable = std_norm < (0.2 * mean_norm)
    
    result = {
        "mean_norm": round(mean_norm, 6),
        "std_norm": round(std_norm, 6),
        "is_stable": is_stable
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Gradient stability analysis complete: mean={mean_norm:.4f}, "
               f"std={std_norm:.4f}, stable={is_stable}")
    
    return result

def compare_ablation_results(full_mae: float, ablated_mae: float) -> Dict[str, Any]:
    """
    Compare ablation results using paired t-test logic.
    
    Args:
        full_mae: MAE of the full model.
        ablated_mae: MAE of the ablated model.
        
    Returns:
        Dictionary with comparison metrics.
    """
    mae_diff = ablated_mae - full_mae
    # Simplified significance check (in real implementation, would use sample data)
    significant = mae_diff > 0.01  # Placeholder threshold
    
    return {
        "full_mae": full_mae,
        "ablated_mae": ablated_mae,
        "mae_diff": mae_diff,
        "significant": significant
    }

def calculate_scaling_exponent(params_list: List[int], mae_list: List[float]) -> Dict[str, Any]:
    """
    Calculate scaling exponent from parameters and MAE.
    
    Args:
        params_list: List of parameter counts.
        mae_list: List of corresponding MAE values.
        
    Returns:
        Dictionary with exponent and fit quality.
    """
    log_params = np.log(params_list)
    log_mae = np.log(mae_list)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_mae)
    
    return {
        "exponent": float(slope),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value)
    }

def main():
    """CLI entry point for statistics module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistics utilities for experiments")
    parser.add_argument("--input", type=str, required=True, help="Input gradient norms file")
    parser.add_argument("--output", type=str, required=True, help="Output stability results file")
    
    args = parser.parse_args()
    
    result = compare_gradient_stability(args.input, args.output)
    print(f"Results: {result}")

if __name__ == "__main__":
    main()
