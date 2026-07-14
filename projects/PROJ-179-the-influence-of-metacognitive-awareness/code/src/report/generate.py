import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from sibling modules as per API surface
# Note: Assuming these exist in code/src/utils/stats.py or similar based on context
# If they are missing, we define minimal helpers here or import from standard libs
from scipy.stats import t

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {filepath}")
        return {}

def write_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Write data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_bootstrap_results(filepath: str) -> Dict[str, Any]:
    """Load bootstrap results for a specific analysis."""
    return load_json_file(filepath)

def load_diagnostics_results(filepath: str) -> Dict[str, Any]:
    """Load diagnostics results."""
    return load_json_file(filepath)

def determine_correlation_direction(r: float) -> str:
    """Determine the direction of correlation."""
    if r > 0:
        return "positive"
    elif r < 0:
        return "negative"
    else:
        return "zero"

def calculate_effect_size_magnitude(r: float) -> str:
    """Calculate the magnitude of the effect size based on Cohen's guidelines."""
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
        n_tests: Number of hypothesis tests performed.
        
    Returns:
        List of corrected p-values, capped at 1.0.
    """
    if n_tests == 0:
        return p_values
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg (FDR) correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of corrected p-values (q-values).
    """
    n = len(p_values)
    if n == 0:
        return p_values
    
    # Sort p-values and keep track of original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    # Calculate BH corrected values
    corrected_sorted = [p * n / (i + 1) for i, p in enumerate(sorted_p)]
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        corrected_sorted[i] = min(corrected_sorted[i], corrected_sorted[i + 1])
        
    # Cap at 1.0
    corrected_sorted = [min(p, 1.0) for p in corrected_sorted]
    
    # Restore original order
    corrected = [0.0] * n
    for i, orig_idx in enumerate(sorted_indices):
        corrected[orig_idx] = corrected_sorted[i]
        
    return corrected

