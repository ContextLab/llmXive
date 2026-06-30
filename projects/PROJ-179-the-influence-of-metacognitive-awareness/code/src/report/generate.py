"""
T016: Implement src/report/generate.py to render correlation magnitude, direction, p-value, and CI.
Outputs: data/results/primary_analysis.json
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_bootstrap_results(filepath: str) -> dict:
    """Load bootstrap results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Bootstrap results file not found: {filepath}")
        return None
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_regression_results(filepath: str) -> dict:
    """Load regression results from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Regression results file not found: {filepath}")
        return None
    
    with open(filepath, 'r') as f:
        return json.load(f)

def determine_correlation_direction(r_value: float) -> str:
    """Determine if correlation is positive, negative, or negligible."""
    if r_value > 0.1:
        return "positive"
    elif r_value < -0.1:
        return "negative"
    else:
        return "negligible"

def calculate_effect_size_magnitude(r_value: float) -> str:
    """Calculate effect size magnitude based on Cohen's conventions."""
    abs_r = abs(r_value)
    if abs_r >= 0.5:
        return "large"
    elif abs_r >= 0.3:
        return "medium"
    elif abs_r >= 0.1:
        return "small"
    else:
        return "negligible"

def apply_bonferroni_correction(p_value: float, n_tests: int) -> float:
    """Apply Bonferroni correction for multiple comparisons."""
    return min(p_value * n_tests, 1.0)

def apply_bh_correction(p_values: list) -> list:
    """Apply Benjamini-Hochberg correction for multiple comparisons."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    corrected = np.zeros(n)
    for i in range(n):
        corrected[sorted_indices[i]] = min(sorted_p_values[i] * n / (i + 1), 1.0)
    
    # Ensure monotonicity
  #   for i in range(n-2, -1, -1):
  #       corrected[sorted_indices[i]] = min(corrected[sorted_indices[i]], corrected[sorted_indices[i+1]])
    
    return corrected.tolist()

def generate_primary_analysis_report(bootstrap_results: dict, config: dict = None) -> dict:
    """
    Generate the primary analysis report from bootstrap results.
    
    Args:
        bootstrap_results: Dictionary containing correlation results from bootstrap analysis
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing the formatted report
    """
    if not bootstrap_results:
        logger.error("No bootstrap results provided")
        return None
    
    # Extract key statistics
    r_value = bootstrap_results.get('r_value')
    p_value = bootstrap_results.get('p_value')
    ci_lower = bootstrap_results.get('ci_lower')
    ci_upper = bootstrap_results.get('ci_upper')
    n_resamples = bootstrap_results.get('n_resamples', 1000)
    method = bootstrap_results.get('method', 'pearson')
    
    # Calculate derived metrics
    direction = determine_correlation_direction(r_value)
    magnitude = calculate_effect_size_magnitude(r_value)
    significance = "significant" if p_value < 0.05 else "not significant"
    
    # Build report structure
    report = {
        "analysis_type": "primary_correlation",
        "method": method,
        "statistics": {
            "correlation_coefficient": r_value,
            "p_value": p_value,
            "confidence_interval_95": {
                "lower": ci_lower,
                "upper": ci_upper
            },
            "n_resamples": n_resamples,
            "significance": significance
        },
        "interpretation": {
            "direction": direction,
            "magnitude": magnitude,
            "summary": f"The correlation between metacognitive awareness (Type-2 AUC) and reality testing accuracy (d') is {direction} (r = {r_value:.3f}, p = {p_value:.3f}, 95% CI [{ci_lower:.3f}, {ci_upper:.3f}]). This effect is {magnitude} and {significance}."
        },
        "metadata": {
            "timestamp": pd.Timestamp.now().isoformat(),
            "pipeline_version": "1.0.0"
        }
    }
    
    return report

def write_report(report: dict, output_path: str):
    """Write the report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report written to {output_path}")

def main():
    """Main entry point for generating the primary analysis report."""
    logger.info("Starting report generation (T016)...")
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    bootstrap_results_path = base_dir / "data" / "results" / "bootstrap_results.json"
    output_path = base_dir / "data" / "results" / "primary_analysis.json"
    
    # Load bootstrap results
    logger.info(f"Loading bootstrap results from {bootstrap_results_path}")
    bootstrap_results = load_bootstrap_results(str(bootstrap_results_path))
    
    if not bootstrap_results:
        logger.error("Failed to load bootstrap results. Aborting.")
        sys.exit(1)
    
    # Generate report
    logger.info("Generating primary analysis report...")
    report = generate_primary_analysis_report(bootstrap_results)
    
    if not report:
        logger.error("Failed to generate report. Aborting.")
        sys.exit(1)
    
    # Write report
    logger.info(f"Writing report to {output_path}")
    write_report(report, str(output_path))
    
    logger.info("Report generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())