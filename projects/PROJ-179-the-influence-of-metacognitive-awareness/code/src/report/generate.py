import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Importing CONFIG from the project's config module to handle path resolution
# We assume the config module is available as per the project structure
try:
    from code.config.env_config import load_config, setup_logging, AppConfig
    CONFIG = load_config()
except ImportError:
    # Fallback for direct execution or different import context
    import importlib.util
    spec = importlib.util.spec_from_file_location("env_config", "code/config/env_config.py")
    if spec and spec.loader:
        env_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(env_config)
        load_config = env_config.load_config
        CONFIG = load_config()
    else:
        CONFIG = {}

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return {}

def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Write a dictionary to a JSON file."""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4, default=str)
        logger.info(f"Successfully wrote JSON to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing JSON to {file_path}: {e}")
        return False

def load_bootstrap_results(file_path: str = None) -> Dict[str, Any]:
    """Load bootstrap results from a JSON file."""
    if file_path is None:
        # Default path relative to project root
        base_dir = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
        file_path = base_dir / "data/results/bootstrap_results.json"
    return load_json_file(str(file_path))

def load_diagnostics_results(file_path: str = None) -> Dict[str, Any]:
    """Load diagnostics results from a JSON file."""
    if file_path is None:
        base_dir = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
        file_path = base_dir / "data/results/diagnostics_results.json"
    return load_json_file(str(file_path))

def determine_correlation_direction(r: float) -> str:
    """Determine the direction of the correlation."""
    if r > 0:
        return "positive"
    elif r < 0:
        return "negative"
    else:
        return "none"

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

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of p-values to correct.
        alpha: Significance level (default 0.05).
        
    Returns:
        List of corrected p-values (adjusted).
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    # Bonferroni: adjusted p = p * n, capped at 1.0
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def apply_bh_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg (FDR) correction for multiple comparisons.
    
    Args:
        p_values: List of p-values to correct.
        alpha: Significance level (default 0.05).
        
    Returns:
        List of adjusted p-values (q-values).
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    # Sort p-values and keep track of original indices
    indexed_p_values = list(enumerate(p_values))
    sorted_p_values = sorted(indexed_p_values, key=lambda x: x[1])
    
    adjusted_p_values = [0.0] * n_tests
    
    # Calculate BH adjusted p-values
    # q_i = p_i * n / rank_i
    # Then ensure monotonicity: q_i = min(q_i, q_{i+1})
    
    ranks = [i + 1 for i in range(n_tests)]
    raw_adjusted = [p * n_tests / rank for (_, p), rank in zip(sorted_p_values, ranks)]
    
    # Enforce monotonicity (cumulative minimum from the end)
    # Start from the largest rank (smallest p) and move backwards
    # Actually, BH requires q_i <= q_{i+1} for sorted p.
    # We compute cumulative min from the end.
    cumulative_min = [0.0] * n_tests
    current_min = 1.0
    for i in range(n_tests - 1, -1, -1):
        current_min = min(current_min, raw_adjusted[i])
        cumulative_min[i] = current_min
        
    # Map back to original order
    for original_idx, adjusted_val in zip([idx for idx, _ in indexed_p_values], cumulative_min):
        adjusted_p_values[original_idx] = min(adjusted_val, 1.0)
        
    return adjusted_p_values

def generate_primary_analysis_report(bootstrap_results: Dict[str, Any], 
                                    output_path: str = None) -> Dict[str, Any]:
    """Generate the primary analysis report."""
    if output_path is None:
        base_dir = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
        output_path = base_dir / "data/results/primary_analysis.json"
        
    report = {
        "analysis_type": "primary_correlation",
        "method": "Hold-Out Accuracy (70/30 Split)",
        "results": {}
    }
    
    if bootstrap_results:
        r = bootstrap_results.get("r", np.nan)
        p = bootstrap_results.get("p", np.nan)
        ci_lower = bootstrap_results.get("ci_lower", np.nan)
        ci_upper = bootstrap_results.get("ci_upper", np.nan)
        bootstrap_count = bootstrap_results.get("bootstrap_count", 1000)
        
        report["results"] = {
            "pearson_r": float(r) if not np.isnan(r) else None,
            "p_value": float(p) if not np.isnan(p) else None,
            "confidence_interval": {
                "lower": float(ci_lower) if not np.isnan(ci_lower) else None,
                "upper": float(ci_upper) if not np.isnan(ci_upper) else None,
                "level": 0.95
            },
            "bootstrap_count": bootstrap_count,
            "direction": determine_correlation_direction(float(r)) if not np.isnan(r) else "unknown",
            "magnitude": calculate_effect_size_magnitude(float(r)) if not np.isnan(r) else "unknown"
        }
        
        # Determine significance
        if not np.isnan(p) and p < 0.05:
            report["results"]["significant_at_0.05"] = True
        else:
            report["results"]["significant_at_0.05"] = False
            
    success = write_json_file(str(output_path), report)
    if success:
        logger.info(f"Primary analysis report written to {output_path}")
    return report

def generate_regression_analysis_report(regression_results: Dict[str, Any], 
                                        diagnostics_results: Dict[str, Any],
                                        output_path: str = None) -> Dict[str, Any]:
    """Generate the regression analysis report."""
    if output_path is None:
        base_dir = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
        output_path = base_dir / "data/results/regression_analysis.json"
        
    report = {
        "analysis_type": "hierarchical_regression",
        "model_1": {},
        "model_2": {},
        "incremental_variance": {},
        "diagnostics": {},
        "assumptions_met": False
    }
    
    # Model 1 (Controls)
    model_1 = regression_results.get("model_1", {})
    report["model_1"] = {
        "predictors": model_1.get("predictors", []),
        "r_squared": model_1.get("r_squared"),
        "adjusted_r_squared": model_1.get("adjusted_r_squared"),
        "f_statistic": model_1.get("f_statistic"),
        "p_value": model_1.get("p_value"),
        "coefficients": model_1.get("coefficients", {})
    }
    
    # Model 2 (Controls + Metacognition)
    model_2 = regression_results.get("model_2", {})
    report["model_2"] = {
        "predictors": model_2.get("predictors", []),
        "r_squared": model_2.get("r_squared"),
        "adjusted_r_squared": model_2.get("adjusted_r_squared"),
        "f_statistic": model_2.get("f_statistic"),
        "p_value": model_2.get("p_value"),
        "coefficients": model_2.get("coefficients", {})
    }
    
    # Incremental Variance
    r2_change = model_2.get("r_squared", 0) - model_1.get("r_squared", 0)
    report["incremental_variance"] = {
        "delta_r_squared": r2_change,
        "f_change": model_2.get("f_change"),
        "p_change": model_2.get("p_change"),
        "n_model_used": model_2.get("n_model_used", False)
    }
    
    # Diagnostics
    if diagnostics_results:
        report["diagnostics"] = {
            "normality": {
                "statistic": diagnostics_results.get("normality", {}).get("statistic"),
                "p_value": diagnostics_results.get("normality", {}).get("p_value"),
                "passed": diagnostics_results.get("normality", {}).get("is_normal", False)
            },
            "homoscedasticity": {
                "statistic": diagnostics_results.get("homoscedasticity", {}).get("statistic"),
                "p_value": diagnostics_results.get("homoscedasticity", {}).get("p_value"),
                "passed": diagnostics_results.get("homoscedasticity", {}).get("is_homoscedastic", False)
            },
            "collinearity": {
                "vif_scores": diagnostics_results.get("collinearity", {}).get("vif_scores", {}),
                "max_vif": diagnostics_results.get("collinearity", {}).get("max_vif"),
                "flagged": diagnostics_results.get("collinearity", {}).get("collinearity_flag", False)
            }
        }
        
        # Check assumptions
        normality_ok = diagnostics_results.get("normality", {}).get("is_normal", False)
        homoscedasticity_ok = diagnostics_results.get("homoscedasticity", {}).get("is_homoscedastic", False)
        collinearity_ok = not diagnostics_results.get("collinearity", {}).get("collinearity_flag", False)
        
        report["assumptions_met"] = normality_ok and homoscedasticity_ok and collinearity_ok
        
    success = write_json_file(str(output_path), report)
    if success:
        logger.info(f"Regression analysis report written to {output_path}")
    return report

def generate_robustness_analysis_report(visual_results: Dict[str, Any], 
                                        auditory_results: Dict[str, Any],
                                        output_path: str = None) -> Dict[str, Any]:
    """
    Generate the robustness analysis report with multiple comparison correction.
    
    This function applies Bonferroni or Benjamini-Hochberg correction to the p-values
    from the modality-specific analyses (visual and auditory).
    """
    if output_path is None:
        base_dir = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
        output_path = base_dir / "data/results/robustness_analysis.json"
        
    report = {
        "analysis_type": "modality_specific_robustness",
        "correction_method": "Bonferroni",
        "results": {
            "visual": {},
            "auditory": {}
        },
        "multiple_comparison_correction": {}
    }
    
    # Collect raw p-values
    raw_p_values = []
    modality_labels = []
    
    if visual_results:
        p_val = visual_results.get("p", np.nan)
        if not np.isnan(p_val):
            raw_p_values.append(float(p_val))
            modality_labels.append("visual")
            
    if auditory_results:
        p_val = auditory_results.get("p", np.nan)
        if not np.isnan(p_val):
            raw_p_values.append(float(p_val))
            modality_labels.append("auditory")
    
    # Apply corrections
    corrected_p_values = {}
    
    if len(raw_p_values) > 0:
        # Bonferroni Correction
        bonf_corrected = apply_bonferroni_correction(raw_p_values)
        for i, label in enumerate(modality_labels):
            corrected_p_values[label] = {
                "bonferroni": bonf_corrected[i]
            }
        
        # Benjamini-Hochberg (FDR) Correction
        bh_corrected = apply_bh_correction(raw_p_values)
        for i, label in enumerate(modality_labels):
            corrected_p_values[label]["bh_fdr"] = bh_corrected[i]
    else:
        logger.warning("No valid p-values found for correction.")
    
    # Build the report
    if visual_results:
        r = visual_results.get("r", np.nan)
        p = visual_results.get("p", np.nan)
        ci_lower = visual_results.get("ci_lower", np.nan)
        ci_upper = visual_results.get("ci_upper", np.nan)
        
        report["results"]["visual"] = {
            "pearson_r": float(r) if not np.isnan(r) else None,
            "p_value": float(p) if not np.isnan(p) else None,
            "confidence_interval": {
                "lower": float(ci_lower) if not np.isnan(ci_lower) else None,
                "upper": float(ci_upper) if not np.isnan(ci_upper) else None,
                "level": 0.95
            },
            "direction": determine_correlation_direction(float(r)) if not np.isnan(r) else "unknown",
            "magnitude": calculate_effect_size_magnitude(float(r)) if not np.isnan(r) else "unknown",
            "corrected_p_values": corrected_p_values.get("visual", {})
        }
        
        # Determine significance after correction (using Bonferroni by default)
        if "visual" in corrected_p_values:
            bonf_p = corrected_p_values["visual"].get("bonferroni", 1.0)
            report["results"]["visual"]["significant_after_bonferroni"] = bonf_p < 0.05
            report["results"]["visual"]["significant_after_bh"] = corrected_p_values["visual"].get("bh_fdr", 1.0) < 0.05
        else:
            report["results"]["visual"]["significant_after_bonferroni"] = False
            report["results"]["visual"]["significant_after_bh"] = False

    if auditory_results:
        r = auditory_results.get("r", np.nan)
        p = auditory_results.get("p", np.nan)
        ci_lower = auditory_results.get("ci_lower", np.nan)
        ci_upper = auditory_results.get("ci_upper", np.nan)
        
        report["results"]["auditory"] = {
            "pearson_r": float(r) if not np.isnan(r) else None,
            "p_value": float(p) if not np.isnan(p) else None,
            "confidence_interval": {
                "lower": float(ci_lower) if not np.isnan(ci_lower) else None,
                "upper": float(ci_upper) if not np.isnan(ci_upper) else None,
                "level": 0.95
            },
            "direction": determine_correlation_direction(float(r)) if not np.isnan(r) else "unknown",
            "magnitude": calculate_effect_size_magnitude(float(r)) if not np.isnan(r) else "unknown",
            "corrected_p_values": corrected_p_values.get("auditory", {})
        }
        
        # Determine significance after correction
        if "auditory" in corrected_p_values:
            bonf_p = corrected_p_values["auditory"].get("bonferroni", 1.0)
            report["results"]["auditory"]["significant_after_bonferroni"] = bonf_p < 0.05
            report["results"]["auditory"]["significant_after_bh"] = corrected_p_values["auditory"].get("bh_fdr", 1.0) < 0.05
        else:
            report["results"]["auditory"]["significant_after_bonferroni"] = False
            report["results"]["auditory"]["significant_after_bh"] = False
    
    # Summary of corrections
    report["multiple_comparison_correction"] = {
        "method": "Bonferroni and Benjamini-Hochberg (FDR)",
        "alpha": 0.05,
        "num_comparisons": len(raw_p_values),
        "details": corrected_p_values
    }
    
    success = write_json_file(str(output_path), report)
    if success:
        logger.info(f"Robustness analysis report written to {output_path}")
    return report

def write_report(report: Dict[str, Any], output_path: str) -> bool:
    """Generic function to write a report dictionary to a JSON file."""
    return write_json_file(output_path, report)

def main():
    """Main entry point for report generation."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting report generation (T028)...")
    
    # Load existing results from previous steps
    base_dir = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
    
    # Load robustness results (from T027)
    visual_path = base_dir / "data/results/visual_correlation.json"
    auditory_path = base_dir / "data/results/auditory_correlation.json"
    
    visual_results = load_json_file(str(visual_path))
    auditory_results = load_json_file(str(auditory_path))
    
    if not visual_results and not auditory_results:
        logger.error("No robustness results found. Cannot generate report.")
        sys.exit(1)
    
    # Generate the robustness analysis report with corrections
    report = generate_robustness_analysis_report(visual_results, auditory_results)
    
    logger.info("Robustness analysis report generation completed.")
    return report

if __name__ == "__main__":
    main()