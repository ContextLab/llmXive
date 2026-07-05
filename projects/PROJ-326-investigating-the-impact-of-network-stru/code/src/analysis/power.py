"""
Statistical Power Analysis Module for Network Topology Energy Transfer Study.

This module consumes output from regression (T033) and ANOVA (T034) analyses to
calculate the actual achieved statistical power of the study. It validates the
experimental design against the target correlation coefficient (r >= 0.3) and
sample size (n >= 100) requirements defined in SC-003.

Outputs:
    data/analysis/power_analysis_report.json: A JSON file containing the power
    analysis results, including achieved power, effect sizes, and a pass/fail
    status for the design validation.
"""

import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.utils.reproducibility import ensure_data_directory

# Constants for the study design requirements (SC-003)
TARGET_CORRELATION_R = 0.3
MIN_SAMPLE_SIZE = 100
SIGNIFICANCE_LEVEL = 0.05
TARGET_POWER = 0.80

logger = logging.getLogger(__name__)


def calculate_effect_size_r_to_cohen_d(r: float) -> float:
    """
    Convert Pearson's r correlation coefficient to Cohen's d.
    Formula: d = 2r / sqrt(1 - r^2)
    """
    if abs(r) >= 1.0:
        raise ValueError("Correlation coefficient r must be strictly between -1 and 1.")
    return (2 * r) / math.sqrt(1 - r**2)


def calculate_power_t_test_two_tailed(
    effect_size: float,
    sample_size: int,
    alpha: float = SIGNIFICANCE_LEVEL
) -> float:
    """
    Calculate the statistical power for a two-tailed t-test given effect size and sample size.
    Uses the non-central t-distribution approximation.

    Args:
        effect_size: Cohen's d.
        sample_size: Total number of observations (n).
        alpha: Significance level.

    Returns:
        Power (probability of rejecting null hypothesis when alternative is true).
    """
    if sample_size < 2:
        return 0.0

    df = sample_size - 2
    # Non-centrality parameter (nCP)
    ncp = effect_size * math.sqrt(sample_size / 2)

    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)

    # Power is the probability that the t-statistic exceeds the critical value
    # under the non-central t-distribution with the calculated ncp.
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)

    return float(power)