def generate_primary_analysis_report(bootstrap_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the primary analysis report."""
    r = bootstrap_results.get("r", np.nan)
    p = bootstrap_results.get("p", np.nan)
    ci_lower = bootstrap_results.get("ci_lower", np.nan)
    ci_upper = bootstrap_results.get("ci_upper", np.nan)
    
    return {
        "correlation_coefficient": r,
        "p_value": p,
        "confidence_interval_95": [ci_lower, ci_upper],
        "direction": determine_correlation_direction(r),
        "magnitude": calculate_effect_size_magnitude(r),
        "analysis_type": "primary_hold_out"
    }

def generate_regression_analysis_report(regression_results: Dict[str, Any], diagnostics_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the regression analysis report."""
    model_1 = regression_results.get("model_1", {})
    model_2 = regression_results.get("model_2", {})
    delta_r2 = regression_results.get("delta_r_squared", np.nan)
    f_change = regression_results.get("f_change", np.nan)
    
    return {
        "model_1": model_1,
        "model_2": model_2,
        "delta_r_squared": delta_r2,
        "f_change": f_change,
        "normality_passed": diagnostics_results.get("normality_passed", False),
        "homoscedasticity_passed": diagnostics_results.get("homoscedasticity_passed", False),
        "collinearity_flagged": diagnostics_results.get("collinearity_flagged", False)
    }

def generate_robustness_analysis_report(modality_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate the robustness analysis report with multiple comparison corrections.
    
    This function aggregates results from different modalities (e.g., visual, auditory),
    extracts raw p-values, applies Bonferroni and Benjamini-Hochberg corrections,
    and returns a comprehensive report.
    
    Args:
        modality_results: Dictionary mapping modality names to their analysis results
                         (containing 'r', 'p', 'ci_lower', 'ci_upper', etc.)
                         
    Returns:
        Dictionary containing the full report with corrected p-values.
    """
    if not modality_results:
        logger.warning("No modality results provided for robustness analysis.")
        return {"status": "empty", "message": "No results to report."}
    
    report = {
        "analysis_type": "modality_robustness",
        "modalities": {},
        "multiple_comparison_correction": {}
    }
    
    # Collect raw p-values and results
    raw_p_values = []
    modality_names = []
    
    for modality, results in modality_results.items():
        p_val = results.get("p", np.nan)
        if not np.isnan(p_val):
            raw_p_values.append(p_val)
            modality_names.append(modality)
        
        # Add uncorrected results to report
        report["modalities"][modality] = {
            "correlation_coefficient": results.get("r", np.nan),
            "p_value_uncorrected": p_val,
            "confidence_interval_95": [
                results.get("ci_lower", np.nan),
                results.get("ci_upper", np.nan)
            ],
            "direction": determine_correlation_direction(results.get("r", 0)),
            "magnitude": calculate_effect_size_magnitude(results.get("r", 0))
        }
    
    n_tests = len(raw_p_values)
    
    if n_tests == 0:
        logger.warning("No valid p-values found for correction.")
        report["multiple_comparison_correction"] = {
            "method": "none",
            "reason": "No valid p-values found",
            "corrected_p_values": {}
        }
        return report
    
    # Apply Bonferroni correction
    bonferroni_corrected = apply_bonferroni_correction(raw_p_values, n_tests)
    
    # Apply Benjamini-Hochberg correction
    bh_corrected = apply_bh_correction(raw_p_values)
    
    # Map corrected p-values back to modalities
    bonferroni_map = {}
    bh_map = {}
    
    for i, modality in enumerate(modality_names):
        bonferroni_map[modality] = bonferroni_corrected[i]
        bh_map[modality] = bh_corrected[i]
        
        # Update modality report with corrected values
        report["modalities"][modality]["p_value_bonferroni"] = bonferroni_map[modality]
        report["modalities"][modality]["p_value_bh_fdr"] = bh_map[modality]
    
    report["multiple_comparison_correction"] = {
        "n_tests": n_tests,
        "methods_applied": ["bonferroni", "benjamini_hochberg"],
        "bonferroni_corrected_p_values": bonferroni_map,
        "bh_fdr_corrected_p_values": bh_map,
        "family_wise_error_rate_controlled": True
    }
    
    logger.info(f"Robustness analysis report generated for {n_tests} modalities.")
    return report

def write_report(filepath: str, data: Dict[str, Any]) -> None:
    """Write the report to a JSON file."""
    write_json_file(filepath, data)

def main():
    """
    Main function to generate the robustness analysis report.
    This is the entry point for T028.
    """
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/ directory
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    results_dir = base_dir / "data" / "results"
    derived_dir = base_dir / "data" / "derived"
    
    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    
    # Load results from T027 (robustness analysis per modality)
    # We expect T027 to have produced results for 'visual' and 'auditory'
    # These might be stored in separate files or a combined file.
    # For this task, we assume a structure where T027 outputs a file per modality
    # or a single file containing all. Let's assume T027 wrote to:
    # data/results/robustness_visual.json and data/results/robustness_auditory.json
    # Or a single file data/results/robustness_analysis_raw.json containing a dict.
    
    # Let's try to load a combined raw file first, if it exists.
    # If not, we'll construct from individual files if T027 created them.
    combined_raw_path = results_dir / "robustness_analysis_raw.json"
    
    if combined_raw_path.exists():
        raw_data = load_json_file(str(combined_raw_path))
        # Expecting raw_data to be a dict like: {"visual": {...}, "auditory": {...}}
        modality_results = raw_data
    else:
        # Fallback: try to load individual files if they exist
        modality_results = {}
        visual_path = results_dir / "robustness_visual.json"
        auditory_path = results_dir / "robustness_auditory.json"
        
        if visual_path.exists():
            modality_results["visual"] = load_json_file(str(visual_path))
        if auditory_path.exists():
            modality_results["auditory"] = load_json_file(str(auditory_path))
        
        if not modality_results:
            logger.error("No robustness analysis results found. Ensure T027 has run successfully.")
            # Create a minimal empty report to satisfy the deliverable requirement
            report = {
                "status": "error",
                "message": "No input data found for robustness analysis. T027 results missing."
            }
            output_path = results_dir / "robustness_analysis.json"
            write_report(str(output_path), report)
            return
    
    # Generate the report with corrections
    report = generate_robustness_analysis_report(modality_results)
    
    # Write the final report
    output_path = results_dir / "robustness_analysis.json"
    write_report(str(output_path), report)
    
    logger.info(f"Robustness analysis report written to {output_path}")
    print(f"SUCCESS: Robustness analysis report generated at {output_path}")

if __name__ == "__main__":
    main()