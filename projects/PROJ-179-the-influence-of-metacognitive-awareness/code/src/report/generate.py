import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.env_config import load_config, setup_logging

# --- Helper Functions ---

def load_json_file(filepath):
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in file: {filepath}")
        return None

def write_json_file(data, filepath):
    """Write data to a JSON file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Report written to {filepath}")

def load_bootstrap_results(filepath):
    """Load bootstrap results for correlation analysis."""
    return load_json_file(filepath)

def load_regression_results(filepath):
    """Load regression analysis results."""
    return load_json_file(filepath)

def load_diagnostics_results(filepath):
    """Load diagnostics results."""
    return load_json_file(filepath)

def determine_correlation_direction(r_value):
    """Determine the direction of correlation based on r_value."""
    if r_value > 0.1:
        return "positive"
    elif r_value < -0.1:
        return "negative"
    else:
        return "negligible"

def calculate_effect_size_magnitude(r_value):
    """Calculate the magnitude of effect size based on Cohen's guidelines."""
    abs_r = abs(r_value)
    if abs_r >= 0.5:
        return "large"
    elif abs_r >= 0.3:
        return "medium"
    elif abs_r >= 0.1:
        return "small"
    else:
        return "negligible"

def apply_bonferroni_correction(p_values, family_size):
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values (list of float): List of raw p-values.
        family_size (int): The number of tests in the family (total comparisons).
        
    Returns:
        list of float: Corrected p-values (capped at 1.0).
    """
    if family_size <= 0:
        return p_values
    
    corrected = [min(p * family_size, 1.0) for p in p_values]
    return corrected

def apply_bh_correction(p_values):
    """
    Apply Benjamini-Hochberg (FDR) correction for multiple comparisons.
    
    Args:
        p_values (list of float): List of raw p-values.
        
    Returns:
        list of float: Corrected p-values (capped at 1.0).
    """
    n = len(p_values)
    if n == 0:
        return []
        
    # Sort p-values and keep track of original indices
    indexed_p_values = list(enumerate(p_values))
    sorted_p_values = sorted(indexed_p_values, key=lambda x: x[1])
    
    corrected = [0.0] * n
    rank = n
    
    # Calculate BH critical values
    # q_i = (i / m) * alpha, but we compute adjusted p-values
    # adjusted_p_i = min( (m/i) * p_i, adjusted_p_{i+1} )
    
    last_corrected = 1.0
    for rank, (original_idx, p_val) in enumerate(sorted_p_values, 1):
        # BH adjustment: p_adj = p * m / rank
        adj_p = min(p_val * n / rank, last_corrected, 1.0)
        corrected[original_idx] = adj_p
        last_corrected = adj_p
        
    return corrected

# --- Report Generation Functions ---

def generate_primary_analysis_report(correlation_results, bootstrap_results, config):
    """
    Generate the primary analysis report with correlation metrics and CI.
    
    Args:
        correlation_results (dict): Results from correlation analysis.
        bootstrap_results (dict): Results from bootstrap analysis.
        config (AppConfig): Configuration object.
        
    Returns:
        dict: The generated report.
    """
    report = {
        "analysis_type": "Primary Correlation Analysis",
        "method": "Hold-Out Accuracy (70/30 Train/Test)",
        "metrics": {
            "pearson_r": correlation_results.get("correlation", np.nan),
            "p_value": correlation_results.get("p_value", np.nan),
            "ci_95_lower": correlation_results.get("ci_lower", np.nan),
            "ci_95_upper": correlation_results.get("ci_upper", np.nan),
            "n_resamples": correlation_results.get("n_resamples", 0),
            "direction": determine_correlation_direction(correlation_results.get("correlation", 0)),
            "effect_size_magnitude": calculate_effect_size_magnitude(correlation_results.get("correlation", 0))
        },
        "bootstrap_config": {
            "count": bootstrap_results.get("n_resamples", 1000) if bootstrap_results else 1000,
            "runtime_warning": bootstrap_results.get("runtime_warning", False) if bootstrap_results else False
        } if bootstrap_results else None
    }
    return report

def generate_regression_analysis_report(regression_results, diagnostics_results, config):
    """
    Generate the hierarchical regression analysis report.
    
    Args:
        regression_results (dict): Results from regression analysis.
        diagnostics_results (dict): Results from diagnostics checks.
        config (AppConfig): Configuration object.
        
    Returns:
        dict: The generated report.
    """
    report = {
        "analysis_type": "Hierarchical Regression Analysis",
        "model_1": regression_results.get("model_1", {}),
        "model_2": regression_results.get("model_2", {}),
        "delta_r_squared": regression_results.get("delta_r_squared", np.nan),
        "f_change": regression_results.get("f_change", np.nan),
        "n_minus_1_model_used": regression_results.get("n_minus_1_model_used", False),
        "diagnostics": {
            "normality": diagnostics_results.get("normality", {}) if diagnostics_results else {},
            "homoscedasticity": diagnostics_results.get("homoscedasticity", {}) if diagnostics_results else {},
            "collinearity": diagnostics_results.get("collinearity", {}) if diagnostics_results else {},
            "all_passed": diagnostics_results.get("all_passed", False) if diagnostics_results else False
        } if diagnostics_results else {}
    }
    return report

def generate_robustness_analysis_report(robustness_results, config):
    """
    Generate the robustness analysis report with modality-specific correlations
    and multiple comparison corrections (Bonferroni and Benjamini-Hochberg).
    
    Args:
        robustness_results (dict): Results from robustness analysis (dict of modality -> results).
        config (AppConfig): Configuration object.
        
    Returns:
        dict: The generated report with corrected p-values.
    """
    if not robustness_results:
        logging.warning("No robustness results provided.")
        return {"error": "No robustness results provided"}

    # Extract raw p-values and correlations
    modalities = list(robustness_results.keys())
    raw_p_values = []
    correlations = []
    
    report_data = {
        "analysis_type": "Modality-Specific Robustness Analysis",
        "method": "Hold-Out Accuracy (70/30) per Modality",
        "corrections_applied": ["Bonferroni", "Benjamini-Hochberg (FDR)"],
        "results": {}
    }
    
    for modality, results in robustness_results.items():
        if results and results.get("status") == "success":
            p_val = results.get("p_value", np.nan)
            r_val = results.get("correlation", np.nan)
            raw_p_values.append(p_val)
            correlations.append(r_val)
            
            report_data["results"][modality] = {
                "pearson_r": r_val,
                "p_value": p_val,
                "ci_95_lower": results.get("ci_lower", np.nan),
                "ci_95_upper": results.get("ci_upper", np.nan),
                "n_resamples": results.get("n_resamples", 0),
                "direction": determine_correlation_direction(r_val),
                "effect_size_magnitude": calculate_effect_size_magnitude(r_val)
            }
    
    family_size = len(raw_p_values)
    
    if family_size > 0:
        # Apply Bonferroni correction
        bonf_corrected = apply_bonferroni_correction(raw_p_values, family_size)
        
        # Apply Benjamini-Hochberg correction
        bh_corrected = apply_bh_correction(raw_p_values)
        
        # Update report with corrected p-values
        for i, modality in enumerate(modalities):
            if modality in report_data["results"]:
                report_data["results"][modality]["p_value_bonferroni"] = bonf_corrected[i]
                report_data["results"][modality]["p_value_bh"] = bh_corrected[i]
                
                # Determine significance after correction (alpha = 0.05)
                alpha = 0.05
                report_data["results"][modality]["significant_bonferroni"] = bonf_corrected[i] < alpha
                report_data["results"][modality]["significant_bh"] = bh_corrected[i] < alpha
    else:
        logging.warning("No valid results to correct for multiple comparisons.")

    return report_data

def write_report(report, output_path):
    """Write the report to a JSON file."""
    write_json_file(report, output_path)

def main():
    """Main entry point for report generation."""
    config = load_config()
    logger = setup_logging(config)
    logger.info("Starting robustness analysis report generation (T028)...")
    
    # Paths
    base_dir = config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness")
    results_dir = Path(base_dir) / config.get("paths", {}).get("results", "data/results")
    
    # Load robustness results
    robustness_path = Path(base_dir) / "data" / "results" / "robustness_raw.json"
    # Fallback if raw file doesn't exist, try to load from individual modality files if structure differs
    # For now, assume the robustness script writes to robustness_raw.json or similar
    # If the robustness script (T027) writes directly to the final path, we might just need to read it.
    # However, T028 specifically asks to update the report to apply corrections.
    # We assume T027 writes uncorrected results to data/results/robustness_raw.json or similar.
    # Let's check if the robustness script writes to a specific location.
    # Based on T027 description, it runs the pipeline on subsets.
    # We will assume the robustness analysis results are in data/results/robustness_analysis_raw.json
    # or we need to construct them from the modality-specific files if they exist.
    # Given the task is to update `src/report/generate.py`, we assume the data is available.
    
    # Attempt to load robustness results
    # If T027 writes to data/results/robustness_analysis.json directly, we might need to read that,
    # but T028 is about *updating* the report generation to apply corrections.
    # So we assume the input to this function is the raw uncorrected results.
    # Let's assume the robustness script outputs to data/results/robustness_raw.json
    robustness_input_path = Path(base_dir) / "data" / "results" / "robustness_raw.json"
    
    if not robustness_input_path.exists():
        # Fallback: check if the robustness script already wrote to the final location
        # and we just need to re-process? No, T028 is the one applying corrections.
        # If the file doesn't exist, we can't generate the report.
        logger.error(f"Robustness results not found at {robustness_input_path}")
        # Try to find any robustness related json
        potential_files = list((Path(base_dir) / "data" / "results").glob("*robustness*.json"))
        if potential_files:
            robustness_input_path = potential_files[0]
            logger.info(f"Using fallback file: {robustness_input_path}")
        else:
            logger.error("No robustness results found. Cannot generate report.")
            return 1

    robustness_data = load_json_file(robustness_input_path)
    
    if not robustness_data:
        logger.error("Failed to load robustness results.")
        return 1
    
    # Generate report with corrections
    report = generate_robustness_analysis_report(robustness_data, config)
    
    # Write output
    output_path = results_dir / "robustness_analysis.json"
    write_report(report, output_path)
    
    logger.info("Robustness analysis report generated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
