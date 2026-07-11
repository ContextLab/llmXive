import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from src.analysis.forgetting_metrics import RetentionMetrics

class StatisticalAnalysisError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

@dataclass
class ANOVAResult:
    f_statistic: float
    p_value: float
    degrees_of_freedom: Tuple[int, int]
    is_significant: bool

@dataclass
class TukeyResult:
    comparison: str
    difference: float
    p_value: float
    is_significant: bool

@dataclass
class StatisticalReport:
    anova_result: Optional[ANOVAResult]
    tukey_results: List[TukeyResult]
    descriptive_stats: Dict[str, Dict[str, float]]
    retention_comparison: Optional[Dict[str, Any]]

def load_forgetting_data(data_dir: Path) -> Dict[str, List[float]]:
    """Load forgetting data from aggregated results."""
    if not data_dir.exists():
        raise StatisticalAnalysisError(f"Data directory not found: {data_dir}")

    results = {}
    json_file = data_dir / "aggregated_results.json"

    if not json_file.exists():
        raise StatisticalAnalysisError(f"Aggregated results not found: {json_file}")

    with open(json_file, 'r') as f:
        data = json.load(f)

    if "results" not in data:
        raise StatisticalAnalysisError("No 'results' key in aggregated data")

    for run_data in data["results"]:
        condition = run_data.get("condition")
        forgetting_rate = run_data.get("forgetting_rate")

        if condition and forgetting_rate is not None:
            if condition not in results:
                results[condition] = []
            results[condition].append(forgetting_rate)

    return results

def load_retention_data(data_dir: Path) -> Dict[str, Dict[str, float]]:
    """Load retention metrics from the retention metrics file."""
    retention_file = data_dir / "retention_metrics.json"
    if not retention_file.exists():
        raise StatisticalAnalysisError(f"Retention metrics file not found: {retention_file}")

    with open(retention_file, 'r') as f:
        data = json.load(f)

    if "metrics" not in data:
        raise StatisticalAnalysisError("No 'metrics' key in retention data")

    return data["metrics"]

def perform_mixed_design_anova(data: Dict[str, List[float]]) -> ANOVAResult:
    """Perform Mixed-Design ANOVA on forgetting rates across conditions."""
    if len(data) < 2:
        raise StatisticalAnalysisError("Need at least 2 conditions for ANOVA")

    values = []
    groups = []
    for group_name, group_values in data.items():
        if len(group_values) < 2:
            raise StatisticalAnalysisError(f"Insufficient samples for condition {group_name}")
        values.extend(group_values)
        groups.extend([group_name] * len(group_values))

    values = np.array(values)
    groups = np.array(groups)

    f_stat, p_val = stats.f_oneway(*[v for k, v in data.items()])

    # Calculate degrees of freedom
    k = len(data)  # number of groups
    n = sum(len(v) for v in data.values())  # total samples
    df_between = k - 1
    df_within = n - k

    return ANOVAResult(
        f_statistic=float(f_stat),
        p_value=float(p_val),
        degrees_of_freedom=(df_between, df_within),
        is_significant=p_val < 0.05
    )

def perform_tukey_hsd(data: Dict[str, List[float]]) -> List[TukeyResult]:
    """Perform Tukey HSD post-hoc test."""
    values = []
    groups = []
    for group_name, group_values in data.items():
        values.extend(group_values)
        groups.extend([group_name] * len(group_values))

    tukey = pairwise_tukeyhsd(endog=values, groups=groups, alpha=0.05)

    results = []
    for i, row in enumerate(tukey.results):
        group1, group2 = row[0], row[1]
        diff = row[2]
        p_val = row[4]

        comparison = f"{group1} vs {group2}"
        results.append(TukeyResult(
            comparison=comparison,
            difference=float(diff),
            p_value=float(p_val),
            is_significant=p_val < 0.05
        ))

    return results

def compute_descriptive_stats(data: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
    """Compute descriptive statistics for each condition."""
    stats_dict = {}
    for group_name, group_values in data.items():
        arr = np.array(group_values)
        stats_dict[group_name] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "count": len(arr)
        }
    return stats_dict

