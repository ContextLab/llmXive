"""
Statistics Module

Provides statistical analysis functions for evaluating geometric consistency
and prompt adherence rates, including power analysis, hypothesis testing,
and final report generation.
"""
import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats

# Custom exceptions
class StudyInvalidError(Exception):
    """Raised when a study is deemed invalid due to statistical or data quality issues."""
    pass

def calculate_effect_size(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h effect size for two proportions.

    Args:
        p1: Proportion for group 1.
        p2: Proportion for group 2.

    Returns:
        Cohen's h effect size.
    """
    # Arcsine transformation
    phi1 = 2 * np.arcsin(np.sqrt(p1))
    phi2 = 2 * np.arcsin(np.sqrt(p2))
    return abs(phi1 - phi2)

def power_analysis_two_proportions(
    effect_size: float,
    alpha: float = 0.05,
    power_target: float = 0.8,
    n_per_group: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform power analysis for two-proportion test.

    Args:
        effect_size: Expected effect size (Cohen's h).
        alpha: Significance level (default 0.05).
        power_target: Target statistical power (default 0.8).
        n_per_group: Optional fixed sample size per group to calculate achieved power.

    Returns:
        Dictionary with power analysis results.
    """
    if n_per_group:
        # Calculate achieved power for given sample size
        # Using normal approximation for two-proportion z-test
        # Power = P(Z > z_crit - delta) + P(Z < -z_crit - delta)
        z_crit = stats.norm.ppf(1 - alpha / 2)
        delta = effect_size * np.sqrt(n_per_group / 2)
        power = stats.norm.cdf(delta - z_crit) + stats.norm.cdf(-delta - z_crit)
        # Ensure power is between 0 and 1
        power = max(0.0, min(1.0, power))
    else:
        # Calculate required sample size for target power
        # Using approximation: n = 2 * (z_alpha + z_beta)^2 / effect_size^2
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power_target)
        n_per_group = int(np.ceil(2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)))
        power = power_target

    return {
        "effect_size": effect_size,
        "alpha": alpha,
        "target_power": power_target,
        "achieved_power": power if n_per_group else None,
        "required_n_per_group": n_per_group if not (n_per_group and effect_size == 0) else None,
        "is_adequate": power >= power_target if n_per_group else None
    }

