import json
import logging
import os
import sys
from pathlib import Path
import numpy as np

from code.src.analysis.bootstrap import run_bootstrap_analysis
from code.src.analysis.regression import run_regression_analysis
from code.src.analysis.diagnostics import run_diagnostics
from code.src.analysis.robustness import run_robustness_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(filepath):
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON file {filepath}: {e}")
        return None

def write_json_file(filepath, data):
    """Write data to a JSON file."""
    try:
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Report written to {filepath}")
    except Exception as e:
        logger.error(f"Error writing JSON file {filepath}: {e}")
        raise

def load_bootstrap_results(filepath="data/results/bootstrap_config.json"):
    """Load bootstrap results from the specified file."""
    return load_json_file(filepath)

def load_regression_results(filepath="data/results/regression_analysis.json"):
    """Load regression results from the specified file."""
    return load_json_file(filepath)

def load_diagnostics_results(filepath="data/results/diagnostics.json"):
    """Load diagnostics results from the specified file."""
    return load_json_file(filepath)

def load_robustness_results(filepath="data/results/robustness_analysis.json"):
    """Load robustness results from the specified file."""
    return load_json_file(filepath)

def determine_correlation_direction(r_value):
    """Determine the direction of correlation based on r-value."""
    if r_value > 0:
        return "positive"
    elif r_value < 0:
        return "negative"
    else:
        return "no correlation"

def calculate_effect_size_magnitude(r_value):
    """Calculate the magnitude of effect size based on Cohen's guidelines for r."""
    abs_r = abs(r_value)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def apply_bonferroni_correction(p_values, n_tests):
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values (list): List of p-values to correct.
        n_tests (int): Number of tests performed.
        
    Returns:
        list: Corrected p-values.
    """
    corrected_p_values = []
    for p in p_values:
        corrected_p = min(p * n_tests, 1.0)
        corrected_p_values.append(corrected_p)
    return corrected_p_values

def apply_bh_correction(p_values):
    """
    Apply Benjamini-Hochberg (FDR) correction for multiple comparisons.
    
    Args:
        p_values (list): List of p-values to correct.
        
    Returns:
        list: Corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * sorted_p_values[-1] if sorted_p_values[-1] > 0 else 0
    
    # Find the largest k where p_k <= critical value
    # We'll use the standard BH procedure: find max k such that p_(k) <= (k/m) * alpha
    # But for reporting corrected p-values, we calculate adjusted p-values
    # Adjusted p-value for p_(i) = min_{j>=i} (m/j * p_(j))
    
    adjusted_p_values = np.ones(n)
    current_min = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adjusted = (n / rank) * sorted_p_values[i]
        if adjusted < current_min:
            current_min = adjusted
        else:
            adjusted = current_min
        # Ensure not greater than 1
        adjusted = min(adjusted, 1.0)
        adjusted_p_values[i] = adjusted
    
    # Restore original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted_p_values
    
    return final_adjusted.tolist()

def generate_primary_analysis_report(bootstrap_results):
    """Generate the primary analysis report."""
    if not bootstrap_results:
        return {"error": "No bootstrap results provided"}
    
    r = bootstrap_results.get("r", np.nan)
    p = bootstrap_results.get("p", np.nan)
    ci_lower = bootstrap_results.get("ci_lower", np.nan)
    ci_upper = bootstrap_results.get("ci_upper", np.nan)
    bootstrap_count = bootstrap_results.get("bootstrap_count", 1000)
    
    report = {
        "analysis_type": "primary_correlation",
        "metacognitive_metric": "Type-2 AUC (training split)",
        "reality_testing_metric": "d' (test split)",
        "design": "Hold-Out (70/30 split)",
        "correlation": {
            "r": float(r),
            "p_value": float(p),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "direction": determine_correlation_direction(r),
            "magnitude": calculate_effect_size_magnitude(r)
        },
        "bootstrap_config": {
            "count": bootstrap_count
        },
        "interpretation": {
            "significant": float(p) < 0.05,
            "description": f"Metacognitive awareness (Type-2 AUC) shows a {determine_correlation_direction(r)} correlation with reality testing accuracy (d')."
        }
    }
    
    return report

def generate_regression_analysis_report(regression_results, diagnostics_results=None):
    """Generate the hierarchical regression analysis report."""
    if not regression_results:
        return {"error": "No regression results provided"}
    
    model_1 = regression_results.get("model_1", {})
    model_2 = regression_results.get("model_2", {})
    
    r_squared_1 = model_1.get("r_squared", 0)
    r_squared_2 = model_2.get("r_squared", 0)
    f_change = model_2.get("f_change", 0)
    p_f_change = model_2.get("p_f_change", 1.0)
    
    report = {
        "analysis_type": "hierarchical_regression",
        "dependent_variable": "Reality Testing Accuracy (d')",
        "independent_variable": "Metacognitive Awareness (Type-2 AUC)",
        "covariates": model_1.get("predictors", []),
        "model_1": {
            "predictors": model_1.get("predictors", []),
            "r_squared": float(r_squared_1),
            "adjusted_r_squared": float(model_1.get("adjusted_r_squared", 0))
        },
        "model_2": {
            "predictors": model_2.get("predictors", []),
            "r_squared": float(r_squared_2),
            "adjusted_r_squared": float(model_2.get("adjusted_r_squared", 0))
        },
        "incremental_variance": {
            "delta_r_squared": float(r_squared_2 - r_squared_1),
            "f_change": float(f_change),
            "p_f_change": float(p_f_change),
            "significant": float(p_f_change) < 0.05
        },
        "diagnostics": diagnostics_results if diagnostics_results else {}
    }
    
    return report

