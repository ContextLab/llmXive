"""
Sensitivity Analysis Module

Performs threshold sweeps on maintenance definitions to test the robustness
of the correlation between dependency age and vulnerability counts.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from src.analysis.correlation import load_dependencies_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_unmaintained_ratio(dependencies: List[Dict[str, Any]], age_threshold_days: int) -> float:
    """
    Calculate the proportion of dependencies considered 'unmaintained'
    based on a specific age threshold.

    Args:
        dependencies: List of dependency dictionaries.
        age_threshold_days: Number of days after which a package is considered unmaintained.

    Returns:
        Float ratio of unmaintained packages (0.0 to 1.0).
    """
    if not dependencies:
        return 0.0

    unmaintained_count = 0
    valid_count = 0

    for dep in dependencies:
        age = dep.get('age_in_days')
        if age is None:
            continue  # Skip entries with missing age data
        
        valid_count += 1
        if age > age_threshold_days:
            unmaintained_count += 1

    if valid_count == 0:
        return 0.0

    return unmaintained_count / valid_count

def calculate_correlation_with_maintenance_status(dependencies: List[Dict[str, Any]], age_threshold_days: int) -> Tuple[float, float]:
    """
    Calculate Spearman correlation between age_in_days and vulnerability_count,
    but only for the subset of dependencies that are 'unmaintained' by the given threshold.
    
    This tests if the correlation holds specifically within the 'unmaintained' group.

    Args:
        dependencies: List of dependency dictionaries.
        age_threshold_days: Threshold to define 'unmaintained'.

    Returns:
        Tuple of (correlation_coefficient, p_value). Returns (0.0, 1.0) if insufficient data.
    """
    # Filter for unmaintained dependencies
    unmaintained_deps = [
        dep for dep in dependencies 
        if dep.get('age_in_days') is not None and dep.get('age_in_days') > age_threshold_days
    ]

    if len(unmaintained_deps) < 2:
        logger.warning(f"Insufficient data for threshold {age_threshold_days} (N={len(unmaintained_deps)}). Skipping correlation.")
        return 0.0, 1.0

    ages = [dep['age_in_days'] for dep in unmaintained_deps]
    vulns = [dep.get('vulnerability_count', 0) or 0 for dep in unmaintained_deps]

    # Handle cases where all values are constant (e.g., all 0 vulnerabilities)
    if len(set(ages)) < 2 or len(set(vulns)) < 2:
        logger.warning(f"Constant values in subset for threshold {age_threshold_days}. Skipping correlation.")
        return 0.0, 1.0

    try:
        rho, p_value = scipy.stats.spearmanr(ages, vulns)
        return float(rho), float(p_value)
    except Exception as e:
        logger.error(f"Error calculating correlation for threshold {age_threshold_days}: {e}")
        return 0.0, 1.0

def run_threshold_sweep(dependencies: List[Dict[str, Any]], 
                        thresholds: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """
    Run the sensitivity analysis by sweeping through different age thresholds.

    Args:
        dependencies: List of dependency dictionaries.
        thresholds: List of age thresholds (in days) to test. Defaults to [30, 90, 180, 365, 730].

    Returns:
        List of dictionaries containing results for each threshold.
    """
    if thresholds is None:
        thresholds = [30, 90, 180, 365, 730]

    results = []
    
    logger.info(f"Starting threshold sweep with {len(thresholds)} thresholds.")
    
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold} days")
        
        unmaintained_ratio = calculate_unmaintained_ratio(dependencies, threshold)
        rho, p_value = calculate_correlation_with_maintenance_status(dependencies, threshold)
        
        # Count valid entries for this threshold
        valid_count = sum(1 for dep in dependencies if dep.get('age_in_days') is not None)
        unmaintained_count = sum(1 for dep in dependencies if dep.get('age_in_days') is not None and dep['age_in_days'] > threshold)

        results.append({
            "threshold_days": threshold,
            "unmaintained_ratio": round(unmaintained_ratio, 4),
            "unmaintained_count": unmaintained_count,
            "total_valid_samples": valid_count,
            "correlation_coefficient": round(rho, 4),
            "p_value": round(p_value, 6)
        })

    return results

def run_sensitivity_analysis(input_path: Optional[str] = None, 
                             output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for the sensitivity analysis pipeline.
    Loads data, runs the threshold sweep, and saves results.

    Args:
        input_path: Path to the processed dependencies CSV. Defaults to 'data/processed/dependencies_raw.csv'.
        output_path: Path for the output JSON. Defaults to 'data/processed/sensitivity_analysis.json'.

    Returns:
        Dictionary containing the analysis results.
    """
    if input_path is None:
        input_path = "data/processed/dependencies_raw.csv"
    if output_path is None:
        output_path = "data/processed/sensitivity_analysis.json"

    logger.info(f"Loading dependencies from {input_path}")
    dependencies = load_dependencies_data(input_path)

    if not dependencies:
        logger.error("No dependencies loaded. Aborting analysis.")
        raise ValueError("No dependencies loaded. Check input file path and content.")

    # Run the sweep
    threshold_results = run_threshold_sweep(dependencies)

    # Compile final result
    analysis_result = {
        "analysis_type": "sensitivity_threshold_sweep",
        "input_file": input_path,
        "total_dependencies_analyzed": len(dependencies),
        "threshold_sweep": threshold_results
    }

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    
    return analysis_result

def main():
    """CLI entry point for sensitivity analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run sensitivity analysis on dependency data.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/dependencies_raw.csv",
        help="Path to input dependencies CSV (default: data/processed/dependencies_raw.csv)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/sensitivity_analysis.json",
        help="Path for output JSON (default: data/processed/sensitivity_analysis.json)"
    )
    
    args = parser.parse_args()

    try:
        result = run_sensitivity_analysis(args.input, args.output)
        print(f"Analysis completed successfully. Output: {args.output}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
