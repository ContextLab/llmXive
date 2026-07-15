"""
Sensitivity Analysis Module (Task T028)

Implements sensitivity analysis of nutrient coefficients against literature ranges.
This module compares the fitted model coefficients (from LMM) against established
biological ranges found in literature to assess biological plausibility.

References:
- FR-011: Verify biological plausibility of coefficients against literature
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

# Import from local project modules
from config import get_config, setup_logging
from modeling import fit_lmm, train_models

# Configure logger
logger = setup_logging("sensitivity_analysis")

# Literature ranges for nutrient coefficients (log-transformed root metrics vs nutrients)
# These ranges are derived from meta-analyses of plant root response to nutrients
# Format: (lower_bound, upper_bound) for standardized coefficients
LITERATURE_RANGES = {
    "phosphorus": {
        "min": -0.8,
        "max": 0.5,
        "typical": -0.2,
        "source": "meta-analysis root-phosphorus response (log-scale)"
    },
    "nitrogen": {
        "min": -0.6,
        "max": 0.4,
        "typical": -0.15,
        "source": "meta-analysis root-nitrogen response (log-scale)"
    },
    "potassium": {
        "min": -0.5,
        "max": 0.3,
        "typical": -0.1,
        "source": "estimated from NPK correlation studies"
    }
}

# Thresholds for sensitivity flags
DEVIATION_WARNING_THRESHOLD = 0.3  # Coefficient deviates >30% from typical
DEVIATION_CRITICAL_THRESHOLD = 0.5  # Coefficient deviates >50% from typical


def load_model_coefficients(model_results_path: str) -> Dict[str, Any]:
    """
    Load model results containing coefficients from the modeling output.
    
    Args:
        model_results_path: Path to the model results JSON file
        
    Returns:
        Dictionary containing model coefficients and metadata
    """
    if not os.path.exists(model_results_path):
        raise FileNotFoundError(f"Model results file not found: {model_results_path}")
    
    with open(model_results_path, 'r') as f:
        results = json.load(f)
    
    return results


def extract_lmm_coefficients(lmm_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract fixed effect coefficients from LMM results.
    
    Args:
        lmm_results: Dictionary containing LMM model results
        
    Returns:
        Dictionary mapping coefficient names to their values
    """
    coefficients = {}
    
    # Navigate through the results structure to find fixed effects
    if "lmm_results" in lmm_results:
        lmm_data = lmm_results["lmm_results"]
        
        if "fixed_effects" in lmm_data:
            fixed_effects = lmm_data["fixed_effects"]
            
            # Extract coefficients for nutrient variables
            for coef_name, coef_value in fixed_effects.items():
                if coef_name in LITERATURE_RANGES:
                    coefficients[coef_name] = float(coef_value)
    
    return coefficients


def compare_against_literature(
    coefficients: Dict[str, float], 
    literature_ranges: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compare fitted coefficients against literature ranges.
    
    Args:
        coefficients: Dictionary of fitted coefficients
        literature_ranges: Dictionary of literature reference ranges
        
    Returns:
        List of comparison results with status and deviation metrics
    """
    comparisons = []
    
    for nutrient, fitted_coef in coefficients.items():
        if nutrient not in literature_ranges:
            logger.warning(f"No literature range found for nutrient: {nutrient}")
            continue
        
        ref_range = literature_ranges[nutrient]
        typical = ref_range["typical"]
        min_val = ref_range["min"]
        max_val = ref_range["max"]
        
        # Calculate deviation from typical
        deviation = abs(fitted_coef - typical)
        deviation_pct = deviation / abs(typical) if typical != 0 else deviation
        
        # Determine status
        if min_val <= fitted_coef <= max_val:
            status = "within_range"
        elif deviation_pct <= DEVIATION_WARNING_THRESHOLD:
            status = "warning"
        else:
            status = "critical"
        
        comparison = {
            "nutrient": nutrient,
            "fitted_coefficient": fitted_coef,
            "literature_typical": typical,
            "literature_range": (min_val, max_val),
            "deviation_from_typical": deviation,
            "deviation_percentage": deviation_pct,
            "status": status,
            "source": ref_range["source"]
        }
        
        comparisons.append(comparison)
        logger.info(f"Nutrient {nutrient}: fitted={fitted_coef:.4f}, "
                   f"typical={typical:.4f}, status={status}")
    
    return comparisons


def calculate_sensitivity_metrics(comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate sensitivity metrics.
    
    Args:
        comparisons: List of comparison results
        
    Returns:
        Dictionary with aggregate metrics
    """
    if not comparisons:
        return {
            "total_coefficients_tested": 0,
            "within_range_count": 0,
            "warning_count": 0,
            "critical_count": 0,
            "overall_plausibility": "unknown"
        }
    
    total = len(comparisons)
    within_range = sum(1 for c in comparisons if c["status"] == "within_range")
    warning = sum(1 for c in comparisons if c["status"] == "warning")
    critical = sum(1 for c in comparisons if c["status"] == "critical")
    
    # Determine overall plausibility
    if critical > 0:
        overall = "questionable"
    elif warning > total * 0.3:
        overall = "caution"
    elif within_range == total:
        overall = "plausible"
    else:
        overall = "mixed"
    
    return {
        "total_coefficients_tested": total,
        "within_range_count": within_range,
        "warning_count": warning,
        "critical_count": critical,
        "overall_plausibility": overall,
        "plausibility_score": within_range / total if total > 0 else 0
    }


def run_sensitivity_analysis(
    model_results_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main function to run sensitivity analysis.
    
    Args:
        model_results_path: Path to model results JSON
        output_path: Path to write sensitivity analysis results
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    logger.info(f"Starting sensitivity analysis for {model_results_path}")
    
    # Load model results
    model_results = load_model_coefficients(model_results_path)
    
    # Extract LMM coefficients
    coefficients = extract_lmm_coefficients(model_results)
    
    if not coefficients:
        logger.warning("No nutrient coefficients found in model results")
        results = {
            "status": "no_coefficients",
            "message": "No nutrient coefficients found for comparison",
            "comparisons": [],
            "metrics": calculate_sensitivity_metrics([])
        }
    else:
        # Compare against literature
        comparisons = compare_against_literature(coefficients, LITERATURE_RANGES)
        
        # Calculate metrics
        metrics = calculate_sensitivity_metrics(comparisons)
        
        results = {
            "status": "success",
            "model_source": model_results_path,
            "comparisons": comparisons,
            "metrics": metrics,
            "literature_ranges_used": LITERATURE_RANGES
        }
    
    # Write results to output file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    logger.info(f"Overall plausibility: {results['metrics']['overall_plausibility']}")
    
    return results


def main():
    """Main entry point for sensitivity analysis script."""
    config = get_config()
    
    # Paths from config
    model_results_path = config.get("MODEL_RESULTS_PATH", "artifacts/models/model_results.json")
    sensitivity_output_path = config.get("SENSITIVITY_OUTPUT_PATH", "artifacts/reports/sensitivity_analysis.json")
    
    # Run analysis
    results = run_sensitivity_analysis(model_results_path, sensitivity_output_path, config)
    
    # Exit with appropriate code based on plausibility
    if results["metrics"]["overall_plausibility"] == "questionable":
        logger.warning("Sensitivity analysis indicates questionable biological plausibility")
        # Do not exit with error code to allow pipeline to continue, but log warning
    
    return results


if __name__ == "__main__":
    main()
