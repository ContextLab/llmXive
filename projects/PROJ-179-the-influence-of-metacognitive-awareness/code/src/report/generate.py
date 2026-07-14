import json
import logging
import os
import sys
from pathlib import Path
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {path}: {e}")
        return {}

def write_json_file(path: Path, data: dict) -> None:
    """Write a dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Report written to {path}")

def load_bootstrap_results(path: Path = None) -> dict:
    """Load bootstrap results from the specified path or default location."""
    if path is None:
        base_dir = Path(__file__).resolve().parents[3]
        path = base_dir / "data" / "results" / "bootstrap_results.json"
    return load_json_file(path)

def load_regression_results(path: Path = None) -> dict:
    """Load regression results from the specified path or default location."""
    if path is None:
        base_dir = Path(__file__).resolve().parents[3]
        path = base_dir / "data" / "results" / "regression_results.json"
    return load_json_file(path)

def load_diagnostics_results(path: Path = None) -> dict:
    """Load diagnostics results from the specified path or default location."""
    if path is None:
        base_dir = Path(__file__).resolve().parents[3]
        path = base_dir / "data" / "results" / "diagnostics_results.json"
    return load_json_file(path)

def load_robustness_results(path: Path = None) -> dict:
    """Load robustness results from the specified path or default location."""
    if path is None:
        base_dir = Path(__file__).resolve().parents[3]
        path = base_dir / "data" / "results" / "robustness_results.json"
    return load_json_file(path)

def determine_correlation_direction(r: float) -> str:
    """Determine the direction of correlation based on r value."""
    if r > 0:
        return "positive"
    elif r < 0:
        return "negative"
    else:
        return "no correlation"

def calculate_effect_size_magnitude(r: float) -> str:
    """Categorize effect size magnitude based on Cohen's guidelines for r."""
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def apply_bonferroni_correction(p_values: list, num_tests: int) -> list:
    """Apply Bonferroni correction to a list of p-values."""
    alpha = 0.05
    adjusted_alpha = alpha / num_tests
    corrected_p_values = [min(p * num_tests, 1.0) for p in p_values]
    return corrected_p_values, adjusted_alpha

def apply_bh_correction(p_values: list) -> list:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    bh_values = (np.arange(1, n + 1) / n) * 0.05
    
    # Find the largest k such that p_(k) <= bh_(k)
    mask = sorted_p_values <= bh_values
    if not np.any(mask):
        return [1.0] * n  # All non-significant
    
    k = np.max(np.where(mask)[0])
    threshold = sorted_p_values[k]
    
    # Apply correction: p_adj = p * n / rank
    corrected = np.zeros(n)
    for i, p in enumerate(p_values):
        rank = np.sum(p_values <= p)
        corrected[i] = min(p * n / rank, 1.0)
    
    return corrected.tolist()

def generate_primary_analysis_report(bootstrap_results: dict, 
                                     regression_results: dict = None,
                                     diagnostics_results: dict = None) -> dict:
    """Generate the primary analysis report combining correlation and regression data."""
    r = bootstrap_results.get("r", np.nan)
    p = bootstrap_results.get("p", np.nan)
    ci_lower = bootstrap_results.get("ci_lower", np.nan)
    ci_upper = bootstrap_results.get("ci_upper", np.nan)
    bootstrap_count = bootstrap_results.get("bootstrap_count", 1000)
    
    report = {
        "analysis_type": "primary_correlation",
        "correlation": {
            "r": float(r),
            "p_value": float(p),
            "confidence_interval": {
                "lower": float(ci_lower),
                "upper": float(ci_upper)
            },
            "direction": determine_correlation_direction(r),
            "magnitude": calculate_effect_size_magnitude(r),
            "bootstrap_count": bootstrap_count
        },
        "interpretation": {
            "significant": bool(p < 0.05),
            "description": f"Metacognitive awareness (Type-2 AUC) shows a {determine_correlation_direction(r)} "
                           f"correlation (r={r:.3f}, 95% CI [{ci_lower:.3f}, {ci_upper:.3f}]) "
                           f"with reality testing accuracy (d')."
        }
    }
    
    if regression_results:
        model_1 = regression_results.get("model_1", {})
        model_2 = regression_results.get("model_2", {})
        
        r_squared_1 = model_1.get("r_squared", 0)
        r_squared_2 = model_2.get("r_squared", 0)
        f_change = model_2.get("f_change", 0)
        p_f_change = model_2.get("p_f_change", 1.0)
        
        report["regression_summary"] = {
            "model_1_r_squared": float(r_squared_1),
            "model_2_r_squared": float(r_squared_2),
            "delta_r_squared": float(r_squared_2 - r_squared_1),
            "f_change": float(f_change),
            "p_f_change": float(p_f_change),
            "covariates_controlled": model_1.get("predictors", []),
            "metacognitive_added": True
        }
    
    if diagnostics_results:
        report["diagnostics_summary"] = {
            "normality_passed": diagnostics_results.get("normality_passed", False),
            "homoscedasticity_passed": diagnostics_results.get("homoscedasticity_passed", False),
            "collinearity_flagged": diagnostics_results.get("collinearity_flagged", False),
            "assumptions_met": (
                diagnostics_results.get("normality_passed", False) and
                diagnostics_results.get("homoscedasticity_passed", False) and
                not diagnostics_results.get("collinearity_flagged", False)
            )
        }
        
    return report

