import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Import logging utilities from the project's utils module
try:
    from utils.logging import get_logger, log_with_context
except ImportError:
    # Fallback for direct execution if path isn't set up, though project structure assumes utils is importable
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    def log_with_context(logger, level, msg, **kwargs):
        logger.log(level, msg, extra=kwargs)

logger = get_logger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_coverage_vectors(file_path: str) -> List[Dict[str, Any]]:
    """Load aggregated coverage vectors from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Coverage vectors file not found: {file_path}")
    with open(path, 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'vectors' in data:
            return data['vectors']
        else:
            raise ValueError("Unexpected format in coverage vectors file")

def load_validation_results(file_path: str) -> List[Dict[str, Any]]:
    """Load validation results (success rates) from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Validation results file not found: {file_path}")
    with open(path, 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        else:
            raise ValueError("Unexpected format in validation results file")

def calculate_vector_scalar(coverage_vector: List[int]) -> float:
    """
    Calculate the scalar count (sum of 1s) from the binary State Coverage Vector.
    
    Args:
        coverage_vector: A list of 0s and 1s representing the state coverage.
        
    Returns:
        The sum of the vector elements (number of covered states).
    """
    if not isinstance(coverage_vector, list):
        raise TypeError("Coverage vector must be a list")
    if not all(isinstance(x, int) for x in coverage_vector):
        raise TypeError("Coverage vector must contain only integers")
    return float(sum(coverage_vector))

def align_data(coverage_vectors: List[Dict[str, Any]], validation_results: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """
    Align coverage vectors with validation results based on a common identifier (e.g., 'task_id' or 'run_id').
    
    Args:
        coverage_vectors: List of dicts containing 'id' and 'vector' keys.
        validation_results: List of dicts containing 'id' and 'success_rate' keys.
        
    Returns:
        Tuple of (scalars, success_rates) aligned by ID.
    """
    # Create a lookup map for validation results
    val_map = {item['id']: item['success_rate'] for item in validation_results if 'id' in item and 'success_rate' in item}
    
    scalars = []
    success_rates = []
    
    for cv in coverage_vectors:
        if 'id' not in cv:
            logger.warning("Coverage vector entry missing 'id', skipping.")
            continue
        vec_id = cv['id']
        if vec_id not in val_map:
            logger.warning(f"No validation result found for coverage vector ID: {vec_id}, skipping.")
            continue
        
        vector = cv.get('vector', cv.get('coverage_vector', []))
        if not vector:
            logger.warning(f"Empty vector for ID {vec_id}, skipping.")
            continue
            
        scalar_val = calculate_vector_scalar(vector)
        scalars.append(scalar_val)
        success_rates.append(val_map[vec_id])
        
    if len(scalars) != len(success_rates):
        raise ValueError("Alignment failed: mismatched lengths after filtering.")
        
    return scalars, success_rates

def compute_pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Compute Pearson correlation coefficient (r) between two lists.
    
    Args:
        x: List of scalar values (sum of coverage vectors).
        y: List of success rates.
        
    Returns:
        Pearson correlation coefficient r.
    """
    if len(x) != len(y):
        raise ValueError("Input lists must be of equal length")
    if len(x) < 2:
        raise ValueError("Need at least 2 data points to compute correlation")
        
    x_arr = np.array(x)
    y_arr = np.array(y)
    
    # Handle constant arrays
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return 0.0
        
    r = np.corrcoef(x_arr, y_arr)[0, 1]
    return float(r)

def analyze_sensitivity(config: Dict[str, Any], coverage_vectors: List[Dict[str, Any]], validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform sensitivity analysis: compute Pearson correlation between 
    the scalar count of the State Coverage Vector and success rate.
    
    Args:
        config: Configuration dictionary.
        coverage_vectors: List of coverage vector records.
        validation_results: List of validation result records.
        
    Returns:
        Dictionary containing analysis results including correlation coefficient.
    """
    scalars, success_rates = align_data(coverage_vectors, validation_results)
    
    if not scalars:
        raise ValueError("No aligned data points found for analysis.")
        
    r = compute_pearson_correlation(scalars, success_rates)
    
    result = {
        "correlation_coefficient": r,
        "n_samples": len(scalars),
        "mean_scalar": float(np.mean(scalars)),
        "mean_success_rate": float(np.mean(success_rates)),
        "status": "pending"
    }
    
    # Determine status based on thresholds
    if r >= 0.5:
        result["status"] = "validated"
    elif r < 0.3:
        result["status"] = "invalid"
    else:
        result["status"] = "inconclusive"
        
    return result

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save analysis results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def generate_markdown_report(results: Dict[str, Any], output_path: str) -> None:
    """Generate a markdown report for the sensitivity analysis."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    r = results.get("correlation_coefficient", 0.0)
    status = results.get("status", "unknown")
    n_samples = results.get("n_samples", 0)
    
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Overview",
        f"- **Samples Analyzed**: {n_samples}",
        f"- **Pearson Correlation (r)**: {r:.4f}",
        f"- **Status**: {status.upper()}",
        "",
        "## Interpretation",
        ""
    ]
    
    if r >= 0.5:
        report_lines.append("The State Coverage Vector is a **statistically significant proxy** for task difficulty (r ≥ 0.5).")
        report_lines.append("Logging 'Proxy Validated' as per protocol.")
    elif r < 0.3:
        report_lines.append("The State Coverage Vector is **NOT** a significant proxy (r < 0.3).")
        report_lines.append("Recommendation: Expand the variable set or re-evaluate state definitions.")
    else:
        report_lines.append("The correlation is inconclusive (0.3 ≤ r < 0.5).")
        report_lines.append("Further data collection or variable refinement may be needed.")
        
    with open(path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """Main entry point for the sensitivity analysis script."""
    # Default paths (can be overridden by args or config)
    config_path = "data/processed/config.json"
    coverage_vectors_path = "data/processed/coverage_vectors.json"
    validation_results_path = "data/processed/validation_results.json"
    output_json_path = "data/processed/sensitivity_analysis.json"
    output_md_path = "data/processed/sensitivity_report.md"
    
    # Try to load config if it exists, otherwise use defaults
    if Path(config_path).exists():
        config = load_config(config_path)
        coverage_vectors_path = config.get("coverage_vectors_path", coverage_vectors_path)
        validation_results_path = config.get("validation_results_path", validation_results_path)
        output_json_path = config.get("output_json_path", output_json_path)
        output_md_path = config.get("output_md_path", output_md_path)
    else:
        config = {}
        
    logger.info("Starting Sensitivity Analysis...")
    
    try:
        # Load data
        logger.info(f"Loading coverage vectors from {coverage_vectors_path}")
        coverage_vectors = load_coverage_vectors(coverage_vectors_path)
        
        logger.info(f"Loading validation results from {validation_results_path}")
        validation_results = load_validation_results(validation_results_path)
        
        # Perform analysis
        logger.info("Computing Pearson correlation...")
        results = analyze_sensitivity(config, coverage_vectors, validation_results)
        
        # Save JSON results
        logger.info(f"Saving JSON results to {output_json_path}")
        save_results(results, output_json_path)
        
        # Generate and save Markdown report
        logger.info(f"Generating Markdown report to {output_md_path}")
        generate_markdown_report(results, output_md_path)
        
        # LOGGING FOR T041: "Proxy Validated" if r >= 0.5
        if results["correlation_coefficient"] >= 0.5:
            log_with_context(logger, logging.INFO, "Proxy Validated", 
                             correlation=results["correlation_coefficient"],
                             status="validated",
                             message="State Coverage Vector is a statistically significant proxy for task difficulty.")
        elif results["correlation_coefficient"] < 0.3:
            log_with_context(logger, logging.WARNING, "Invalid Proxy", 
                             correlation=results["correlation_coefficient"],
                             status="invalid",
                             message="State Coverage Vector is NOT a significant proxy. Recommend expanding variable set.")
        else:
            log_with_context(logger, logging.INFO, "Inconclusive Correlation", 
                             correlation=results["correlation_coefficient"],
                             status="inconclusive")
                             
        logger.info("Sensitivity Analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()