import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Import existing utilities from the project
from config.env_config import load_config, setup_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON in {filepath}: {e}")
        return {}

def write_json_file(filepath: str, data: dict) -> bool:
    """Write a dictionary to a JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error writing to {filepath}: {e}")
        return False

def load_bootstrap_results(filepath: str = "data/results/bootstrap_config.json") -> dict:
    """Load bootstrap results from the specified file."""
    return load_json_file(filepath)

def load_regression_results(filepath: str = "data/results/regression_analysis.json") -> dict:
    """Load regression results from the specified file."""
    return load_json_file(filepath)

def load_diagnostics_results(filepath: str = "data/results/diagnostics.json") -> dict:
    """Load diagnostics results from the specified file."""
    return load_json_file(filepath)

def load_correlation_results(filepath: str = "data/results/primary_analysis.json") -> dict:
    """Load correlation results from the specified file."""
    return load_json_file(filepath)

def determine_correlation_direction(r_value: float) -> str:
    """Determine if correlation is positive, negative, or negligible."""
    if r_value > 0.1:
        return "positive"
    elif r_value < -0.1:
        return "negative"
    return "negligible"

def calculate_effect_size_magnitude(r_value: float) -> str:
    """Calculate the magnitude of the effect size based on Cohen's guidelines."""
    abs_r = abs(r_value)
    if abs_r >= 0.5:
        return "large"
    elif abs_r >= 0.3:
        return "medium"
    elif abs_r >= 0.1:
        return "small"
    return "negligible"