def generate_regression_analysis_report(regression_results: dict,
                                        diagnostics_results: dict) -> dict:
    """
    Generate the regression analysis report including coefficients, SE, t-stat, p-value,
    and diagnostic flags as required by T022.
    """
    model_1 = regression_results.get("model_1", {})
    model_2 = regression_results.get("model_2", {})
    
    # Extract coefficients for Model 2 (full model with metacognitive score)
    coefficients = model_2.get("coefficients", {})
    
    # Build detailed coefficient table
    coeff_table = []
    for term, stats in coefficients.items():
        coeff_entry = {
            "term": term,
            "coefficient": float(stats.get("coef", np.nan)),
            "std_error": float(stats.get("std_err", np.nan)),
            "t_statistic": float(stats.get("t", np.nan)),
            "p_value": float(stats.get("pvalue", np.nan)),
            "confidence_interval_95": [
                float(stats.get("conf_int", [[np.nan, np.nan]])[0][0]),
                float(stats.get("conf_int", [[np.nan, np.nan]])[0][1])
            ]
        }
        coeff_table.append(coeff_entry)
    
    # Extract model fit statistics
    r_squared = model_2.get("r_squared", 0)
    adj_r_squared = model_2.get("adj_r_squared", 0)
    f_statistic = model_2.get("f_statistic", 0)
    p_f_stat = model_2.get("f_pvalue", 1.0)
    
    # Delta R2 and F-change (comparing Model 1 and Model 2)
    r_squared_1 = model_1.get("r_squared", 0)
    delta_r2 = float(r_squared - r_squared_1)
    f_change = float(model_2.get("f_change", 0))
    p_f_change = float(model_2.get("p_f_change", 1.0))
    
    report = {
        "analysis_type": "hierarchical_regression",
        "model_comparison": {
            "model_1": {
                "predictors": model_1.get("predictors", []),
                "r_squared": float(r_squared_1),
                "adj_r_squared": float(model_1.get("adj_r_squared", 0))
            },
            "model_2": {
                "predictors": model_2.get("predictors", []),
                "r_squared": float(r_squared),
                "adj_r_squared": float(adj_r_squared)
            },
            "delta_r_squared": delta_r2,
            "f_change": f_change,
            "p_f_change": p_f_change,
            "interpretation": f"Adding metacognitive awareness (Type-2 AUC) to the model "
                              f"explained an additional {delta_r2:.3%} of variance in reality testing accuracy "
                              f"(F-change={f_change:.3f}, p={p_f_change:.4f})."
        },
        "full_model_coefficients": coeff_table,
        "model_fit_statistics": {
            "r_squared": float(r_squared),
            "adjusted_r_squared": float(adj_r_squared),
            "f_statistic": float(f_statistic),
            "p_f_statistic": float(p_f_stat),
            "sample_size": model_2.get("n_obs", 0)
        },
        "diagnostics": {
            "normality_of_residuals": {
                "passed": diagnostics_results.get("normality_passed", False),
                "statistic": diagnostics_results.get("shapiro_statistic", np.nan),
                "p_value": diagnostics_results.get("shapiro_p_value", np.nan)
            },
            "homoscedasticity": {
                "passed": diagnostics_results.get("homoscedasticity_passed", False),
                "statistic": diagnostics_results.get("bp_statistic", np.nan),
                "p_value": diagnostics_results.get("bp_p_value", np.nan)
            },
            "collinearity": {
                "flagged": diagnostics_results.get("collinearity_flagged", False),
                "max_vif": diagnostics_results.get("max_vif", 0),
                "vif_details": diagnostics_results.get("vif_details", {})
            },
            "assumptions_satisfied": (
                diagnostics_results.get("normality_passed", False) and
                diagnostics_results.get("homoscedasticity_passed", False) and
                not diagnostics_results.get("collinearity_flagged", False)
            )
        },
        "n_minus_1_model_used": regression_results.get("n_minus_1_model", False),
        "notes": [
            "Model 1 controls for age, gender, and working memory (if available).",
            "Model 2 adds metacognitive awareness (Type-2 AUC) as the predictor of interest.",
            "Diagnostics indicate whether regression assumptions are met."
        ]
    }
    
    return report