def generate_robustness_analysis_report(robustness_results):
    """
    Generate the robustness analysis report with multiple comparison correction.
    
    Args:
        robustness_results (dict): Results from the robustness analysis containing
                                   correlations for different modalities.
                                   
    Returns:
        dict: Report with corrected p-values using Bonferroni and BH methods.
    """
    if not robustness_results:
        return {"error": "No robustness results provided"}
    
    # Extract results for each modality
    modalities = robustness_results.get("modalities", {})
    
    if not modalities:
        return {"error": "No modality results found in robustness data"}
    
    # Collect p-values for correction
    p_values = []
    modality_names = []
    
    for modality, data in modalities.items():
        p_val = data.get("p_value", np.nan)
        if not np.isnan(p_val):
            p_values.append(float(p_val))
            modality_names.append(modality)
    
    n_tests = len(p_values)
    
    # Apply corrections
    bonferroni_corrected = apply_bonferroni_correction(p_values, n_tests) if n_tests > 0 else []
    bh_corrected = apply_bh_correction(p_values) if n_tests > 0 else []
    
    # Build the report
    report = {
        "analysis_type": "modality_specific_robustness",
        "multiple_comparison_correction": {
            "method": "Bonferroni and Benjamini-Hochberg (FDR)",
            "n_tests": n_tests,
            "family_wise_error_rate": 0.05
        },
        "uncorrected_results": {},
        "corrected_results": {
            "bonferroni": {},
            "benjamini_hochberg": {}
        },
        "summary": {
            "significant_uncorrected": 0,
            "significant_bonferroni": 0,
            "significant_bh": 0
        }
    }
    
    # Populate results
    for i, modality in enumerate(modality_names):
        data = modalities[modality]
        r = data.get("r", np.nan)
        p_uncorrected = float(data.get("p_value", np.nan))
        ci_lower = data.get("ci_lower", np.nan)
        ci_upper = data.get("ci_upper", np.nan)
        
        report["uncorrected_results"][modality] = {
            "r": float(r) if not np.isnan(r) else None,
            "p_value": p_uncorrected,
            "ci_95_lower": float(ci_lower) if not np.isnan(ci_lower) else None,
            "ci_95_upper": float(ci_upper) if not np.isnan(ci_upper) else None,
            "direction": determine_correlation_direction(r) if not np.isnan(r) else "unknown",
            "magnitude": calculate_effect_size_magnitude(r) if not np.isnan(r) else "unknown"
        }
        
        # Add corrected p-values
        if i < len(bonferroni_corrected):
            p_bonf = bonferroni_corrected[i]
            report["corrected_results"]["bonferroni"][modality] = {
                "p_value": p_bonf,
                "significant": p_bonf < 0.05
            }
            if p_bonf < 0.05:
                report["summary"]["significant_bonferroni"] += 1
        
        if i < len(bh_corrected):
            p_bh = bh_corrected[i]
            report["corrected_results"]["benjamini_hochberg"][modality] = {
                "p_value": p_bh,
                "significant": p_bh < 0.05
            }
            if p_bh < 0.05:
                report["summary"]["significant_bh"] += 1
        
        if p_uncorrected < 0.05:
            report["summary"]["significant_uncorrected"] += 1
    
    report["interpretation"] = {
        "primary_finding": f"Analysis of {n_tests} modality-specific correlations.",
        "correction_applied": f"Bonferroni (family-wise) and BH (FDR) corrections applied to control for multiple comparisons.",
        "conclusion": (
            f"Uncorrected: {report['summary']['significant_uncorrected']} significant, "
            f"Bonferroni: {report['summary']['significant_bonferroni']} significant, "
            f"BH-FDR: {report['summary']['significant_bh']} significant."
        )
    }
    
    return report

def write_report(filepath, report_data):
    """Write a report to a JSON file."""
    write_json_file(filepath, report_data)

def main():
    """Main function to generate all analysis reports."""
    logger.info("Starting report generation...")
    
    # Paths
    base_dir = Path("projects/PROJ-179-the-influence-of-metacognitive-awareness")
    results_dir = base_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load results
    bootstrap_results = load_json_file(results_dir / "bootstrap_config.json")
    regression_results = load_json_file(results_dir / "regression_analysis.json")
    diagnostics_results = load_json_file(results_dir / "diagnostics.json")
    robustness_results = load_json_file(results_dir / "robustness_analysis_raw.json")
    
    # Generate Primary Analysis Report
    if bootstrap_results:
        primary_report = generate_primary_analysis_report(bootstrap_results)
        write_report(results_dir / "primary_analysis.json", primary_report)
        logger.info("Primary analysis report generated.")
    else:
        logger.warning("Bootstrap results not found. Skipping primary analysis report.")
    
    # Generate Regression Analysis Report
    if regression_results:
        reg_report = generate_regression_analysis_report(regression_results, diagnostics_results)
        write_report(results_dir / "regression_analysis.json", reg_report)
        logger.info("Regression analysis report generated.")
    else:
        logger.warning("Regression results not found. Skipping regression analysis report.")
    
    # Generate Robustness Analysis Report with Corrections
    if robustness_results:
        robust_report = generate_robustness_analysis_report(robustness_results)
        write_report(results_dir / "robustness_analysis.json", robust_report)
        logger.info("Robustness analysis report with corrections generated.")
    else:
        logger.warning("Robustness results not found. Skipping robustness analysis report.")
    
    logger.info("Report generation complete.")

if __name__ == "__main__":
    main()