import os
import json
import math
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from statsmodels.stats.power import GofChisquarePower
from statsmodels.stats.power import tt_ind_solve_power
from statsmodels.stats.power import FTestAnovaPower

from config import Paths


def calculate_effect_size_for_logistic(
    prop_control: float,
    prop_treatment: float,
    base_rate: float = 0.5
) -> float:
    """
    Estimate Cohen's h for logistic comparison of proportions.
    Used as a proxy for effect size in binary violation outcomes.
    
    Args:
        prop_control: Proportion of violations in baseline (monolithic)
        prop_treatment: Proportion of violations in dual-track
        base_rate: Not used in simple h calculation, kept for signature compatibility
    
    Returns:
        Cohen's h effect size
    """
    # Fisher's z-transformation for proportions
    z1 = 2 * math.asin(math.sqrt(prop_control))
    z2 = 2 * math.asin(math.sqrt(prop_treatment))
    return abs(z2 - z1)


def estimate_required_sample_size(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    n_groups: int = 2
) -> int:
    """
    Estimate the total sample size required to detect a given effect size
    with specified power and alpha.
    
    Uses GofChisquarePower for proportion differences (binary outcomes).
    
    Args:
        effect_size: Cohen's h (or f for ANOVA)
        alpha: Significance level
        power: Target statistical power
        n_groups: Number of groups being compared (default 2)
    
    Returns:
        Estimated total sample size required
    """
    # For binary outcome (violation vs no violation), we use proportion test
    # GofChisquarePower is appropriate for goodness-of-fit or test of proportions
    solver = GofChisquarePower()
    
    # Solve for nobs1 (sample size per group)
    # effect_size here is Cohen's h
    n_per_group = solver.solve(effect_size=effect_size, 
                               power=power, 
                               alpha=alpha, 
                               n_groups=n_groups)
    
    return int(math.ceil(n_per_group * n_groups))


def perform_power_analysis(
    execution_traces_path: Path,
    target_effect_size: float = 0.15,
    target_power: float = 0.80,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform power analysis on the filtered subset of execution traces.
    
    Calculates the achieved power given the current sample size and estimated
    effect size between architectures.
    
    Args:
        execution_traces_path: Path to data/processed/execution_traces.csv
        target_effect_size: Target f² (medium effect size per task spec)
        target_power: Target power (0.80)
        alpha: Significance level (0.05)
    
    Returns:
        Dictionary containing:
            - calculated_power: The achieved power given current sample
            - required_sample_size: Sample size needed for target power
            - current_sample_size: Actual number of observations
            - effect_size_estimate: Estimated effect size from data
            - pass_fail: True if calculated_power >= target_power
            - details: Additional metrics
    """
    if not execution_traces_path.exists():
        raise FileNotFoundError(
            f"Execution traces file not found: {execution_traces_path}. "
            "Run T024 (generate_execution_traces) first."
        )
    
    df = pd.read_csv(execution_traces_path)
    
    # Ensure required columns exist
    required_cols = ['architecture', 'violation', 'constraint_count']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Execution traces missing required columns: {missing}. "
            "Expected columns: {required_cols}"
        )
    
    # Calculate group sizes
    group_sizes = df['architecture'].value_counts()
    total_n = len(df)
    
    if len(group_sizes) < 2:
        return {
            "calculated_power": 0.0,
            "required_sample_size": 0,
            "current_sample_size": total_n,
            "effect_size_estimate": 0.0,
            "pass_fail": False,
            "details": {
                "error": "Insufficient groups in data",
                "group_counts": group_sizes.to_dict()
            }
        }
    
    # Calculate violation rates by architecture
    violation_rates = df.groupby('architecture')['violation'].mean()
    
    # Estimate effect size (Cohen's h for proportions)
    if len(violation_rates) >= 2:
        rates = violation_rates.values
        effect_size = calculate_effect_size_for_logistic(
            prop_control=rates[0],
            prop_treatment=rates[1]
        )
    else:
        effect_size = 0.0
    
    # Use F-test power analysis for ANOVA-style comparison (2 groups)
    # This is more appropriate for comparing means across groups
    solver = FTestAnovaPower()
    
    # Calculate achieved power
    try:
        achieved_power = solver.solve(
            effect_size=effect_size,
            nobs=total_n,
            alpha=alpha,
            k_groups=len(group_sizes)
        )
    except Exception:
        # Fallback: if effect size is 0 or very small
        achieved_power = 0.0
    
    # Calculate required sample size for target power
    try:
        required_n = estimate_required_sample_size(
            effect_size=effect_size,
            alpha=alpha,
            power=target_power,
            n_groups=len(group_sizes)
        )
    except Exception:
        required_n = total_n * 2  # Conservative estimate
    
    return {
        "calculated_power": round(float(achieved_power), 4),
        "required_sample_size": required_n,
        "current_sample_size": total_n,
        "effect_size_estimate": round(float(effect_size), 4),
        "pass_fail": bool(achieved_power >= target_power),
        "details": {
            "target_effect_size": target_effect_size,
            "target_power": target_power,
            "alpha": alpha,
            "group_counts": group_sizes.to_dict(),
            "violation_rates": {k: round(float(v), 4) for k, v in violation_rates.to_dict().items()},
            "analysis_method": "FTestAnovaPower (ANOVA-style for 2+ groups)"
        }
    }


def run_power_analysis(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point for power analysis.
    
    Args:
        input_path: Path to execution_traces.csv (default: from config)
        output_path: Path for output JSON (default: from config)
    
    Returns:
        Power analysis results dictionary
    """
    paths = Paths()
    
    if input_path is None:
        input_path = paths.data_processed / "execution_traces.csv"
    
    if output_path is None:
        output_path = paths.data_processed / "power_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Perform analysis
    results = perform_power_analysis(input_path)
    
    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def main():
    """CLI entry point for power analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Perform power analysis on execution traces"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to execution_traces.csv"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for output JSON report"
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=0.15,
        help="Target effect size f² (default: 0.15)"
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.80,
        help="Target power (default: 0.80)"
    )
    
    args = parser.parse_args()
    
    results = run_power_analysis(
        input_path=args.input,
        output_path=args.output
    )
    
    print(f"Power Analysis Complete")
    print(f"  Current Sample Size: {results['current_sample_size']}")
    print(f"  Calculated Power: {results['calculated_power']:.4f}")
    print(f"  Required Sample Size: {results['required_sample_size']}")
    print(f"  Effect Size Estimate: {results['effect_size_estimate']:.4f}")
    print(f"  Pass/Fail (Power >= 0.80): {'PASS' if results['pass_fail'] else 'FAIL'}")
    print(f"\nReport written to: {paths.data_processed / 'power_report.json'}")
    
    if not results['pass_fail']:
        print("\n⚠ WARNING: Current sample size is insufficient for target power.")
        print(f"  Need {results['required_sample_size']} samples for 80% power.")


if __name__ == "__main__":
    main()