def generate_robustness_analysis_report(robustness_results: dict) -> dict:
    """Generate the robustness analysis report for modality-specific effects."""
    visual_results = robustness_results.get("visual", {})
    auditory_results = robustness_results.get("auditory", {})
    
    # Extract p-values for correction
    p_values = []
    if visual_results.get("p_value") is not None:
        p_values.append(visual_results["p_value"])
    if auditory_results.get("p_value") is not None:
        p_values.append(auditory_results["p_value"])
    
    corrected_p_values = apply_bh_correction(p_values) if len(p_values) > 1 else p_values
    
    report = {
        "analysis_type": "modality_specific_robustness",
        "visual_stimuli": {
            "r": float(visual_results.get("r", np.nan)),
            "p_value_raw": float(visual_results.get("p_value", np.nan)),
            "p_value_corrected": float(corrected_p_values[0]) if corrected_p_values else np.nan,
            "ci_lower": float(visual_results.get("ci_lower", np.nan)),
            "ci_upper": float(visual_results.get("ci_upper", np.nan)),
            "sample_size": visual_results.get("n", 0),
            "significant_raw": bool(visual_results.get("p_value", 1.0) < 0.05),
            "significant_corrected": bool(corrected_p_values[0] < 0.05) if corrected_p_values else False
        },
        "auditory_stimuli": {
            "r": float(auditory_results.get("r", np.nan)),
            "p_value_raw": float(auditory_results.get("p_value", np.nan)),
            "p_value_corrected": float(corrected_p_values[1]) if len(corrected_p_values) > 1 else np.nan,
            "ci_lower": float(auditory_results.get("ci_lower", np.nan)),
            "ci_upper": float(auditory_results.get("ci_upper", np.nan)),
            "sample_size": auditory_results.get("n", 0),
            "significant_raw": bool(auditory_results.get("p_value", 1.0) < 0.05),
            "significant_corrected": bool(corrected_p_values[1] < 0.05) if len(corrected_p_values) > 1 else False
        },
        "multiple_comparison_correction": {
            "method": "Benjamini-Hochberg",
            "num_tests": len(p_values),
            "alpha": 0.05
        },
        "interpretation": {
            "modality_specific": bool(
                visual_results.get("r", 0) != auditory_results.get("r", 0) and
                (visual_results.get("significant_raw", False) != auditory_results.get("significant_raw", False))
            ),
            "description": "Comparison of metacognitive-awareness/reality-testing correlation across visual and auditory modalities."
        }
    }
    
    return report

def write_report(report: dict, output_path: Path) -> None:
    """Write the report to a JSON file."""
    write_json_file(output_path, report)

def main():
    """Main function to generate all analysis reports."""
    base_dir = Path(__file__).resolve().parents[3]
    results_dir = base_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing results
    bootstrap_results = load_bootstrap_results(base_dir / "data" / "results" / "bootstrap_results.json")
    regression_results = load_regression_results(base_dir / "data" / "results" / "regression_results.json")
    diagnostics_results = load_diagnostics_results(base_dir / "data" / "results" / "diagnostics_results.json")
    robustness_results = load_robustness_results(base_dir / "data" / "results" / "robustness_results.json")
    
    # Generate Primary Analysis Report
    primary_report = generate_primary_analysis_report(bootstrap_results, regression_results, diagnostics_results)
    write_report(primary_report, base_dir / "data" / "results" / "primary_analysis.json")
    
    # Generate Regression Analysis Report (T022 requirement)
    if regression_results:
        regression_report = generate_regression_analysis_report(regression_results, diagnostics_results)
        write_report(regression_report, base_dir / "data" / "results" / "regression_analysis.json")
    else:
        logger.warning("Regression results not found. Skipping regression analysis report.")
    
    # Generate Robustness Analysis Report
    if robustness_results:
        robustness_report = generate_robustness_analysis_report(robustness_results)
        write_report(robustness_report, base_dir / "data" / "results" / "robustness_analysis.json")
    else:
        logger.warning("Robustness results not found. Skipping robustness analysis report.")
    
    logger.info("All reports generated successfully.")

if __name__ == "__main__":
    main()