def two_proportion_z_test(
    successes1: int,
    n1: int,
    successes2: int,
    n2: int,
    alternative: str = "two-sided"
) -> Dict[str, float]:
    """
    Perform two-proportion z-test.

    Args:
        successes1: Number of successes in group 1.
        n1: Total trials in group 1.
        successes2: Number of successes in group 2.
        n2: Total trials in group 2.
        alternative: Type of test ("two-sided", "greater", "less").

    Returns:
        Dictionary with test results (statistic, p-value).
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes cannot be zero")

    prop1 = successes1 / n1
    prop2 = successes2 / n2
    p_pool = (successes1 + successes2) / (n1 + n2)

    if p_pool == 0 or p_pool == 1:
        # Edge case: all successes or all failures
        statistic = 0.0
        p_value = 1.0
    else:
        se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        statistic = (prop1 - prop2) / se

        if alternative == "two-sided":
            p_value = 2 * (1 - stats.norm.cdf(abs(statistic)))
        elif alternative == "greater":
            p_value = 1 - stats.norm.cdf(statistic)
        elif alternative == "less":
            p_value = stats.norm.cdf(statistic)
        else:
            raise ValueError("alternative must be 'two-sided', 'greater', or 'less'")

    return {
        "statistic": statistic,
        "p_value": p_value,
        "prop1": prop1,
        "prop2": prop2,
        "n1": n1,
        "n2": n2
    }

def fisher_exact_test(
    successes1: int,
    failures1: int,
    successes2: int,
    failures2: int,
    alternative: str = "two-sided"
) -> Dict[str, float]:
    """
    Perform Fisher's Exact Test.

    Args:
        successes1: Successes in group 1.
        failures1: Failures in group 1.
        successes2: Successes in group 2.
        failures2: Failures in group 2.
        alternative: Type of test ("two-sided", "greater", "less").

    Returns:
        Dictionary with test results (odds_ratio, p-value).
    """
    contingency = np.array([
        [successes1, failures1],
        [successes2, failures2]
    ])

    # Handle edge cases where all values are zero
    if contingency.sum() == 0:
        return {
            "odds_ratio": 1.0,
            "p_value": 1.0,
            "contingency_table": contingency.tolist()
        }

    try:
        result = stats.fisher_exact(contingency, alternative=alternative)
        return {
            "odds_ratio": result[0],
            "p_value": result[1],
            "contingency_table": contingency.tolist()
        }
    except Exception as e:
        # Fallback for numerical issues
        return {
            "odds_ratio": 1.0,
            "p_value": 1.0,
            "contingency_table": contingency.tolist(),
            "warning": str(e)
        }

def select_statistical_test(
    successes1: int,
    n1: int,
    successes2: int,
    n2: int
) -> str:
    """
    Select appropriate statistical test based on cell counts.

    Args:
        successes1: Successes in group 1.
        n1: Total trials in group 1.
        successes2: Successes in group 2.
        n2: Total trials in group 2.

    Returns:
        "z_test" or "fisher" based on expected cell counts.
    """
    # Calculate expected cell counts for chi-square approximation
    total = n1 + n2
    total_successes = successes1 + successes2
    total_failures = total - total_successes

    if total_successes == 0 or total_failures == 0:
        return "fisher"

    # Expected counts under null hypothesis
    expected_success_rate = total_successes / total
    expected_fail_rate = total_failures / total

    exp_cell1 = n1 * expected_success_rate
    exp_cell2 = n1 * expected_fail_rate
    exp_cell3 = n2 * expected_success_rate
    exp_cell4 = n2 * expected_fail_rate

    min_expected = min(exp_cell1, exp_cell2, exp_cell3, exp_cell4)

    if min_expected < 5:
        return "fisher"
    else:
        return "z_test"

def load_evaluation_results(results_dir: str) -> List[Dict[str, Any]]:
    """
    Load all evaluation result JSON files from a directory.

    Args:
        results_dir: Directory containing evaluation result files.

    Returns:
        List of evaluation result dictionaries.
    """
    results = []
    results_path = Path(results_dir)

    if not results_path.exists():
        return results

    for file_path in results_path.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {file_path}: {e}", file=sys.stderr)

    return results

def aggregate_violation_rates(
    evaluation_results: List[Dict[str, Any]],
    group_key: str = "group"
) -> Dict[str, Dict[str, int]]:
    """
    Aggregate violation rates by group from evaluation results.

    Args:
        evaluation_results: List of evaluation result dictionaries.
        group_key: Key used to identify the group in results.

    Returns:
        Dictionary mapping group names to {total: int, violations: int}.
    """
    aggregation = {}

    for result in evaluation_results:
        group = result.get(group_key, "unknown")
        if group not in aggregation:
            aggregation[group] = {"total": 0, "violations": 0}

        aggregation[group]["total"] += 1
        if result.get("has_violation", False):
            aggregation[group]["violations"] += 1

    return aggregation

def calculate_contradiction_rate(
    contradiction_log: List[Dict[str, Any]],
    total_scenes: int
) -> float:
    """
    Calculate contradiction rate (alias for contradiction_analyzer function).

    Args:
        contradiction_log: List of contradiction records.
        total_scenes: Total number of scenes.

    Returns:
        Contradiction rate percentage.
    """
    if total_scenes == 0:
        return 0.0

    contradictory_ids = set(r.get('scene_id') for r in contradiction_log if 'scene_id' in r)
    return (len(contradictory_ids) / total_scenes) * 100.0

def verify_contradiction_rate(rate: float, threshold: float = 5.0) -> bool:
    """
    Verify contradiction rate is below threshold.

    Args:
        rate: Calculated rate.
        threshold: Maximum allowed rate.

    Returns:
        True if valid, False otherwise.
    """
    return rate <= threshold

def run_power_analysis_and_report(
    baseline_rate: float,
    experimental_rate: float,
    alpha: float = 0.05,
    power_target: float = 0.8,
    n_per_group: int = 100,
    output_path: str = "data/processed/power_analysis_report.json"
) -> Dict[str, Any]:
    """
    Run power analysis and save report.

    Args:
        baseline_rate: Expected baseline violation rate.
        experimental_rate: Expected experimental violation rate.
        alpha: Significance level.
        power_target: Target power.
        n_per_group: Sample size per group.
        output_path: Path to save report.

    Returns:
        Power analysis results dictionary.
    """
    effect_size = calculate_effect_size(baseline_rate, experimental_rate)
    analysis = power_analysis_two_proportions(
        effect_size=effect_size,
        alpha=alpha,
        power_target=power_target,
        n_per_group=n_per_group
    )

    # Add input parameters to report
    analysis["input_parameters"] = {
        "baseline_rate": baseline_rate,
        "experimental_rate": experimental_rate,
        "alpha": alpha,
        "power_target": power_target,
        "n_per_group": n_per_group
    }

    # Save report
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)

    print(f"Power analysis report saved to {output_path}")

    return analysis

def run_statistical_comparison(
    baseline_results: Dict[str, int],
    experimental_results: Dict[str, int],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run statistical comparison between two groups.

    Args:
        baseline_results: {total: int, violations: int} for baseline.
        experimental_results: {total: int, violations: int} for experimental.
        output_path: Optional path to save results.

    Returns:
        Comparison results dictionary.
    """
    b_total = baseline_results["total"]
    b_violations = baseline_results["violations"]
    e_total = experimental_results["total"]
    e_violations = experimental_results["violations"]

    # Select test
    test_type = select_statistical_test(b_violations, b_total, e_violations, e_total)

    result = {
        "test_type": test_type,
        "baseline": baseline_results,
        "experimental": experimental_results
    }

    if test_type == "z_test":
        test_result = two_proportion_z_test(
            successes1=b_violations,
            n1=b_total,
            successes2=e_violations,
            n2=e_total
        )
        result.update(test_result)
    else:
        test_result = fisher_exact_test(
            successes1=b_violations,
            failures1=b_total - b_violations,
            successes2=e_violations,
            failures2=e_total - e_violations
        )
        result.update(test_result)

    # Determine significance
    alpha = 0.05
    result["is_significant"] = result["p_value"] < alpha
    result["alpha"] = alpha

    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"Statistical comparison saved to {output_path}")

    return result

