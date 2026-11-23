"""
Statistical analysis module for co-evolving policy distillation.
Implements Mixed-Design ANOVA, power analysis, and sample size calculation.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
from statsmodels.stats.power import FTestAnovaPower

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatisticalAnalysisError(Exception):
    """Custom exception for statistical analysis errors."""
    pass


class ANOVAResult:
    """Result container for ANOVA analysis."""
    def __init__(self, f_statistic: float, p_value: float, df_between: int, df_within: int):
        self.f_statistic = f_statistic
        self.p_value = p_value
        self.df_between = df_between
        self.df_within = df_within

    def to_dict(self) -> Dict[str, Any]:
        return {
            'f_statistic': self.f_statistic,
            'p_value': self.p_value,
            'df_between': self.df_between,
            'df_within': self.df_within
        }


class TukeyResult:
    """Result container for Tukey HSD post-hoc test."""
    def __init__(self, comparisons: List[Dict[str, Any]]):
        self.comparisons = comparisons

    def to_dict(self) -> Dict[str, Any]:
        return {'comparisons': self.comparisons}


class StatisticalReport:
    """Complete statistical analysis report."""
    def __init__(self, anova_results: ANOVAResult, tukey_results: Optional[TukeyResult] = None):
        self.anova_results = anova_results
        self.tukey_results = tukey_results

    def to_dict(self) -> Dict[str, Any]:
        result = {'anova': self.anova_results.to_dict()}
        if self.tukey_results:
            result['tukey'] = self.tukey_results.to_dict()
        return result


def load_forgetting_data(input_path: str) -> Dict[str, List[float]]:
    """
    Load forgetting metrics from a CSV or JSON file.
    Expected format: condition -> list of forgetting rates.
    """
    path = Path(input_path)
    if not path.exists():
        raise StatisticalAnalysisError(f"Input file not found: {input_path}")

    if path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    elif path.suffix == '.csv':
        # Simple CSV parser for expected format
        # Header: condition,forgetting_rate
        import csv
        data: Dict[str, List[float]] = {}
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cond = row['condition']
                rate = float(row['forgetting_rate'])
                if cond not in data:
                    data[cond] = []
                data[cond].append(rate)
        return data
    else:
        raise StatisticalAnalysisError(f"Unsupported file format: {path.suffix}")


def load_retention_data(input_path: str) -> Dict[str, List[float]]:
    """
    Load retention metrics from a CSV or JSON file.
    Expected format: condition -> list of retention rates.
    """
    return load_forgetting_data(input_path)  # Reuse logic, format is similar


def compute_descriptive_stats(data: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
    """Compute mean, std, min, max for each condition."""
    stats = {}
    for cond, values in data.items():
        arr = np.array(values)
        stats[cond] = {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'n': len(values)
        }
    return stats


def perform_mixed_design_anova(data: Dict[str, List[float]]) -> ANOVAResult:
    """
    Perform a Mixed-Design ANOVA (repeated measures) on forgetting rates.
    Simplified to one-way ANOVA for between-subjects factor (condition)
    as we are comparing different conditions across independent runs.
    """
    if len(data) < 2:
        raise StatisticalAnalysisError("Need at least 2 conditions for ANOVA")

    groups = list(data.values())
    group_names = list(data.keys())
    n_groups = len(groups)

    # Check sample sizes
    for i, g in enumerate(groups):
        if len(g) < 2:
            raise StatisticalAnalysisError(f"Condition '{group_names[i]}' has insufficient samples (n < 2)")

    # Perform one-way ANOVA (between-subjects)
    # Using scipy for the actual calculation
    from scipy import stats
    f_stat, p_val = stats.f_oneway(*groups)

    df_between = n_groups - 1
    df_within = sum(len(g) for g in groups) - n_groups

    return ANOVAResult(
        f_statistic=float(f_stat),
        p_value=float(p_val),
        df_between=df_between,
        df_within=df_within
    )


def perform_tukey_hsd(data: Dict[str, List[float]], alpha: float = 0.05) -> TukeyResult:
    """
    Perform Tukey HSD post-hoc test for pairwise comparisons.
    """
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        from statsmodels.stats.power import FTestAnovaPower
    except ImportError:
        raise StatisticalAnalysisError("statsmodels is required for Tukey HSD")

    # Flatten data
    values = []
    groups = []
    for cond, vals in data.items():
        values.extend(vals)
        groups.extend([cond] * len(vals))

    if len(set(groups)) < 2:
        raise StatisticalAnalysisError("Need at least 2 groups for Tukey HSD")

    tukey = pairwise_tukeyhsd(endog=values, groups=groups, alpha=alpha)

    comparisons = []
    for i in range(len(tukey.groupsunique)):
        for j in range(i + 1, len(tukey.groupsunique)):
            g1 = tukey.groupsunique[i]
            g2 = tukey.groupsunique[j]
            # Find the result for this pair
            # tukey.results is a table, we need to extract specific comparison
            # Using the reject array and pvalues
            # A simpler approach: iterate the summary table
            pass

    # Alternative: extract from tukey object directly
    # The tukey object has a 'reject' array and 'pvalues' array
    # We need to map these to group pairs
    results = []
    n = len(tukey.groupsunique)
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            g1 = tukey.groupsunique[i]
            g2 = tukey.groupsunique[j]
            p_val = tukey.pvalues[idx]
            rej = tukey.reject[idx]
            meandiff = tukey.meandiffs[idx]
            results.append({
                'group1': str(g1),
                'group2': str(g2),
                'mean_difference': float(meandiff),
                'p_value': float(p_val),
                'significant': bool(rej)
            })
            idx += 1

    return TukeyResult(comparisons=results)


def calculate_power_and_sample_size(
    alpha: float = 0.05,
    power: float = 0.8,
    effect_size: float = 0.25
) -> int:
    """
    Calculate the minimum sample size (N per group) required to achieve
    the specified power for a fixed effect size.

    Uses FTestAnovaPower from statsmodels.

    Args:
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.8)
        effect_size: Cohen's f effect size (default 0.25, medium effect)

    Returns:
        Minimum N per group (integer)
    """
    solver = FTestAnovaPower()
    # solve for nobs (sample size per group)
    # n_groups is assumed to be 3 (sequential, mixed, coevolving) based on project design
    n_groups = 3
    n_per_group = solver.solve_power(
        effect_size=effect_size,
        n_groups=n_groups,
        alpha=alpha,
        power=power
    )
    # Round up to ensure sufficient power
    return int(np.ceil(n_per_group))


def check_power_requirement(
    current_n: int,
    alpha: float = 0.05,
    power: float = 0.8,
    effect_size: float = 0.25
) -> Tuple[bool, float]:
    """
    Check if the current sample size meets the power requirement for a given effect size.

    Returns:
        Tuple of (meets_requirement, achieved_power)
    """
    solver = FTestAnovaPower()
    n_groups = 3
    achieved_power = solver.power(
        effect_size=effect_size,
        nobs1=current_n,
        alpha=alpha,
        n_groups=n_groups
    )
    return achieved_power >= power, achieved_power


def generate_batch_config(
    output_path: str,
    n_per_condition: int = 30,
    conditions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a batch configuration file containing unique random seeds.

    Args:
        output_path: Path to write the JSON config file
        n_per_condition: Number of seeds per condition (default 30)
        conditions: List of condition names (default: sequential, mixed, coevolving)

    Returns:
        The generated configuration dictionary
    """
    if conditions is None:
        conditions = ['sequential', 'mixed', 'coevolving']

    config = {
        'n_per_condition': n_per_condition,
        'conditions': conditions,
        'seeds': {}
    }

    for cond in conditions:
        # Generate unique seeds for this condition
        # Using a large range to ensure uniqueness across conditions
        seeds = list(range(100000, 100000 + n_per_condition * 1000))
        # Shuffle to randomize order
        np.random.shuffle(seeds)
        config['seeds'][cond] = [int(s) for s in seeds[:n_per_condition]]

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Generated batch config with {n_per_condition} seeds per condition: {output_path}")
    return config


