import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure parent directory is in path for imports if running as script
_parent_dir = Path(__file__).resolve().parent.parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from config.env_config import load_config, setup_logging

logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def write_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Write a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_bootstrap_results(results_path: Path) -> Optional[Dict[str, Any]]:
    """Load bootstrap results from a JSON file."""
    if not results_path.exists():
        logger.warning(f"Bootstrap results file not found: {results_path}")
        return None
    return load_json_file(results_path)

def load_diagnostics_results(results_path: Path) -> Optional[Dict[str, Any]]:
    """Load diagnostic results from a JSON file."""
    if not results_path.exists():
        logger.warning(f"Diagnostics results file not found: {results_path}")
        return None
    return load_json_file(results_path)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected

def apply_bh_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    ranks = np.arange(1, n + 1)
    corrected = np.minimum(1, (n / ranks) * sorted_p)
    # Ensure monotonicity (cumulative min from end)
    for i in range(n - 2, -1, -1):
        corrected[i] = min(corrected[i], corrected[i+1])
    # Reorder to original
    result = np.zeros(n)
    result[sorted_indices] = corrected
    return result.tolist()

def determine_correlation_direction(r: float) -> str:
    """Determine the direction of correlation."""
    if r > 0.1:
        return "positive"
    elif r < -0.1:
        return "negative"
    return "negligible"

def calculate_effect_size_magnitude(r: float) -> str:
    """Calculate the magnitude of the effect size based on Cohen's guidelines."""
    abs_r = abs(r)
    if abs_r >= 0.5:
        return "large"
    elif abs_r >= 0.3:
        return "medium"
    elif abs_r >= 0.1:
        return "small"
    return "negligible"

def generate_regression_analysis_report(
    regression_results: Dict[str, Any],
    diagnostics_results: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the regression analysis report including coefficients, SE, t-stat, p-value,
    and diagnostic flags.
    """
    report = {
        "model_1": regression_results.get("model_1", {}),
        "model_2": regression_results.get("model_2", {}),
        "delta_r_squared": regression_results.get("delta_r_squared", np.nan),
        "f_change": regression_results.get("f_change", np.nan),
        "normality_passed": diagnostics_results.get("normality_passed", False),
        "homoscedasticity_passed": diagnostics_results.get("homoscedasticity_passed", False),
        "collinearity_flagged": diagnostics_results.get("collinearity_flagged", False)
    }

    # Extract specific coefficients from model_2 if available
    if "model_2" in regression_results and regression_results["model_2"]:
        model_2_summary = regression_results["model_2"].get("summary", {})
        if isinstance(model_2_summary, dict) and "params" in model_2_summary:
            params = model_2_summary["params"]
            bse = model_2_summary.get("bse", {})
            tvalues = model_2_summary.get("tvalues", {})
            pvalues = model_2_summary.get("pvalues", {})

            coefficients = []
            for var_name, coef in params.items():
                entry = {
                    "variable": var_name,
                    "coefficient": float(coef) if not np.isnan(coef) else None,
                    "se": float(bse.get(var_name, np.nan)) if var_name in bse else None,
                    "t_stat": float(tvalues.get(var_name, np.nan)) if var_name in tvalues else None,
                    "p_value": float(pvalues.get(var_name, np.nan)) if var_name in pvalues else None
                }
                coefficients.append(entry)
            report["coefficients"] = coefficients

    # Check overall model fit status
    all_diagnostics_passed = (
        diagnostics_results.get("normality_passed", False) and
        diagnostics_results.get("homoscedasticity_passed", False) and
        not diagnostics_results.get("collinearity_flagged", False)
    )
    report["model_validity"] = "valid" if all_diagnostics_passed else "invalid"

    return report

def generate_robustness_analysis_report(
    visual_results: Optional[Dict[str, Any]],
    auditory_results: Optional[Dict[str, Any]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Generate the robustness analysis report with multiple comparison corrections."""
    report = {
        "visual": visual_results if visual_results else {},
        "auditory": auditory_results if auditory_results else {},
        "correction_method": "bonferroni"
    }

    # Collect p-values for correction if available
    p_values = []
    if visual_results and "p_value" in visual_results:
        p_values.append(visual_results["p_value"])
    if auditory_results and "p_value" in auditory_results:
        p_values.append(auditory_results["p_value"])

    if len(p_values) > 1:
        corrected_p = apply_bonferroni_correction(p_values, alpha)
        if visual_results and "p_value" in visual_results:
            visual_results["p_value_corrected"] = corrected_p[0]
        if auditory_results and "p_value" in auditory_results:
            auditory_results["p_value_corrected"] = corrected_p[1]

    return report

def write_report(file_path: Path, report_data: Dict[str, Any]) -> None:
    """Write the report to a JSON file."""
    write_json_file(file_path, report_data)
    logger.info(f"Report written to {file_path}")

def main():
    """Main entry point for generating the regression analysis report."""
    config = load_config()
    logger = setup_logging(config.get("logging", {}).get("level", "INFO"))

    base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
    results_dir = base_dir / config.get("paths", {}).get("results", "data/results")
    derived_dir = base_dir / config.get("paths", {}).get("derived_data", "data/derived")

    results_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)

    # Load regression results
    regression_results_path = base_dir / "data" / "results" / "regression_raw.json"
    if not regression_results_path.exists():
        # Fallback: try to load from src/analysis output if raw file not found
        regression_results_path = base_dir / "data" / "results" / "regression_analysis_raw.json"
    
    if not regression_results_path.exists():
        logger.error(f"Regression results file not found: {regression_results_path}")
        sys.exit(1)

    try:
        regression_results = load_json_file(regression_results_path)
    except Exception as e:
        logger.error(f"Failed to load regression results: {e}")
        sys.exit(1)

    # Load diagnostics results
    diagnostics_results_path = base_dir / "data" / "results" / "diagnostics.json"
    if not diagnostics_results_path.exists():
        logger.error(f"Diagnostics results file not found: {diagnostics_results_path}")
        sys.exit(1)

    try:
        diagnostics_results = load_json_file(diagnostics_results_path)
    except Exception as e:
        logger.error(f"Failed to load diagnostics results: {e}")
        sys.exit(1)

    # Generate the report
    report = generate_regression_analysis_report(regression_results, diagnostics_results, config)

    # Write the report
    output_path = results_dir / "regression_analysis.json"
    write_report(output_path, report)

    logger.info("Regression analysis report generated successfully.")

if __name__ == "__main__":
    main()