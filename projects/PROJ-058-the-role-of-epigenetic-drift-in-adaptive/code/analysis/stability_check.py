"""
Stability check for sensitivity analysis results.

Implements the logic to flag results if:
1. Correlation remains significant (p < 0.05) in < 2 of 3 thresholds.
2. |Δrho| > 0.1 across the thresholds.

Dependency: Requires T023 (converged p-values) for empirical p-values.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_env, ensure_directories

# Constants
SIGNIFICANCE_THRESHOLD = 0.05
RHO_DIFF_THRESHOLD = 0.1
MIN_SIGNIFICANT_COUNT = 2
THRESHOLD_VALUES = [3, 4, 5]

logger = logging.getLogger(__name__)


def load_sensitivity_results(input_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load sensitivity analysis results from the default or specified path.
    
    Args:
        input_path: Path to the sensitivity results JSON file. Defaults to 
                   output/sensitivity_results.json if not provided.
                   
    Returns:
        Dictionary containing sensitivity sweep results.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = get_env("SENSITIVITY_RESULTS_PATH", "output/sensitivity_results.json")
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results file not found: {input_path}")
    
    with open(path, 'r') as f:
        return json.load(f)


def check_significance_count(results: Dict[str, Any]) -> Tuple[int, List[bool]]:
    """
    Count how many thresholds have significant correlation (p < 0.05).
    
    Args:
        results: Dictionary containing sensitivity sweep results with 'thresholds' key.
                
    Returns:
        Tuple of (count of significant thresholds, list of boolean significance flags).
    """
    thresholds_data = results.get("thresholds", [])
    significant_flags = []
    
    for entry in thresholds_data:
        p_value = entry.get("p_value")
        if p_value is not None:
            is_sig = p_value < SIGNIFICANCE_THRESHOLD
            significant_flags.append(is_sig)
        else:
            # If p-value is missing, treat as not significant
            significant_flags.append(False)
            
    return sum(significant_flags), significant_flags


def calculate_max_rho_diff(results: Dict[str, Any]) -> float:
    """
    Calculate the maximum absolute difference in rho between any two thresholds.
    
    Args:
        results: Dictionary containing sensitivity sweep results with 'thresholds' key.
                
    Returns:
        Maximum absolute difference in rho values.
    """
    thresholds_data = results.get("thresholds", [])
    rho_values = [entry.get("rho") for entry in thresholds_data if entry.get("rho") is not None]
    
    if len(rho_values) < 2:
        return 0.0
        
    max_diff = 0.0
    for i in range(len(rho_values)):
        for j in range(i + 1, len(rho_values)):
            diff = abs(rho_values[i] - rho_values[j])
            if diff > max_diff:
                max_diff = diff
                
    return max_diff


def perform_stability_check(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform the stability check on sensitivity results.
    
    Flags the result if:
    1. Correlation remains significant (p < 0.05) in < 2 of 3 thresholds.
    2. |Δrho| > 0.1 across the thresholds.
    
    Args:
        results: Dictionary containing sensitivity sweep results.
                
    Returns:
        Dictionary with stability check results including flags and status.
    """
    significant_count, significant_flags = check_significance_count(results)
    max_rho_diff = calculate_max_rho_diff(results)
    
    # Condition 1: Significant in < 2 of 3 thresholds
    significance_stable = significant_count >= MIN_SIGNIFICANT_COUNT
    
    # Condition 2: |Δrho| <= 0.1
    rho_stable = max_rho_diff <= RHO_DIFF_THRESHOLD
    
    # Overall stability: both conditions must be met
    is_stable = significance_stable and rho_stable
    
    stability_result = {
        "stability_check": {
            "significant_count": significant_count,
            "total_thresholds": len(THRESHOLD_VALUES),
            "max_rho_diff": round(max_rho_diff, 4),
            "significance_stable": significance_stable,
            "rho_stable": rho_stable,
            "is_stable": is_stable,
            "status": "STABLE" if is_stable else "UNSTABLE",
            "flags": {
                "insufficient_significance": not significance_stable,
                "high_rho_variation": not rho_stable
            }
        },
        "threshold_details": []
    }
    
    # Add details for each threshold
    for i, entry in enumerate(results.get("thresholds", [])):
        threshold_val = entry.get("threshold")
        p_value = entry.get("p_value")
        rho = entry.get("rho")
        is_sig = p_value < SIGNIFICANT_THRESHOLD if p_value is not None else False
        
        stability_result["threshold_details"].append({
            "threshold": threshold_val,
            "rho": rho,
            "p_value": p_value,
            "significant": is_sig
        })
    
    return stability_result


def save_results(stability_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save stability check results to a JSON file.
    
    Args:
        stability_result: Dictionary containing stability check results.
        output_path: Path for the output file. Defaults to 
                   output/stability_check_results.json if not provided.
                   
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_env("STABILITY_RESULTS_PATH", "output/stability_check_results.json")
    
    path = Path(output_path)
    ensure_directories([path.parent])
    
    with open(path, 'w') as f:
        json.dump(stability_result, f, indent=2)
        
    logger.info(f"Stability check results saved to {output_path}")
    return str(path)


def run_stability_analysis(input_path: Optional[str] = None, 
                           output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete stability analysis pipeline.
    
    Args:
        input_path: Path to sensitivity results JSON.
        output_path: Path for stability check results JSON.
                    
    Returns:
        Dictionary containing stability check results.
    """
    logger.info("Loading sensitivity analysis results...")
    sensitivity_results = load_sensitivity_results(input_path)
    
    logger.info("Performing stability check...")
    stability_result = perform_stability_check(sensitivity_results)
    
    logger.info(f"Stability status: {stability_result['stability_check']['status']}")
    
    saved_path = save_results(stability_result, output_path)
    
    return stability_result


def main():
    """Main entry point for the stability check script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/stability_check.log')
        ]
    )
    
    logger.info("Starting stability check for sensitivity analysis...")
    
    try:
        # Get paths from environment or use defaults
        input_path = get_env("SENSITIVITY_RESULTS_PATH", "output/sensitivity_results.json")
        output_path = get_env("STABILITY_RESULTS_PATH", "output/stability_check_results.json")
        
        results = run_stability_analysis(input_path, output_path)
        
        # Print summary
        check = results["stability_check"]
        print(f"\n{'='*50}")
        print(f"STABILITY CHECK SUMMARY")
        print(f"{'='*50}")
        print(f"Status: {check['status']}")
        print(f"Significant thresholds: {check['significant_count']}/{check['total_thresholds']}")
        print(f"Max |Δrho|: {check['max_rho_diff']:.4f}")
        print(f"Significance stable: {check['significance_stable']}")
        print(f"Rho stable: {check['rho_stable']}")
        
        if not check['significance_stable']:
            print(f"⚠ WARNING: Correlation significant in < {MIN_SIGNIFICANT_COUNT} of {check['total_thresholds']} thresholds")
        if not check['rho_stable']:
            print(f"⚠ WARNING: |Δrho| > {RHO_DIFF_THRESHOLD}")
            
        print(f"{'='*50}\n")
        
        sys.exit(0 if check['is_stable'] else 1)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"ERROR: {e}")
        print("Make sure sensitivity analysis has been run first (T028, T029).")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during stability check: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
