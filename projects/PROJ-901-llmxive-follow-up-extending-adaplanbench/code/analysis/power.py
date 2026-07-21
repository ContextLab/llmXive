import os
import json
import math
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.power import GofChisquarePower

# Import from sibling modules if needed, but mostly standard/statsmodels
# from config import Paths, AnalysisConfig # Not strictly needed if we hardcode or pass args, but good for consistency

def calculate_effect_size_for_logistic(
    group1_prop: float, group2_prop: float, p_pool: Optional[float] = None
) -> float:
    """
    Calculate Cohen's h (effect size for proportions) or similar metric.
    For power analysis in logistic regression context, we often use the
    proportion difference or odds ratio derived effect size.
    Here we use Cohen's h for two proportions as a proxy for the effect size
    in a chi-square test of independence (which underlies the GLMM binomial test).

    Cohen's h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
    """
    if p_pool is None:
        # Simple difference approach or standard Cohen's h
        # For power analysis of a chi-square test (2x2), we can use the effect size w.
        # w = sqrt( sum((p_obs - p_exp)^2 / p_exp) )
        # However, statsmodels GofChisquarePower expects 'effect_size' (w) or we can compute it.
        # Let's compute Cohen's h which is standard for proportions.
        if not (0 < group1_prop < 1 and 0 < group2_prop < 1):
            return 0.0
        h = 2 * (math.asin(math.sqrt(group1_prop)) - math.asin(math.sqrt(group2_prop)))
        return abs(h)
    return 0.0

def estimate_required_sample_size(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    df: int = 1
) -> int:
    """
    Estimate the required total sample size for a chi-square test given an effect size.
    Uses statsmodels GofChisquarePower.
    """
    if effect_size <= 0:
        return -1 # Cannot calculate
    solver = GofChisquarePower()
    try:
        # nobs is total sample size
        n = solver.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            n_groups=2, # 2x2 table
            df_divisor=df # df for the test
        )
        return int(math.ceil(n))
    except Exception:
        return -1

def perform_power_analysis(
    monolithic_logs: list,
    dual_track_logs: list,
    target_effect_size: float = 0.15,
    alpha: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Perform power analysis based on observed violation rates.
    Returns a report with calculated power, effect size, and pass/fail.
    """
    if not monolithic_logs or not dual_track_logs:
        return {
            "calculated_power": 0.0,
            "effect_size": 0.0,
            "target_power": target_power,
            "pass": False,
            "error": "Insufficient data in logs"
        }

    # Extract violation rates
    n_mono = len(monolithic_logs)
    violations_mono = sum(1 for log in monolithic_logs if log.get("violated", False))
    prop_mono = violations_mono / n_mono if n_mono > 0 else 0.0

    n_dual = len(dual_track_logs)
    violations_dual = sum(1 for log in dual_track_logs if log.get("violated", False))
    prop_dual = violations_dual / n_dual if n_dual > 0 else 0.0

    # Calculate effect size (Cohen's h)
    effect_size = calculate_effect_size_for_logistic(prop_mono, prop_dual)

    # Calculate achieved power given the observed effect size and sample sizes
    # We treat this as a test of two proportions (chi-square equivalent)
    # statsmodels GofChisquarePower can compute power if we provide nobs
    # But GofChisquarePower is for goodness of fit. For two proportions, we use TTestIndPower or similar?
    # Actually, for a 2x2 contingency table, the test is a Chi-Square test of independence.
    # We can use the GofChisquarePower but we need to construct the expected proportions.
    # Alternatively, use TTestIndPower for proportions (approximation) or use the effect size w.
    # Let's use the effect size w (Cohen's w) which is equivalent to sqrt(chi2/N).
    # For 2x2, w = h / 2? No, h is for proportions.
    # Let's stick to the statsmodels TTestIndPower for difference in means (proportions are means of 0/1).
    from statsmodels.stats.power import TTestIndPower

    # Effect size for T-test (Cohen's d) for proportions:
    # d = (p1 - p2) / sqrt(p(1-p)) where p is pooled proportion
    if n_mono + n_dual > 0:
        p_pool = (violations_mono + violations_dual) / (n_mono + n_dual)
        if 0 < p_pool < 1:
            pooled_std = math.sqrt(p_pool * (1 - p_pool))
            cohens_d = abs(prop_mono - prop_dual) / pooled_std
        else:
            cohens_d = 0.0
    else:
        cohens_d = 0.0

    solver = TTestIndPower()
    try:
        # Power calculation for two independent samples
        # nobs1, nobs2
        calculated_power = solver.power(
            effect_size=cohens_d,
            nobs1=n_mono,
            ratio=n_dual/n_mono if n_mono > 0 else 1.0,
            alpha=alpha,
            alternative='two-sided'
        )
    except Exception:
        calculated_power = 0.0

    pass_flag = calculated_power >= target_power

    return {
        "calculated_power": float(calculated_power),
        "effect_size": float(cohens_d), # Using Cohen's d for interpretability
        "prop_monolithic": float(prop_mono),
        "prop_dual_track": float(prop_dual),
        "sample_size_monolithic": n_mono,
        "sample_size_dual_track": n_dual,
        "target_power": target_power,
        "target_effect_size": target_effect_size,
        "pass": pass_flag
    }

def run_power_analysis(
    monolithic_logs_path: Path,
    dual_track_logs_path: Path,
    output_path: Path,
    target_effect_size: float = 0.15,
    target_power: float = 0.80
) -> None:
    """
    Main entry point to run power analysis and write report.
    """
    # Load logs
    with open(monolithic_logs_path, 'r') as f:
        monolithic_logs = json.load(f)
    with open(dual_track_logs_path, 'r') as f:
        dual_track_logs = json.load(f)

    report = perform_power_analysis(
        monolithic_logs,
        dual_track_logs,
        target_effect_size=target_effect_size,
        target_power=target_power
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Power analysis report written to {output_path}")
    print(f"Calculated Power: {report['calculated_power']:.4f}")
    print(f"Effect Size (Cohen's d): {report['effect_size']:.4f}")
    print(f"Target Power: {target_power}")
    print(f"Pass: {report['pass']}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Power Analysis")
    parser.add_argument("--monolithic-logs", type=str, required=True, help="Path to monolithic logs JSON")
    parser.add_argument("--dual-track-logs", type=str, required=True, help="Path to dual track logs JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON report")
    parser.add_argument("--target-power", type=float, default=0.80, help="Target power")
    parser.add_argument("--target-effect-size", type=float, default=0.15, help="Target effect size (f2)")

    args = parser.parse_args()

    run_power_analysis(
        Path(args.monolithic_logs),
        Path(args.dual_track_logs),
        Path(args.output),
        target_power=args.target_power,
        target_effect_size=args.target_effect_size
    )

if __name__ == "__main__":
    main()