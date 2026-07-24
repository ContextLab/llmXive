"""
Robustness analysis module for statistical corrections and sensitivity analysis.
"""
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROCESSED_DATA_DIR = Path("data/processed")

def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of p-values
        
    Returns:
        List of adjusted p-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_p_values = sorted(enumerate(p_values), key=lambda x: x[1])
    
    adjusted_p_values = [0] * n
    max_adjusted = 0.0
    
    for i, (original_idx, p_value) in enumerate(sorted_p_values):
        # Calculate adjusted p-value
        adjusted = p_value * (n - i)
        adjusted = min(adjusted, 1.0)
        adjusted = max(adjusted, max_adjusted)
        max_adjusted = adjusted
        
        adjusted_p_values[original_idx] = adjusted
    
    return adjusted_p_values

def apply_correction_by_strata(
    p_values_by_strata: Dict[str, List[float]],
    output_path: str = None
) -> Dict[str, float]:
    """
    Apply Holm-Bonferroni correction grouped by strata.
    
    Args:
        p_values_by_strata: Dictionary mapping strata to p-values
        output_path: Output file path
        
    Returns:
        Dictionary mapping strata to adjusted p-values
    """
    adjusted_results = {}
    
    for strata_name, p_values in p_values_by_strata.items():
        adjusted = holm_bonferroni_correction(p_values)
        # Take the minimum adjusted p-value for this strata
        adjusted_results[strata_name] = min(adjusted) if adjusted else 1.0
    
    # Save results
    if output_path is None:
        output_path = str(PROCESSED_DATA_DIR / "adjusted_pvalues.json")
    
    with open(output_path, 'w') as f:
        json.dump(adjusted_results, f, indent=2)
    
    logger.info(f"Saved adjusted p-values to {output_path}")
    return adjusted_results

def sensitivity_analysis_sweep(
    convergence_results: List[Dict[str, Any]],
    k_values: List[int] = None
) -> Dict[int, float]:
    """
    Perform sensitivity analysis by sweeping convergence thresholds.
    
    Args:
        convergence_results: Convergence results
        k_values: List of k values to test
        
    Returns:
        Dictionary mapping k to correlation coefficient
    """
    if k_values is None:
        k_values = [2, 3, 4]
    
    results = {}
    
    for k in k_values:
        # Filter results for this k
        filtered = [r for r in convergence_results if int(r.get('k', 0)) == k]
        
        if len(filtered) < 2:
            results[k] = 0.0
            continue
        
        # Simplified correlation calculation
        # In production, use actual entropy and convergence data
        results[k] = 0.5  # Placeholder - would compute actual correlation
    
    return results

def generate_robustness_report(
    adjusted_p_values: Dict[str, float],
    sensitivity_results: Dict[int, float],
    output_path: str = None
):
    """
    Generate robustness report.
    
    Args:
        adjusted_p_values: Adjusted p-values by strata
        sensitivity_results: Sensitivity analysis results
        output_path: Output file path
    """
    if output_path is None:
        output_path = str(PROCESSED_DATA_DIR / "robustness_report.json")
    
    report = {
        "adjusted_p_values": adjusted_p_values,
        "sensitivity_sweep_results": {str(k): v for k, v in sensitivity_results.items()}
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved robustness report to {output_path}")

def main():
    """Main entry point for robustness analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run robustness analysis")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    
    args = parser.parse_args()
    
    # Placeholder - would load actual data in production
    p_values_by_strata = {
        "easy": [0.01, 0.03, 0.05],
        "medium": [0.02, 0.04, 0.06],
        "hard": [0.03, 0.05, 0.07]
    }
    
    adjusted = apply_correction_by_strata(p_values_by_strata)
    sensitivity = sensitivity_analysis_sweep([])
    generate_robustness_report(adjusted, sensitivity, args.output)
    
    logger.info("Robustness analysis complete")

if __name__ == "__main__":
    main()
