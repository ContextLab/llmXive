"""
Statistical Power Calculator for llmXive Analysis.

This module explicitly calculates statistical power for the observed effect size
and sample size (N=10). It is used to determine if the study is underpowered
(< 0.4) and should warn the report generator to interpret results as "inconclusive".
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from existing API surface
# Note: T029 (tests.py) likely exists in code/analysis/tests.py or similar
# We assume the paired_scores.json structure is available as per T024/T030
# We will implement the power calculation logic here using standard stats formulas
# or scipy if available (listed in requirements).

try:
    from scipy import stats
    from statsmodels.stats.power import TTestPower
    HAS_STATS_MODELS = True
except ImportError:
    HAS_STATS_MODELS = False


def calculate_effect_size_cohen_d(mean_diff: float, std_diff: float) -> float:
    """
    Calculate Cohen's d effect size.
    d = mean_difference / standard_deviation_of_differences
    """
    if std_diff == 0:
        return 0.0
    return mean_diff / std_diff


def calculate_power_t_test(
    effect_size: float,
    n_obs: int,
    alpha: float = 0.05,
    two_tail: bool = True
) -> float:
    """
    Calculate statistical power for a paired t-test given effect size and N.

    Args:
        effect_size: Cohen's d
        n_obs: Number of observations (pairs)
        alpha: Significance level
        two_tail: Whether the test is two-tailed

    Returns:
        Power value between 0 and 1.
    """
    if not HAS_STATS_MODELS:
        # Fallback to approximation if statsmodels is missing
        # Using a simplified approximation: power ~ 1 - beta
        # This is a rough estimate, but ensures the module runs without hard crash
        # if statsmodels is not installed (though it is in requirements).
        # Standard normal approximation for power:
        z_alpha = stats.norm.ppf(1 - alpha / 2) if two_tail else stats.norm.ppf(1 - alpha)
        z_beta = effect_size * math.sqrt(n_obs) - z_alpha
        power = stats.norm.cdf(z_beta)
        return float(power)

    power_analysis = TTestPower()
    power_val = power_analysis.solve_power(
        effect_size=effect_size,
        nobs1=n_obs,
        alpha=alpha,
        alternative='two-sided' if two_tail else 'larger'
    )
    return float(power_val)


def load_paired_scores(filepath: str) -> Tuple[float, float, int]:
    """
    Load paired scores from JSON and calculate mean difference and std dev of differences.

    Returns:
        Tuple of (mean_diff, std_diff, n_obs)
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Paired scores file not found: {filepath}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter for valid entries (assuming structure from T024)
    # We need to calculate differences between Scaffolded and Zero-Shot for each task_id
    # The data structure is likely a list of dicts:
    # [{"task_id": "id", "condition": "zero_shot", "scores": {"scientific_core": 0-50}}, ...]

    # Group by task_id
    task_scores: Dict[str, Dict[str, float]] = {}
    for entry in data:
        tid = entry.get('task_id')
        cond = entry.get('condition')
        score = entry.get('scores', {}).get('scientific_core')

        if tid and cond and score is not None:
            if tid not in task_scores:
                task_scores[tid] = {}
            task_scores[tid][cond] = score

    differences = []
    for tid, scores in task_scores.items():
        if 'scaffolded' in scores and 'zero_shot' in scores:
            diff = scores['scaffolded'] - scores['zero_shot']
            differences.append(diff)

    if not differences:
        raise ValueError("No paired data found to calculate differences.")

    n_obs = len(differences)
    mean_diff = sum(differences) / n_obs
    std_diff = math.sqrt(sum((x - mean_diff) ** 2 for x in differences) / (n_obs - 1)) if n_obs > 1 else 0.0

    return mean_diff, std_diff, n_obs


def calculate_power_report(
    input_file: str,
    output_file: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Main function to calculate power and generate a report.

    This function:
    1. Loads paired scores from `input_file`.
    2. Calculates Cohen's d.
    3. Calculates statistical power.
    4. Returns a dictionary with power metrics and warnings.

    If power < 0.4, the report includes a 'power_warning' field.
    """
    report = {
        "input_file": input_file,
        "alpha": alpha,
        "status": "success"
    }

    try:
        mean_diff, std_diff, n_obs = load_paired_scores(input_file)
        effect_size = calculate_effect_size_cohen_d(mean_diff, std_diff)
        power = calculate_power_t_test(effect_size, n_obs, alpha)

        report.update({
            "mean_difference": mean_diff,
            "std_difference": std_diff,
            "n_obs": n_obs,
            "effect_size_cohen_d": effect_size,
            "power_estimate": power
        })

        if power < 0.4:
            report["power_warning"] = {
                "value": power,
                "threshold": 0.4,
                "recommendation": "Interpret results as 'inconclusive' due to low statistical power.",
                "suggested_action": "Increase sample size (N) to achieve power >= 0.8."
            }
            report["interpretation"] = "inconclusive"
        else:
            report["interpretation"] = "validated"

        # Write report to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return report

    except Exception as e:
        report["status"] = "error"
        report["error_message"] = str(e)
        return report


def main():
    """CLI entry point for power calculation."""
    import argparse

    parser = argparse.ArgumentParser(description="Calculate statistical power for llmXive analysis.")
    parser.add_argument(
        "--input",
        type=str,
        default="results/paired_scores.json",
        help="Path to the paired scores JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/power_analysis_report.json",
        help="Path to write the power analysis report."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)."
    )

    args = parser.parse_args()

    print(f"Calculating power for {args.input}...")
    report = calculate_power_report(args.input, args.output, args.alpha)

    if report["status"] == "error":
        print(f"Error: {report['error_message']}")
        exit(1)

    print(f"Power analysis complete. Report written to {args.output}")
    print(f"Power Estimate: {report['power_estimate']:.4f}")
    if "power_warning" in report:
        print(f"WARNING: Low power detected ({report['power_warning']['value']:.4f} < 0.4).")
        print(f"Recommendation: {report['power_warning']['recommendation']}")


if __name__ == "__main__":
    main()