def load_regression_results(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load regression results from the analysis output file.
    Expects a JSON structure compatible with the output of T033 (run_analysis).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Regression results file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # The structure might be nested depending on how run_analysis aggregates.
    # We look for a key containing regression results.
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'regression_results' in data:
            return data['regression_results']
        if 'results' in data and isinstance(data['results'], list):
            return data['results']
        # If it's a single result object, wrap it
        return [data]
    else:
        return []


def load_anova_results(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load ANOVA results from the analysis output file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"ANOVA results file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'anova_results' in data:
            return data['anova_results']
        if 'results' in data and isinstance(data['results'], list):
            return data['results']
        return [data]
    else:
        return []


def compute_power_analysis(
    regression_results: List[Dict[str, Any]],
    anova_results: List[Dict[str, Any]],
    sample_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute statistical power based on observed effect sizes from regression and ANOVA.

    Args:
        regression_results: List of regression result dictionaries (must contain 'r' or 'effect_size').
        anova_results: List of ANOVA result dictionaries (must contain 'f_statistic' or 'effect_size').
        sample_size: The actual sample size used. If None, it will be inferred from results or defaults to MIN_SAMPLE_SIZE.

    Returns:
        Dictionary containing power analysis metrics.
    """
    if sample_size is None:
        # Infer from regression results if possible
        if regression_results and 'n' in regression_results[0]:
            sample_size = regression_results[0]['n']
        else:
            sample_size = MIN_SAMPLE_SIZE

    logger.info(f"Computing power analysis for sample size: {sample_size}")

    power_metrics = {
        "sample_size": sample_size,
        "target_correlation_r": TARGET_CORRELATION_R,
        "significance_level": SIGNIFICANCE_LEVEL,
        "target_power": TARGET_POWER,
        "regression_power_analysis": [],
        "anova_power_analysis": [],
        "overall_achieved_power": 0.0,
        "design_validation": {
            "passed": False,
            "reasons": []
        }
    }

    # Analyze Regression Results
    if regression_results:
        for idx, res in enumerate(regression_results):
            r_val = res.get('r', res.get('correlation_coefficient', 0.0))
            if not isinstance(r_val, (int, float)):
                r_val = 0.0

            # Convert r to Cohen's d for power calculation
            try:
                d_val = calculate_effect_size_r_to_cohen_d(abs(r_val))
            except ValueError:
                d_val = 0.0
                logger.warning(f"Invalid correlation value {r_val} in regression result {idx}, skipping power calc.")

            power = calculate_power_t_test_two_tailed(d_val, sample_size)
            
            power_metrics["regression_power_analysis"].append({
                "index": idx,
                "observed_r": r_val,
                "converted_cohen_d": d_val,
                "achieved_power": power,
                "meets_target": power >= TARGET_POWER
            })

    # Analyze ANOVA Results (Simplified: treating F-test power similarly via effect size eta-squared)
    # If eta-squared is not present, we estimate from F and df if available, otherwise skip or assume 0.
    if anova_results:
        for idx, res in enumerate(anova_results):
            f_stat = res.get('f_statistic', res.get('F', 0.0))
            df_between = res.get('df_between', res.get('df1', 0))
            df_within = res.get('df_within', res.get('df2', sample_size - 1))
            
            # Estimate eta-squared (effect size for ANOVA) if not provided
            # eta_sq = SS_between / SS_total. Approx: F * df1 / (F * df1 + df2)
            eta_sq = 0.0
            if f_stat > 0 and df_between > 0 and df_within > 0:
                eta_sq = (f_stat * df_between) / (f_stat * df_between + df_within)
            
            # Convert eta-squared to Cohen's f
            # f = sqrt(eta_sq / (1 - eta_sq))
            f_val = 0.0
            if eta_sq < 1.0:
                f_val = math.sqrt(eta_sq / (1 - eta_sq))
            
            # Power for ANOVA (approximation using non-central F)
            # ncp = f^2 * N
            ncp = (f_val ** 2) * sample_size
            f_crit = stats.f.ppf(1 - SIGNIFICANCE_LEVEL, df_between, df_within)
            power = 1 - stats.ncf.cdf(f_crit, df_between, df_within, ncp)

            power_metrics["anova_power_analysis"].append({
                "index": idx,
                "f_statistic": f_stat,
                "estimated_eta_squared": eta_sq,
                "estimated_cohen_f": f_val,
                "achieved_power": float(power),
                "meets_target": power >= TARGET_POWER
            })

    # Calculate Overall Achieved Power (Minimum of all calculated powers, or 0 if none)
    all_powers = [p["achieved_power"] for p in power_metrics["regression_power_analysis"]] + \
                 [p["achieved_power"] for p in power_metrics["anova_power_analysis"]]
    
    if all_powers:
        power_metrics["overall_achieved_power"] = min(all_powers)
    else:
        power_metrics["overall_achieved_power"] = 0.0
        power_metrics["design_validation"]["reasons"].append("No valid effect sizes found in results.")

    # Design Validation Logic (SC-003)
    # 1. Sample size >= 100
    # 2. Achieved power >= 0.80 (or at least meets the target r >= 0.3 implication)
    # 3. Observed effect size supports the hypothesis (r >= 0.3)
    
    validation = power_metrics["design_validation"]
    
    if sample_size < MIN_SAMPLE_SIZE:
        validation["reasons"].append(f"Sample size ({sample_size}) is below minimum threshold ({MIN_SAMPLE_SIZE}).")
    
    if power_metrics["overall_achieved_power"] < TARGET_POWER:
        validation["reasons"].append(f"Achieved power ({power_metrics['overall_achieved_power']:.4f}) is below target ({TARGET_POWER}).")
    
    # Check if the observed correlation (from regression) supports the target r >= 0.3
    # We look at the average or max observed r from regression results
    observed_rs = [p["observed_r"] for p in power_metrics["regression_power_analysis"]]
    if observed_rs:
        max_observed_r = max(observed_rs)
        if max_observed_r < TARGET_CORRELATION_R:
            validation["reasons"].append(f"Maximum observed correlation ({max_observed_r:.4f}) is below target ({TARGET_CORRELATION_R}).")
    else:
        validation["reasons"].append("No regression results found to validate target correlation.")

    validation["passed"] = len(validation["reasons"]) == 0

    return power_metrics


def generate_power_report(
    output_path: Path,
    power_metrics: Dict[str, Any]
) -> None:
    """
    Generate the final JSON report file.
    """
    ensure_data_directory(output_path.parent)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "analysis_type": "Statistical Power Analysis",
        "design_requirements": {
            "min_sample_size": MIN_SAMPLE_SIZE,
            "target_correlation_r": TARGET_CORRELATION_R,
            "target_power": TARGET_POWER,
            "significance_level": SIGNIFICANCE_LEVEL
        },
        "results": power_metrics,
        "validation_summary": {
            "passed": power_metrics["design_validation"]["passed"],
            "message": "Design validation PASSED" if power_metrics["design_validation"]["passed"] else "Design validation FAILED",
            "details": power_metrics["design_validation"]["reasons"]
        }
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Power analysis report saved to {output_path}")


def main():
    """
    Main entry point for the power analysis script.
    Loads results from T033/T034, computes power, and saves the report.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "data" / "analysis"
    
    # Define input paths (matching output paths from T033/T034)
    # Assuming run_analysis aggregates results into final_results.json or similar
    # We try to load from the standard output location defined in T037
    regression_path = data_dir / "final_results.json"
    anova_path = data_dir / "final_results.json" # Often same file, or separate if split
    
    # Fallback: try specific files if final_results.json is not the single source
    if not regression_path.exists():
        regression_path = data_dir / "regression_results.json"
    if not anova_path.exists():
        anova_path = data_dir / "anova_results.json"

    # If still not found, try to load from the manifest or a generic analysis output
    # For robustness, we assume the main analysis script (T037) might have saved to a specific key
    # If the file is the same, we load it once and parse keys.
    
    reg_data = []
    anova_data = []

    # Attempt to load regression data
    if regression_path.exists():
        try:
            reg_data = load_regression_results(regression_path)
            logger.info(f"Loaded {len(reg_data)} regression results from {regression_path}")
        except Exception as e:
            logger.error(f"Failed to load regression results: {e}")
    else:
        logger.warning(f"Regression results file not found at {regression_path}")

    # Attempt to load ANOVA data
    if anova_path.exists() and regression_path != anova_path:
        try:
            anova_data = load_anova_results(anova_path)
            logger.info(f"Loaded {len(anova_data)} ANOVA results from {anova_path}")
        except Exception as e:
            logger.error(f"Failed to load ANOVA results: {e}")
    elif regression_path.exists() and regression_path == anova_path:
        # Same file, try to extract ANOVA if it exists in the same JSON
        try:
            with open(regression_path, 'r') as f:
                data = json.load(f)
            if 'anova_results' in data:
                anova_data = data['anova_results']
            elif 'results' in data and isinstance(data['results'], list):
                # Heuristic: if it's a list, assume mixed or just use for regression
                pass
        except Exception as e:
            logger.error(f"Failed to extract ANOVA data: {e}")

    # Determine sample size
    # We need the actual N used. If not in results, we default to the manifest count or 100.
    # Let's assume the first regression result has 'n' or we check the global config.
    sample_size = MIN_SAMPLE_SIZE
    if reg_data and 'n' in reg_data[0]:
        sample_size = reg_data[0]['n']
    elif anova_data and 'n' in anova_data[0]:
        sample_size = anova_data[0]['n']
    
    # Compute Power
    power_metrics = compute_power_analysis(reg_data, anova_data, sample_size)

    # Generate Report
    output_file = data_dir / "power_analysis_report.json"
    generate_power_report(output_file, power_metrics)

    # Print summary
    print(f"\nPower Analysis Complete.")
    print(f"Sample Size: {sample_size}")
    print(f"Overall Achieved Power: {power_metrics['overall_achieved_power']:.4f}")
    print(f"Design Validation: {'PASSED' if power_metrics['design_validation']['passed'] else 'FAILED'}")
    if not power_metrics['design_validation']['passed']:
        for reason in power_metrics['design_validation']['reasons']:
            print(f"  - {reason}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