def generate_final_analysis_csv(
    comparison_results: Dict[str, Any],
    power_results: Dict[str, Any],
    contradiction_rate: float,
    output_path: str = "data/processed/final_analysis.csv"
) -> None:
    """
    Generate final analysis CSV with aggregated statistics.

    Args:
        comparison_results: Statistical comparison results.
        power_results: Power analysis results.
        contradiction_rate: Overall contradiction rate.
        output_path: Path to save CSV.
    """
    import csv

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value", "Unit", "Notes"])

        # Prompt Adherence Rate (1 - violation rate)
        baseline_rate = comparison_results["baseline"]["total"] > 0 and \
                        comparison_results["baseline"]["violations"] / comparison_results["baseline"]["total"] or 0
        experimental_rate = comparison_results["experimental"]["total"] > 0 and \
                            comparison_results["experimental"]["violations"] / comparison_results["experimental"]["total"] or 0

        writer.writerow([
            "Baseline Prompt Adherence Rate",
            f"{(1 - baseline_rate) * 100:.2f}",
            "%",
            "1 - violation rate"
        ])
        writer.writerow([
            "Experimental Prompt Adherence Rate",
            f"{(1 - experimental_rate) * 100:.2f}",
            "%",
            "1 - violation rate"
        ])

        # Statistical test results
        writer.writerow([
            "Statistical Test Used",
            comparison_results["test_type"],
            "-",
            "Selected based on cell counts"
        ])
        writer.writerow([
            "P-Value",
            f"{comparison_results['p_value']:.6f}",
            "-",
            f"Alpha = {comparison_results['alpha']}"
        ])
        writer.writerow([
            "Is Significant",
            "Yes" if comparison_results["is_significant"] else "No",
            "-",
            "p < 0.05"
        ])

        # Power analysis
        writer.writerow([
            "Effect Size (Cohen's h)",
            f"{power_results.get('effect_size', 0):.4f}",
            "-",
            "Cohen's h"
        ])
        writer.writerow([
            "Achieved Power",
            f"{power_results.get('achieved_power', 0):.4f}" if power_results.get('achieved_power') else "N/A",
            "-",
            "Target >= 0.8"
        ])

        # Contradiction rate
        writer.writerow([
            "Contradiction Rate",
            f"{contradiction_rate:.2f}",
            "%",
            "Scenes with physics contradictions"
        ])

    print(f"Final analysis CSV saved to {output_path}")

