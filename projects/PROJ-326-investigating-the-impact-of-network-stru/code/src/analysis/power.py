"""
Statistical Power Analysis Module for Network Topology Energy Transfer Study.

This module consumes output from regression (T033) and ANOVA (T034) analyses
to calculate the actual achieved statistical power based on the generated
sample size (>=100) and observed variance. It validates the design against
the target correlation coefficient (r >= 0.3) and generates a design
validation report (SC-003).

Outputs:
    data/analysis/power_analysis_report.json: Design validation report.
"""

import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import nct

from code.src.utils.reproducibility import ensure_data_directory

# Configure logging
logger = logging.getLogger(__name__)

# Constants
TARGET_CORRELATION = 0.3
TARGET_POWER = 0.80
ALPHA = 0.05
SAMPLE_SIZE_THRESHOLD = 100

class PowerAnalysisError(Exception):
    """Custom exception for power analysis errors."""
    pass


def calculate_effect_size_r_to_cohen_d(r: float) -> float:
    """
    Convert Pearson correlation coefficient (r) to Cohen's d.
    Formula: d = 2r / sqrt(1 - r^2)

    Args:
        r: Pearson correlation coefficient (-1 to 1).

    Returns:
        Cohen's d effect size.
    """
    if abs(r) >= 1.0:
        raise ValueError("Correlation coefficient must be strictly between -1 and 1.")
    return (2 * r) / math.sqrt(1 - r**2)


def calculate_power_t_test_two_tailed(n: int, d: float, alpha: float = ALPHA) -> float:
    """
    Calculate statistical power for a two-tailed t-test given sample size and effect size.
    Uses the non-central t-distribution.

    Args:
        n: Total sample size (N = n1 + n2, assuming equal groups n/2).
        d: Cohen's d effect size.
        alpha: Significance level.

    Returns:
        Statistical power (probability of rejecting null hypothesis).
    """
    if n <= 2:
        return 0.0

    # Degrees of freedom for two independent samples (equal size)
    df = n - 2
    
    # Non-centrality parameter
    # For two-sample t-test: ncp = d * sqrt(n / 2)
    ncp = d * math.sqrt(n / 2)

    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)

    # Power is the probability that the t-statistic exceeds the critical value
    # under the alternative hypothesis (non-central t-distribution)
    # P(T > t_crit) + P(T < -t_crit)
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return float(power)


