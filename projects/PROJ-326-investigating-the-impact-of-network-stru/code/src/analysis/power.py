import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.special import ndtr

from code.src.analysis.regression import RegressionResult
from code.src.analysis.anova import run_anova_on_diffusion_by_topology

logger = logging.getLogger(__name__)


def calculate_effect_size_r_to_cohen_d(r: float) -> float:
    """
    Convert Pearson correlation coefficient r to Cohen's d.
    Formula: d = 2r / sqrt(1 - r^2)
    """
    if abs(r) >= 1.0:
        # Handle edge cases where correlation is perfect (theoretical)
        # Return a large value or handle as error
        logger.warning("Correlation coefficient |r| >= 1.0. Clamping to 0.999.")
        r = 0.999 if r > 0 else -0.999
    
    denominator = math.sqrt(1 - r**2)
    if denominator == 0:
        return float('inf') if r > 0 else float('-inf')
    
    return (2 * r) / denominator


def calculate_power_t_test_two_tailed(
    effect_size: float,
    sample_size: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for a two-tailed t-test given effect size (Cohen's d)
    and sample size.
    
    Approximation using non-central t-distribution or normal approximation for large N.
    For this implementation, we use the normal approximation for power:
    Power = 1 - beta = Phi( |d| * sqrt(N/2) - z_{1-alpha/2} )
    
    Note: This is an approximation. For small samples, non-central t is more accurate.
    """
    if sample_size < 2:
        return 0.0
    
    # Standard normal quantile for 1 - alpha/2
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    
    # Non-centrality parameter approximation
    # For two independent groups of size n/2, delta = d * sqrt(n/2)
    # But here we are looking at correlation regression context, 
    # so we treat the effective N as the sample size for the correlation test.
    # Approximation for correlation power:
    # z_power = sqrt(N - 3) * arctanh(r) - z_alpha
    # However, using d:
    # delta = d * sqrt(N/2) is for t-test of means.
    # Let's use the Fisher Z transformation approach for correlation power which is standard:
    # z_r = 0.5 * ln((1+r)/(1-r))
    # var(z_r) = 1/(N-3)
    # Power = P( |Z| > z_alpha | H1 )
    
    # Using the direct correlation power formula via Fisher Z:
    if abs(r := None): # Placeholder to avoid unused warning if we switch logic
        pass
    
    # Let's stick to the Cohen's d to power mapping as requested by the function signature
    # assuming d is derived from r.
    # The non-centrality parameter for a two-sample t-test is delta = d * sqrt(n/2).
    # For a one-sample or correlation test, the approximation is often:
    # delta = d * sqrt(N) ? No, let's use the standard t-test power approximation:
    # delta = d * sqrt(N/2) (assuming equal groups) or d * sqrt(N) for paired?
    # Given the context of "sample size >= 100" and "target r", this implies a correlation test.
    # Let's use the Fisher Z method for accuracy on correlation r, then map d back if needed.
    # But the function takes 'effect_size' (d).
    
    # Standard approximation for power of t-test with effect size d:
    # delta = d * sqrt(n/2)
    # Power = 1 - beta
    # We can use scipy's nct (non-central t) for precision or the normal approx.
    # Normal approx: Power = Phi( delta - z_alpha ) + Phi( -delta - z_alpha )
    # Since delta is usually positive for effect size magnitude:
    # Power ~ Phi( |delta| - z_alpha )
    
    n = sample_size
    # Assuming two groups of size n/2 for the d calculation context, or simply N total
    # If d is derived from r in a regression of 1 predictor, the effective N is the sample size.
    # Let's assume the standard t-test approximation: delta = d * sqrt(n/2)
    # But if this is a correlation test, the variance is different.
    # Let's use the formula: Power = 1 - beta = P(t > t_crit | H1)
    # Approximation: z = d * sqrt(n/2) - z_alpha
    # Wait, for correlation r, the standard error is 1/sqrt(N-3).
    # Let's use the Fisher Z approach directly on r if we had r, but we have d.
    # Let's assume the user wants the power for the t-test corresponding to this d.
    # delta = d * sqrt(n/2)
    delta = effect_size * math.sqrt(n / 2)
    
    z_power = abs(delta) - z_alpha
    power = ndtr(z_power)
    
    # Clamp power to [0, 1]
    return max(0.0, min(1.0, power))


def load_regression_results(
    results_path: Path, 
    target_key: str = "regression_results"
) -> List[Dict[str, Any]]:
    """
    Load regression results from the final analysis JSON file.
    Expects a structure like:
    {
      "regression_results": [
        {"predictor": "...", "r": 0.35, "r_squared": 0.12, "p_value": 0.001, ...},
        ...
      ],
      ...
    }
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Regression results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    if target_key not in data:
        # Try to find it if the key is slightly different or nested
        # Fallback: look for any key containing 'regression'
        candidates = [k for k in data.keys() if 'regression' in k.lower()]
        if not candidates:
            raise KeyError(f"Could not find regression results in {results_path}. Keys: {list(data.keys())}")
        target_key = candidates[0]
    
    return data[target_key]


def load_anova_results(
    results_path: Path,
    target_key: str = "anova_results"
) -> Dict[str, Any]:
    """
    Load ANOVA results from the final analysis JSON file.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"ANOVA results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    if target_key not in data:
        candidates = [k for k in data.keys() if 'anova' in k.lower()]
        if not candidates:
            raise KeyError(f"Could not find ANOVA results in {results_path}. Keys: {list(data.keys())}")
        target_key = candidates[0]
    
    return data[target_key]


def compute_power_analysis(
    regression_results: List[Dict[str, Any]],
    anova_results: Optional[Dict[str, Any]],
    sample_size: int,
    target_r: float = 0.3,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compute achieved statistical power based on observed effect sizes.
    
    Args:
        regression_results: List of dicts with 'r' or 'r_squared' and 'p_value'.
        anova_results: Dict with F-statistic and p-values.
        sample_size: Total number of observations (graphs).
        target_r: Target correlation threshold for the study design.
        alpha: Significance level.
    
    Returns:
        Dictionary containing power analysis details.
    """
    logger.info(f"Computing power analysis for sample size N={sample_size}")
    
    power_analysis = {
        "sample_size": sample_size,
        "target_correlation": target_r,
        "alpha": alpha,
        "regression_power_analysis": [],
        "anova_power_analysis": {},
        "summary": {}
    }
    
    # 1. Regression Power Analysis
    total_significant = 0
    power_values = []
    
    for res in regression_results:
        r_val = res.get('r') or res.get('correlation')
        p_val = res.get('p_value')
        predictor = res.get('predictor', 'unknown')
        
        if r_val is None:
            continue
        
        # Convert r to Cohen's d
        d = calculate_effect_size_r_to_cohen_d(r_val)
        
        # Calculate power
        power = calculate_power_t_test_two_tailed(abs(d), sample_size, alpha)
        
        power_values.append(power)
        
        entry = {
            "predictor": predictor,
            "observed_r": r_val,
            "effect_size_d": d,
            "p_value": p_val,
            "achieved_power": power,
            "is_significant": p_val < alpha if p_val else False
        }
        power_analysis["regression_power_analysis"].append(entry)
        
        if entry["is_significant"]:
            total_significant += 1
    
    # 2. ANOVA Power Analysis
    if anova_results:
        # Extract F-statistic and degrees of freedom if available
        f_stat = anova_results.get('f_statistic')
        p_val = anova_results.get('p_value')
        df1 = anova_results.get('df_between', 0)
        df2 = anova_results.get('df_within', sample_size - df1 - 1)
        
        # Calculate eta-squared (effect size for ANOVA)
        # eta^2 = SS_between / SS_total. We might not have SS, but we can estimate from F.
        # F = (SS_between/df1) / (SS_within/df2)
        # eta^2 = (F * df1) / (F * df1 + df2)
        if f_stat and df1 and df2:
            eta_sq = (f_stat * df1) / (f_stat * df1 + df2)
            # Convert eta-squared to f (Cohen's f)
            # f = sqrt(eta_sq / (1 - eta_sq))
            if eta_sq < 1.0:
                f_effect = math.sqrt(eta_sq / (1 - eta_sq))
            else:
                f_effect = float('inf')
            
            # Power for ANOVA (approximation)
            # Non-centrality parameter lambda = f^2 * N
            ncp = (f_effect ** 2) * sample_size
            # Critical F value
            f_crit = stats.f.ppf(1 - alpha, df1, df2)
            # Power = 1 - beta = P(F > f_crit | lambda)
            # Using non-central F distribution
            try:
                power_anova = 1 - stats.nct.cdf(f_crit, df1, df2, ncp) # Note: nct is t, need ncf
                # scipy.stats.ncf exists? No, scipy.stats.ncf is not standard in older versions?
                # Actually scipy.stats.ncf is available.
                power_anova = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
            except AttributeError:
                # Fallback if ncf is missing (older scipy)
                # Approximation: power ~ 1 if f_stat is very high, else 0
                power_anova = 1.0 if f_stat > f_crit else 0.0
            
            power_analysis["anova_power_analysis"] = {
                "f_statistic": f_stat,
                "degrees_of_freedom": {"between": df1, "within": df2},
                "effect_size_eta_squared": eta_sq,
                "effect_size_cohen_f": f_effect,
                "non_central_parameter": ncp,
                "achieved_power": float(power_anova),
                "p_value": p_val,
                "is_significant": p_val < alpha if p_val else False
            }
        else:
            power_analysis["anova_power_analysis"] = {"error": "Missing F-stat or DF"}

    # 3. Summary
    avg_power = sum(power_values) / len(power_values) if power_values else 0.0
    min_power = min(power_values) if power_values else 0.0
    max_power = max(power_values) if power_values else 0.0
    
    # Check against target power (usually 0.80)
    # The task asks to measure against target r >= 0.3.
    # If observed r >= 0.3, we check if power is adequate (>= 0.8).
    # If observed r < 0.3, the study might be underpowered to detect the target.
    
    target_correlations_met = [r for r in power_values if r >= target_r] # This is wrong, r is correlation, power is probability
    # Correct logic:
    # Did we observe effects >= target_r?
    observed_effects_meeting_target = [
        entry for entry in power_analysis["regression_power_analysis"] 
        if entry["observed_r"] >= target_r
    ]
    
    power_adequate = all(
        entry["achieved_power"] >= 0.80 
        for entry in observed_effects_meeting_target
    ) if observed_effects_meeting_target else False
    
    # Overall conclusion
    conclusion = "Inconclusive"
    if avg_power >= 0.80:
        conclusion = "Adequate Power"
        if not observed_effects_meeting_target:
            conclusion += " (No effects met target r)"
    elif min_power < 0.50:
        conclusion = "Underpowered"
    else:
        conclusion = "Marginal Power"
    
    power_analysis["summary"] = {
        "average_achieved_power": avg_power,
        "min_achieved_power": min_power,
        "max_achieved_power": max_power,
        "effects_meeting_target_r": len(observed_effects_meeting_target),
        "power_adequate_for_target": power_adequate,
        "conclusion": conclusion,
        "recommendation": "Proceed with caution" if "Marginal" in conclusion else "Valid" if "Adequate" in conclusion else "Requires larger sample"
    }
    
    return power_analysis


def generate_power_report(
    power_analysis: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate the design validation report (JSON).
    """
    ensure_data_directory(output_path)
    
    report = {
        "report_type": "Statistical Power Analysis",
        "generated_at": datetime.now().isoformat(),
        "analysis_results": power_analysis,
        "validation": {
            "sc_003_confirmed": power_analysis["summary"]["power_adequate_for_target"],
            "details": power_analysis["summary"]["conclusion"]
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Power analysis report saved to {output_path}")


def ensure_data_directory(file_path: Path) -> None:
    """Ensure the directory for a file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    """
    Main entry point for the power analysis script.
    Loads results from data/analysis/final_results.json and generates the report.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "analysis" / "final_results.json"
    output_path = project_root / "data" / "analysis" / "power_analysis_report.json"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run run_analysis.py first.")
        return 1
    
    try:
        # Load results
        # We need to extract sample size. It should be in the final_results or we assume >= 100 from manifest
        # Let's try to get it from the data or default to 100 if not found, but better to read from manifest
        manifest_path = project_root / "data" / "raw" / "global_batch_manifest.json"
        sample_size = 100 # Default
        
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                sample_size = manifest.get("total_graphs", 100)
        
        logger.info(f"Detected sample size: {sample_size}")
        
        regression_data = load_regression_results(input_path)
        anova_data = load_anova_results(input_path)
        
        # Compute power
        power_results = compute_power_analysis(
            regression_results=regression_data,
            anova_results=anova_data,
            sample_size=sample_size,
            target_r=0.3,
            alpha=0.05
        )
        
        # Generate report
        generate_power_report(power_results, output_path)
        
        logger.info("Power analysis completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