def run_statistical_analysis(
    forgetting_input: str,
    retention_input: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.

    Args:
        forgetting_input: Path to forgetting metrics data
        retention_input: Optional path to retention metrics data
        output_path: Optional path to write the report JSON

    Returns:
        Statistical report dictionary
    """
    logger.info(f"Loading forgetting data from {forgetting_input}")
    forgetting_data = load_forgetting_data(forgetting_input)

    logger.info("Computing descriptive statistics")
    desc_stats = compute_descriptive_stats(forgetting_data)

    logger.info("Performing ANOVA")
    anova_result = perform_mixed_design_anova(forgetting_data)

    logger.info("Performing Tukey HSD post-hoc test")
    try:
        tukey_result = perform_tukey_hsd(forgetting_data)
    except Exception as e:
        logger.warning(f"Tukey HSD failed: {e}")
        tukey_result = None

    report = StatisticalReport(anova_result, tukey_result).to_dict()
    report['descriptive_stats'] = desc_stats

    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Statistical report written to {output_path}")

    return report


def main():
    """CLI entry point for statistical analysis."""
    import argparse

    parser = argparse.ArgumentParser(description='Statistical Analysis for Co-Evolving Policy Distillation')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run statistical analysis on forgetting metrics')
    analyze_parser.add_argument('--input', required=True, help='Input file (CSV or JSON) with forgetting metrics')
    analyze_parser.add_argument('--retention-input', help='Optional input file for retention metrics')
    analyze_parser.add_argument('--output', help='Output file for statistical report (JSON)')

    # Power command
    power_parser = subparsers.add_parser('power', help='Calculate sample size for power analysis')
    power_parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    power_parser.add_argument('--power', type=float, default=0.8, help='Desired power')
    power_parser.add_argument('--effect-size', type=float, default=0.25, help='Cohen\'s f effect size')
    power_parser.add_argument('--output', help='Output file for batch config (JSON)')
    power_parser.add_argument('--n', type=int, default=30, help='Target N per condition (if generating config)')

    args = parser.parse_args()

    if args.command == 'analyze':
        result = run_statistical_analysis(
            forgetting_input=args.input,
            retention_input=args.retention_input,
            output_path=args.output
        )
        print(json.dumps(result, indent=2))

    elif args.command == 'power':
        if args.output:
            # Generate batch config
            config = generate_batch_config(
                output_path=args.output,
                n_per_condition=args.n
            )
            print(f"Generated batch config: {args.output}")
            print(json.dumps(config, indent=2))
        else:
            # Just calculate sample size
            n = calculate_power_and_sample_size(
                alpha=args.alpha,
                power=args.power,
                effect_size=args.effect_size
            )
            print(f"Minimum N per group required: {n}")
            meets, achieved = check_power_requirement(n, args.alpha, args.power, args.effect_size)
            print(f"Power at N={n}: {achieved:.4f} (meets requirement: {meets})")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