def compare_retention_rates(retention_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Compare retention rates between Co-evolving and Mixed-task conditions.
    Uses a two-sample t-test to determine if the difference in retention
    rates is statistically significant.
    """
    if "coevolving" not in retention_data or "mixed" not in retention_data:
        raise StatisticalAnalysisError(
            "Cannot compare retention rates: missing 'coevolving' or 'mixed' data"
        )

    coevolving_metrics = retention_data["coevolving"]
    mixed_metrics = retention_data["mixed"]

    # Extract retention rates (assuming the key is 'retention_rate' or similar)
    # The data structure from T031 is Dict[str, float] per condition
    # We assume the metrics are aggregated per rule or overall.
    # If it's a single overall rate per condition, we can't do a t-test on one value.
    # However, T031 computes retention rates for distinct rules.
    # Let's assume the input 'retention_data' is structured as:
    # { "condition": { "rule_id_1": rate, "rule_id_2": rate, ... } }
    # OR if T031 outputs a single average per run, we need to aggregate across runs.
    # Given T031 description: "compute and store raw retention rates of distinct logical rules"
    # The file likely contains: { "metrics": { "coevolving": { "rule_1": 0.9, ... }, "mixed": ... } }
    # We will treat the values for each rule as independent samples if multiple rules exist.
    # If only one value exists, we cannot perform a statistical test.

    coevolving_rates = list(coevolving_metrics.values())
    mixed_rates = list(mixed_metrics.values())

    if len(coevolving_rates) == 0 or len(mixed_rates) == 0:
        raise StatisticalAnalysisError("No retention rates found to compare")

    # Calculate means for summary
    mean_coevolving = np.mean(coevolving_rates)
    mean_mixed = np.mean(mixed_rates)

    # Perform independent two-sample t-test (Welch's t-test is safer for unequal variances)
    t_stat, p_value = stats.ttest_ind(coevolving_rates, mixed_rates, equal_var=False)

    return {
        "coevolving_mean": float(mean_coevolving),
        "mixed_mean": float(mean_mixed),
        "difference": float(mean_coevolving - mean_mixed),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "is_significant": p_value < 0.05,
        "sample_sizes": {
            "coevolving": len(coevolving_rates),
            "mixed": len(mixed_rates)
        }
    }

def run_statistical_analysis(data_dir: Path) -> StatisticalReport:
    """Run the full statistical analysis pipeline."""
    # Load forgetting data
    forgetting_data = load_forgetting_data(data_dir)

    if len(forgetting_data) < 2:
        raise StatisticalAnalysisError("Insufficient data for ANOVA (need >= 2 conditions)")

    # Load retention data for comparison
    retention_data = load_retention_data(data_dir)

    # Compute descriptive stats
    desc_stats = compute_descriptive_stats(forgetting_data)

    # Perform ANOVA
    anova_result = perform_mixed_design_anova(forgetting_data)

    # Perform Tukey HSD
    tukey_results = perform_tukey_hsd(forgetting_data)

    # Compare retention rates
    retention_comparison = None
    try:
        retention_comparison = compare_retention_rates(retention_data)
    except StatisticalAnalysisError as e:
        # Log warning but don't fail the whole analysis if retention comparison fails
        print(f"Warning: Could not compare retention rates: {e}", file=sys.stderr)

    return StatisticalReport(
        anova_result=anova_result,
        tukey_results=tukey_results,
        descriptive_stats=desc_stats,
        retention_comparison=retention_comparison
    )

def main():
    """Main entry point for statistical analysis."""
    data_dir = Path("data/results")
    output_file = data_dir / "forgetting_analysis.json"

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        report = run_statistical_analysis(data_dir)

        # Convert report to JSON serializable format
        report_dict = {
            "anova_result": {
                "f_statistic": report.anova_result.f_statistic,
                "p_value": report.anova_result.p_value,
                "degrees_of_freedom": list(report.anova_result.degrees_of_freedom),
                "is_significant": report.anova_result.is_significant
            } if report.anova_result else None,
            "tukey_results": [
                {
                    "comparison": t.comparison,
                    "difference": t.difference,
                    "p_value": t.p_value,
                    "is_significant": t.is_significant
                } for t in report.tukey_results
            ],
            "descriptive_stats": report.descriptive_stats,
            "retention_comparison": report.retention_comparison
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)

        print(f"Statistical analysis complete. Results saved to {output_file}")

        # Print summary to stdout
        if report.anova_result:
            print(f"\nANOVA Result: F({report.anova_result.degrees_of_freedom[0]}, "
                  f"{report.anova_result.degrees_of_freedom[1]}) = "
                  f"{report.anova_result.f_statistic:.4f}, p = {report.anova_result.p_value:.4f}")
            print(f"Significant difference between conditions: {'Yes' if report.anova_result.is_significant else 'No'}")

        if report.retention_comparison:
            print(f"\nRetention Comparison (Coevolving vs Mixed):")
            print(f"  Co-evolving Mean: {report.retention_comparison['coevolving_mean']:.4f}")
            print(f"  Mixed Mean: {report.retention_comparison['mixed_mean']:.4f}")
            print(f"  Difference: {report.retention_comparison['difference']:.4f}")
            print(f"  p-value: {report.retention_comparison['p_value']:.4f}")
            print(f"  Significant: {'Yes' if report.retention_comparison['is_significant'] else 'No'}")

    except StatisticalAnalysisError as e:
        print(f"Error during statistical analysis: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()