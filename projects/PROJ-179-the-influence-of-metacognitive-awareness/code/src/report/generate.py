import json
import logging
import os
import sys
from pathlib import Path
import numpy as np

from code.config.env_config import AppConfig, load_config

# Configure logging
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    with open(file_path, 'r') as f:
        return json.load(f)

def write_json_file(file_path: str, data: dict) -> None:
    """Write a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_bootstrap_results(file_path: str) -> dict:
    """Load bootstrap results from a JSON file."""
    if os.path.exists(file_path):
        return load_json_file(file_path)
    return {}

def load_regression_results(file_path: str) -> dict:
    """Load regression results from a JSON file."""
    if os.path.exists(file_path):
        return load_json_file(file_path)
    return {}

def load_diagnostics_results(file_path: str) -> dict:
    """Load diagnostics results from a JSON file."""
    if os.path.exists(file_path):
        return load_json_file(file_path)
    return {}

def load_robustness_results(file_path: str) -> dict:
    """Load robustness results from a JSON file."""
    if os.path.exists(file_path):
        return load_json_file(file_path)
    return {}

def determine_correlation_direction(r: float) -> str:
    """Determine the direction of the correlation."""
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

def apply_bonferroni_correction(p_values: list, n_tests: int) -> list:
    """Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of uncorrected p-values.
        n_tests: Number of statistical tests performed.
        
    Returns:
        List of corrected p-values.
    """
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def apply_bh_correction(p_values: list) -> list:
    """Apply Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: List of uncorrected p-values.
        
    Returns:
        List of corrected p-values (q-values).
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    # Calculate BH corrected p-values
    corrected_sorted = []
    for i, p in enumerate(sorted_p):
        # BH formula: p * n / rank
        rank = i + 1
        corrected_p = min(p * n / rank, 1.0)
        corrected_sorted.append(corrected_p)
    
    # Ensure monotonicity (cumulative min from largest to smallest rank)
    for i in range(n - 2, -1, -1):
        corrected_sorted[i] = min(corrected_sorted[i], corrected_sorted[i + 1])
    
    # Restore original order
    corrected = [0.0] * n
    for i, orig_idx in enumerate(sorted_indices):
        corrected[orig_idx] = corrected_sorted[i]
        
    return corrected

def generate_primary_analysis_report(bootstrap_results: dict) -> dict:
    """Generate the primary analysis report.
    
    Args:
        bootstrap_results: Dictionary containing bootstrap correlation results.
        
    Returns:
        Dictionary with the primary analysis report.
    """
    r = bootstrap_results.get("r", np.nan)
    p = bootstrap_results.get("p", np.nan)
    ci_lower = bootstrap_results.get("ci_lower", np.nan)
    ci_upper = bootstrap_results.get("ci_upper", np.nan)
    bootstrap_count = bootstrap_results.get("bootstrap_count", 1000)
    
    report = {
        "analysis_type": "primary_correlation",
        "correlation_coefficient": float(r),
        "p_value": float(p),
        "confidence_interval": {
            "lower": float(ci_lower),
            "upper": float(ci_upper),
            "level": 0.95
        },
        "bootstrap_count": bootstrap_count,
        "direction": determine_correlation_direction(r),
        "effect_size_magnitude": calculate_effect_size_magnitude(r),
        "methodology": "Hold-Out Accuracy (70/30 split)",
        "metric_predictor": "Type-2 AUC (Metacognitive Awareness)",
        "metric_outcome": "d' (Reality Testing Accuracy)"
    }
    
    return report

def generate_regression_analysis_report(regression_results: dict, diagnostics_results: dict) -> dict:
    """Generate the hierarchical regression analysis report.
    
    Args:
        regression_results: Dictionary containing regression model results.
        diagnostics_results: Dictionary containing diagnostic test results.
        
    Returns:
        Dictionary with the regression analysis report.
    """
    model_1 = regression_results.get("model_1", {})
    model_2 = regression_results.get("model_2", {})
    
    r_squared_1 = model_1.get("r_squared", 0)
    r_squared_2 = model_2.get("r_squared", 0)
    f_change = model_2.get("f_change", 0)
    p_f_change = model_2.get("p_f_change", 1.0)
    
    # Apply BH correction to p-values if multiple tests
    p_values = [p_f_change]
    corrected_p_values = apply_bh_correction(p_values)
    
    report = {
        "analysis_type": "hierarchical_regression",
        "model_1": {
            "predictors": model_1.get("predictors", []),
            "r_squared": float(r_squared_1),
            "adjusted_r_squared": float(model_1.get("adjusted_r_squared", 0)),
            "f_statistic": model_1.get("f_statistic", 0),
            "p_value": float(model_1.get("p_value", 1.0))
        },
        "model_2": {
            "predictors": model_2.get("predictors", []),
            "r_squared": float(r_squared_2),
            "adjusted_r_squared": float(model_2.get("adjusted_r_squared", 0)),
            "f_statistic": model_2.get("f_statistic", 0),
            "p_value": float(model_2.get("p_value", 1.0))
        },
        "incremental_variance": {
            "delta_r_squared": float(r_squared_2 - r_squared_1),
            "f_change": float(f_change),
            "p_f_change": float(p_f_change),
            "p_f_change_corrected_bh": float(corrected_p_values[0]) if corrected_p_values else 1.0
        },
        "diagnostics": {
            "normality_of_residuals": diagnostics_results.get("normality_passed", False),
            "homoscedasticity": diagnostics_results.get("homoscedasticity_passed", False),
            "collinearity_vif_flagged": diagnostics_results.get("collinearity_flagged", False)
        },
        "n_minus_1_model_used": regression_results.get("n_minus_1_model", False)
    }
    
    return report