def apply_bonferroni_correction(p_values: list, num_tests: int) -> list:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values
        num_tests: Number of statistical tests performed
        
    Returns:
        List of corrected p-values (capped at 1.0)
    """
    if num_tests == 0:
        return [1.0] * len(p_values)
    
    alpha = 0.05
    corrected_p_values = []
    for p in p_values:
        corrected_p = min(p * num_tests, 1.0)
        corrected_p_values.append(corrected_p)
    
    return corrected_p_values

def apply_bh_correction(p_values: list) -> list:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons (FDR).
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of corrected p-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values while keeping track of original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate BH critical values
    corrected_p_values = [0.0] * n
    prev_corrected = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        raw_p = sorted_p_values[i]
        # BH adjusted p-value: p * n / rank
        adjusted_p = min(raw_p * n / rank, prev_corrected)
        corrected_p_values[sorted_indices[i]] = adjusted_p
        prev_corrected = adjusted_p
    
    return corrected_p_values

def generate_primary_analysis_report(correlation_results: dict, bootstrap_results: dict) -> dict:
    """Generate the primary analysis report."""
    r_value = correlation_results.get("correlation", np.nan)
    p_value = correlation_results.get("p_value", np.nan)
    ci_lower = correlation_results.get("ci_lower", np.nan)
    ci_upper = correlation_results.get("ci_upper", np.nan)
    
    report = {
        "analysis_type": "primary_correlation",
        "correlation": r_value,
        "p_value": p_value,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "n_resamples": bootstrap_results.get("n_resamples", 0),
        "direction": determine_correlation_direction(r_value),
        "effect_size_magnitude": calculate_effect_size_magnitude(r_value),
        "interpretation": "Metacognitive awareness significantly predicts reality testing accuracy." if p_value < 0.05 else "No significant relationship found."
    }
    return report

def generate_regression_analysis_report(regression_results: dict, diagnostics_results: dict) -> dict:
    """Generate the regression analysis report."""
    report = {
        "analysis_type": "hierarchical_regression",
        "model_1": regression_results.get("model_1", {}),
        "model_2": regression_results.get("model_2", {}),
        "delta_r_squared": regression_results.get("delta_r_squared", np.nan),
        "f_change": regression_results.get("f_change", np.nan),
        "p_change": regression_results.get("p_change", np.nan),
        "diagnostics": diagnostics_results,
        "assumptions_met": diagnostics_results.get("all_passed", False)
    }
    return report

def generate_robustness_analysis_report(
    visual_results: dict,
    auditory_results: dict,
    correction_method: str = "bonferroni"
) -> dict:
    """
    Generate the robustness analysis report with multiple comparison correction.
    
    Args:
        visual_results: Results from visual modality analysis
        auditory_results: Results from auditory modality analysis
        correction_method: Method for correction ('bonferroni' or 'bh')
        
    Returns:
        Dictionary containing corrected results and interpretation
    """
    # Extract p-values from each modality
    p_visual = visual_results.get("p_value", 1.0)
    p_auditory = auditory_results.get("p_value", 1.0)
    
    raw_p_values = [p_visual, p_auditory]
    
    # Apply correction
    if correction_method == "bonferroni":
        corrected_p_values = apply_bonferroni_correction(raw_p_values, num_tests=2)
    elif correction_method == "bh":
        corrected_p_values = apply_bh_correction(raw_p_values)
    else:
        logger.warning(f"Unknown correction method: {correction_method}. Using no correction.")
        corrected_p_values = raw_p_values
    
    corrected_p_visual = corrected_p_values[0]
    corrected_p_auditory = corrected_p_values[1]
    
    # Determine significance
    sig_visual = corrected_p_visual < 0.05
    sig_auditory = corrected_p_auditory < 0.05
    
    # Build report
    report = {
        "analysis_type": "modality_specific_robustness",
        "correction_method": correction_method,
        "num_tests": 2,
        "visual_modality": {
            "correlation": visual_results.get("correlation", np.nan),
            "p_value_raw": p_visual,
            "p_value_corrected": corrected_p_visual,
            "ci_95_lower": visual_results.get("ci_lower", np.nan),
            "ci_95_upper": visual_results.get("ci_upper", np.nan),
            "significant_after_correction": sig_visual,
            "direction": determine_correlation_direction(visual_results.get("correlation", 0)),
            "effect_size_magnitude": calculate_effect_size_magnitude(visual_results.get("correlation", 0))
        },
        "auditory_modality": {
            "correlation": auditory_results.get("correlation", np.nan),
            "p_value_raw": p_auditory,
            "p_value_corrected": corrected_p_auditory,
            "ci_95_lower": auditory_results.get("ci_lower", np.nan),
            "ci_95_upper": auditory_results.get("ci_upper", np.nan),
            "significant_after_correction": sig_auditory,
            "direction": determine_correlation_direction(auditory_results.get("correlation", 0)),
            "effect_size_magnitude": calculate_effect_size_magnitude(auditory_results.get("correlation", 0))
        },
        "interpretation": {
            "visual": "Significant relationship in visual modality." if sig_visual else "No significant relationship in visual modality.",
            "auditory": "Significant relationship in auditory modality." if sig_auditory else "No significant relationship in auditory modality.",
            "summary": "Robust relationship across modalities." if (sig_visual and sig_auditory) else "Relationship modality-specific or non-significant."
        }
    }
    
    return report

def write_report(report: dict, filepath: str) -> bool:
    """Write the report to a JSON file."""
    return write_json_file(filepath, report)

def main():
    """Main entry point for generating the robustness analysis report."""
    logger.info("Starting robustness analysis report generation (T028)...")
    
    # Load configuration
    config = load_config()
    base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
    
    # Define paths
    visual_results_path = base_dir / "data/results/visual_modality_analysis.json"
    auditory_results_path = base_dir / "data/results/auditory_modality_analysis.json"
    output_path = base_dir / "data/results/robustness_analysis.json"
    
    # Load results from T027 (robustness analysis)
    # Note: These files should have been created by T027
    visual_results = load_json_file(str(visual_results_path))
    auditory_results = load_json_file(str(auditory_results_path))
    
    # Check if results are available
    if not visual_results or not auditory_results:
        logger.error("Could not load modality-specific results. Ensure T027 has completed successfully.")
        # Create a minimal report indicating failure
        report = {
            "analysis_type": "modality_specific_robustness",
            "status": "failed",
            "reason": "Missing input results from T027",
            "visual_modality": {},
            "auditory_modality": {}
        }
    else:
        # Generate the report with Bonferroni correction (default)
        report = generate_robustness_analysis_report(
            visual_results=visual_results,
            auditory_results=auditory_results,
            correction_method="bonferroni"
        )
        report["status"] = "success"
    
    # Write the report
    success = write_report(report, str(output_path))
    
    if success:
        logger.info(f"Robustness analysis report written to {output_path}")
        return 0
    else:
        logger.error("Failed to write robustness analysis report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())