def main() -> int:
    """
    Main entry point for the statistics module script.

    Usage:
        python code/analysis/statistics.py --baseline N --experimental N --output PATH

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run statistical analysis on evaluation results.")
    parser.add_argument("--baseline", type=float, required=True, help="Baseline violation rate")
    parser.add_argument("--experimental", type=float, required=True, help="Experimental violation rate")
    parser.add_argument("--n-per-group", type=int, default=100, help="Sample size per group")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--power-target", type=float, default=0.8, help="Target power")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--contradiction-log", type=str, default=None, help="Path to contradiction log (optional)")
    parser.add_argument("--total-scenes", type=int, default=100, help="Total scenes (for contradiction rate)")

    args = parser.parse_args()

    try:
        # Run power analysis
        power_results = run_power_analysis_and_report(
            baseline_rate=args.baseline,
            experimental_rate=args.experimental,
            alpha=args.alpha,
            power_target=args.power_target,
            n_per_group=args.n_per_group,
            output_path=Path(args.output_dir) / "power_analysis_report.json"
        )

        # Check power adequacy
        if power_results.get("is_adequate") is False:
            raise StudyInvalidError(
                f"Power analysis failed: achieved power {power_results.get('achieved_power')} "
                f"is below target {args.power_target}"
            )

        # Calculate contradiction rate if log provided
        contradiction_rate = 0.0
        if args.contradiction_log:
            from .contradiction_analyzer import load_contradiction_log
            log_data = load_contradiction_log(args.contradiction_log)
            contradiction_rate = calculate_contradiction_rate(log_data, args.total_scenes)

            if not verify_contradiction_rate(contradiction_rate):
                raise StudyInvalidError(
                    f"Contradiction rate {contradiction_rate}% exceeds threshold 5%"
                )

        # Run statistical comparison (simulated with provided rates)
        # In real usage, this would load from evaluation results
        baseline_total = args.n_per_group
        baseline_violations = int(baseline_total * args.baseline)
        experimental_total = args.n_per_group
        experimental_violations = int(experimental_total * args.experimental)

        comparison_results = run_statistical_comparison(
            baseline_results={"total": baseline_total, "violations": baseline_violations},
            experimental_results={"total": experimental_total, "violations": experimental_violations},
            output_path=Path(args.output_dir) / "statistical_comparison.json"
        )

        # Generate final CSV
        generate_final_analysis_csv(
            comparison_results=comparison_results,
            power_results=power_results,
            contradiction_rate=contradiction_rate,
            output_path=Path(args.output_dir) / "final_analysis.csv"
        )

        print("Statistical analysis completed successfully.")
        return 0

    except StudyInvalidError as e:
        print(f"Study Invalid: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