def generate_robustness_analysis_report(robustness_results: dict) -> dict:
    """Generate the robustness analysis report with multiple comparison correction.
    
    Args:
        robustness_results: Dictionary containing modality-specific correlation results.
        
    Returns:
        Dictionary with the robustness analysis report including corrected p-values.
    """
    modality_results = robustness_results.get("modality_results", {})
    
    # Extract p-values for correction
    p_values = []
    modality_names = []
    
    if "visual" in modality_results:
        p_values.append(modality_results["visual"].get("p_value", np.nan))
        modality_names.append("visual")
    
    if "auditory" in modality_results:
        p_values.append(modality_results["auditory"].get("p_value", np.nan))
        modality_names.append("auditory")
    
    n_tests = len(p_values)
    
    # Apply Bonferroni and Benjamini-Hochberg corrections
    bonferroni_corrected = apply_bonferroni_correction(p_values, n_tests) if n_tests > 0 else []
    bh_corrected = apply_bh_correction(p_values) if n_tests > 0 else []
    
    # Build the report
    report = {
        "analysis_type": "modality_specific_robustness",
        "correction_method": {
            "bonferroni": {
                "applied": True,
                "n_tests": n_tests,
                "corrected_p_values": dict(zip(modality_names, [float(p) for p in bonferroni_corrected]))
            },
            "benjamini_hochberg": {
                "applied": True,
                "n_tests": n_tests,
                "corrected_p_values": dict(zip(modality_names, [float(p) for p in bh_corrected]))
            }
        },
        "modality_results": {}
    }
    
    for modality, results in modality_results.items():
        idx = modality_names.index(modality) if modality in modality_names else -1
        
        modality_report = {
            "correlation_coefficient": float(results.get("r", np.nan)),
            "p_value_uncorrected": float(results.get("p_value", np.nan)),
            "p_value_bonferroni": float(bonferroni_corrected[idx]) if idx >= 0 else np.nan,
            "p_value_bh": float(bh_corrected[idx]) if idx >= 0 else np.nan,
            "confidence_interval": {
                "lower": float(results.get("ci_lower", np.nan)),
                "upper": float(results.get("ci_upper", np.nan))
            },
            "bootstrap_count": results.get("bootstrap_count", 1000),
            "n_trials": results.get("n_trials", 0),
            "direction": determine_correlation_direction(results.get("r", 0)),
            "effect_size_magnitude": calculate_effect_size_magnitude(results.get("r", 0))
        }
        
        report["modality_results"][modality] = modality_report
    
    # Summary
    report["summary"] = {
        "total_modalities_tested": n_tests,
        "significant_after_bonferroni": sum(1 for p in bonferroni_corrected if p < 0.05),
        "significant_after_bh": sum(1 for p in bh_corrected if p < 0.05)
    }
    
    return report

def write_report(file_path: str, report: dict) -> None:
    """Write a report to a JSON file."""
    write_json_file(file_path, report)
    logger.info(f"Report written to {file_path}")

def main():
    """Main entry point for report generation."""
    config = load_config()
    base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
    
    # Define paths
    bootstrap_results_path = base_dir / "data" / "results" / "bootstrap_config.json"
    regression_results_path = base_dir / "data" / "results" / "regression_analysis.json"
    diagnostics_results_path = base_dir / "data" / "results" / "diagnostics_results.json"
    robustness_results_path = base_dir / "data" / "results" / "robustness_results.json"
    
    primary_report_path = base_dir / "data" / "results" / "primary_analysis.json"
    regression_report_path = base_dir / "data" / "results" / "regression_analysis.json"
    robustness_report_path = base_dir / "data" / "results" / "robustness_analysis.json"
    
    try:
        # Generate Primary Analysis Report
        logger.info("Generating primary analysis report...")
        bootstrap_data = load_bootstrap_results(str(bootstrap_results_path))
        primary_report = generate_primary_analysis_report(bootstrap_data)
        write_report(str(primary_report_path), primary_report)
        
        # Generate Regression Analysis Report
        logger.info("Generating regression analysis report...")
        regression_data = load_regression_results(str(regression_results_path))
        diagnostics_data = load_diagnostics_results(str(diagnostics_results_path))
        regression_report = generate_regression_analysis_report(regression_data, diagnostics_data)
        write_report(str(regression_report_path), regression_report)
        
        # Generate Robustness Analysis Report with Multiple Comparison Correction
        logger.info("Generating robustness analysis report with multiple comparison correction...")
        robustness_data = load_robustness_results(str(robustness_results_path))
        robustness_report = generate_robustness_analysis_report(robustness_data)
        write_report(str(robustness_report_path), robustness_report)
        
        logger.info("All reports generated successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating reports: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())