def load_regression_results(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load regression results from the analysis output file.
    Expects a JSON file containing a list of regression results.

    Args:
        filepath: Path to the regression results JSON file. Defaults to 
                  data/analysis/regression_results.json.

    Returns:
        List of regression result dictionaries.

    Raises:
        PowerAnalysisError: If file not found or invalid format.
    """
    if filepath is None:
        project_root = Path(__file__).resolve().parents[3]
        filepath = project_root / "data" / "analysis" / "regression_results.json"

    if not filepath.exists():
        raise PowerAnalysisError(f"Regression results file not found: {filepath}")

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise PowerAnalysisError("Regression results must be a list of dictionaries.")
        
        return data
    except json.JSONDecodeError as e:
        raise PowerAnalysisError(f"Invalid JSON in regression results: {e}")


def load_anova_results(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load ANOVA results from the analysis output file.
    Expects a JSON file containing ANOVA summary statistics.

    Args:
        filepath: Path to the ANOVA results JSON file. Defaults to
                  data/analysis/anova_results.json.

    Returns:
        Dictionary of ANOVA results.

    Raises:
        PowerAnalysisError: If file not found or invalid format.
    """
    if filepath is None:
        project_root = Path(__file__).resolve().parents[3]
        filepath = project_root / "data" / "analysis" / "anova_results.json"

    if not filepath.exists():
        raise PowerAnalysisError(f"ANOVA results file not found: {filepath}")

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise PowerAnalysisError("ANOVA results must be a dictionary.")
        
        return data
    except json.JSONDecodeError as e:
        raise PowerAnalysisError(f"Invalid JSON in ANOVA results: {e}")


def compute_power_analysis(
    regression_results: List[Dict[str, Any]],
    anova_results: Dict[str, Any],
    target_r: float = TARGET_CORRELATION,
    target_power: float = TARGET_POWER
) -> Dict[str, Any]:
    """
    Compute comprehensive power analysis based on regression and ANOVA results.

    Args:
        regression_results: List of regression result dictionaries containing 
                            correlation coefficients, p-values, and sample sizes.
        anova_results: Dictionary containing ANOVA F-statistics, p-values, 
                       and group information.
        target_r: Target correlation coefficient for design validation.
        target_power: Target statistical power.

    Returns:
        Dictionary containing detailed power analysis results.
    """
    logger.info("Computing power analysis...")
    
    analysis_results = {
        "timestamp": datetime.now().isoformat(),
        "target_correlation": target_r,
        "target_power": target_power,
        "regression_power_analysis": [],
        "anova_power_analysis": {},
        "design_validation": {
            "sample_size_sufficient": False,
            "power_achieved": False,
            "effect_size_achieved": False,
            "overall_validation": False,
            "notes": []
        }
    }

    # Analyze Regression Results
    total_samples = 0
    max_power = 0.0
    observed_effect_sizes = []

    for reg in regression_results:
        r_value = reg.get("correlation", 0.0)
        n = reg.get("sample_size", 0)
        total_samples = max(total_samples, n)
        
        # Convert r to Cohen's d
        try:
            d = calculate_effect_size_r_to_cohen_d(r_value)
            observed_effect_sizes.append(d)
        except ValueError as e:
            logger.warning(f"Invalid correlation in regression result: {e}")
            continue

        # Calculate power for this effect size
        power = calculate_power_t_test_two_tailed(n, d)
        max_power = max(max_power, power)

        analysis_results["regression_power_analysis"].append({
            "correlation": r_value,
            "effect_size_d": d,
            "sample_size": n,
            "achieved_power": power,
            "meets_target": power >= target_power
        })

    # Analyze ANOVA Results (F-test power)
    # Simplified: Use F-statistic to estimate effect size (Eta-squared)
    # and calculate power for F-test
    if "f_statistic" in anova_results and "p_value" in anova_results:
        f_stat = anova_results["f_statistic"]
        p_val = anova_results["p_value"]
        n_groups = anova_results.get("groups", 3)
        n_total = anova_results.get("total_samples", total_samples)
        
        # Eta-squared (effect size for ANOVA)
        # Approximation: eta2 = F / (F + (df2/df1))
        # df1 = k - 1, df2 = N - k
        df1 = n_groups - 1
        df2 = n_total - n_groups
        
        if df1 > 0 and df2 > 0:
            eta_squared = f_stat / (f_stat + (df2 / df1))
            # Cohen's f = sqrt(eta2 / (1 - eta2))
            f_effect = math.sqrt(eta_squared / (1 - eta_squared)) if eta_squared < 1 else 2.0
            
            # Power for F-test (simplified approximation using non-central F)
            # ncp = f^2 * N
            ncp = (f_effect ** 2) * n_total
            
            # Critical F value
            f_crit = stats.f.ppf(1 - ALPHA, df1, df2)
            
            # Power calculation using non-central F distribution
            anova_power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
            
            analysis_results["anova_power_analysis"] = {
                "f_statistic": f_stat,
                "p_value": p_val,
                "effect_size_eta_squared": eta_squared,
                "effect_size_f": f_effect,
                "achieved_power": anova_power,
                "meets_target": anova_power >= target_power
            }

    # Design Validation Logic
    analysis_results["design_validation"]["sample_size_sufficient"] = total_samples >= SAMPLE_SIZE_THRESHOLD
    
    # Check if observed effect sizes meet target r
    # We check if the observed correlation is >= target_r OR if the power 
    # calculated based on observed r is sufficient to detect target_r
    observed_r_max = max([r.get("correlation", 0) for r in regression_results], default=0)
    analysis_results["design_validation"]["effect_size_achieved"] = abs(observed_r_max) >= target_r
    
    # Power is achieved if either regression or ANOVA power meets target
    regression_power_met = any(r["meets_target"] for r in analysis_results["regression_power_analysis"])
    anova_power_met = analysis_results["anova_power_analysis"].get("meets_target", False)
    
    analysis_results["design_validation"]["power_achieved"] = regression_power_met or anova_power_met
    
    # Overall validation
    validation = analysis_results["design_validation"]
    validation["overall_validation"] = (
        validation["sample_size_sufficient"] and 
        validation["power_achieved"]
    )

    # Generate notes
    if not validation["sample_size_sufficient"]:
        validation["notes"].append(f"Sample size ({total_samples}) is below threshold ({SAMPLE_SIZE_THRESHOLD}).")
    if not validation["effect_size_achieved"]:
        validation["notes"].append(f"Observed effect size (r={observed_r_max:.3f}) is below target (r={target_r}).")
    if not validation["power_achieved"]:
        validation["notes"].append("Statistical power did not meet target threshold.")
    if validation["overall_validation"]:
        validation["notes"].append("Design validation PASSED: Sample size and power requirements met.")

    logger.info(f"Power analysis complete. Overall validation: {validation['overall_validation']}")
    return analysis_results


def generate_power_report(
    analysis_results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate the design validation report and save to disk.

    Args:
        analysis_results: The computed power analysis results.
        output_path: Path to save the report. Defaults to 
                     data/analysis/power_analysis_report.json.

    Returns:
        Path to the saved report file.
    """
    if output_path is None:
        project_root = Path(__file__).resolve().parents[3]
        output_path = project_root / "data" / "analysis" / "power_analysis_report.json"

    # Ensure directory exists
    ensure_data_directory(output_path)

    # Add summary
    validation = analysis_results["design_validation"]
    analysis_results["summary"] = {
        "status": "PASS" if validation["overall_validation"] else "FAIL",
        "message": "Design validation successful" if validation["overall_validation"] 
                   else "Design validation failed: requirements not met"
    }

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)

    logger.info(f"Power analysis report saved to: {output_path}")
    return output_path


def main() -> int:
    """
    Main entry point for power analysis task (T044).
    
    Loads regression and ANOVA results, computes power analysis,
    and generates the design validation report.

    Returns:
        0 on success, 1 on failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load dependencies
        logger.info("Loading regression results...")
        regression_data = load_regression_results()
        
        logger.info("Loading ANOVA results...")
        anova_data = load_anova_results()
        
        # Compute analysis
        logger.info("Computing power analysis...")
        results = compute_power_analysis(regression_data, anova_data)
        
        # Generate report
        logger.info("Generating power analysis report...")
        report_path = generate_power_report(results)
        
        # Verify output exists
        if not report_path.exists():
            raise PowerAnalysisError(f"Failed to create report file: {report_path}")
        
        print(f"Power analysis complete. Report saved to: {report_path}")
        return 0
        
    except PowerAnalysisError as e:
        logger.error(f"Power analysis failed: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during power analysis: {e}")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())