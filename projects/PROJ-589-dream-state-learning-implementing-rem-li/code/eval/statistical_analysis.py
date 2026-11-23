"""
Statistical analysis module for Dream-State Learning project.

Implements paired t-tests and Wilcoxon signed-rank tests to compare
experimental (dream-state) vs baseline (continuous training) performance.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy.stats import ttest_rel, wilcoxon
from utils.logger import get_logger
import json
from pathlib import Path
from config import Config

logger = get_logger(__name__)


def load_accuracy_results(results_dir: Path) -> Tuple[List[float], List[float]]:
    """
    Load accuracy results for experimental and baseline models across seeds.

    Expects a directory structure where each seed has a result file containing
    accuracies for both experimental and baseline runs.

    Args:
        results_dir: Path to directory containing seed result files

    Returns:
        Tuple of (experimental_accuracies, baseline_accuracies) as lists of floats
    """
    config = Config()
    experimental_accuracies = []
    baseline_accuracies = []

    # Find all seed result files
    seed_files = sorted(results_dir.glob("seed_*_results.json"))

    if len(seed_files) != config.num_seeds:
        logger.warning(
            f"Expected {config.num_seeds} seed files, found {len(seed_files)}. "
            "Proceeding with available data."
        )

    for seed_file in seed_files:
        with open(seed_file, 'r') as f:
            data = json.load(f)

        # Extract accuracies for this seed
        exp_acc = data.get('experimental_accuracy')
        base_acc = data.get('baseline_accuracy')

        if exp_acc is not None and base_acc is not None:
            experimental_accuracies.append(float(exp_acc))
            baseline_accuracies.append(float(base_acc))
            logger.info(f"Loaded seed {seed_file.stem}: exp={exp_acc:.4f}, base={base_acc:.4f}")
        else:
            logger.warning(f"Missing accuracy data in {seed_file}")

    if len(experimental_accuracies) == 0:
        raise ValueError("No valid accuracy results found. Cannot perform statistical analysis.")

    logger.info(f"Loaded {len(experimental_accuracies)} paired accuracy results")
    return experimental_accuracies, baseline_accuracies


def compute_accuracy_difference(
    experimental: List[float],
    baseline: List[float]
) -> float:
    """
    Compute the mean accuracy difference (experimental - baseline).

    Args:
        experimental: List of experimental model accuracies
        baseline: List of baseline model accuracies

    Returns:
        Mean difference in accuracy
    """
    if len(experimental) != len(baseline):
        raise ValueError(
            f"Mismatched sample sizes: experimental={len(experimental)}, "
            f"baseline={len(baseline)}"
        )

    diff = np.array(experimental) - np.array(baseline)
    mean_diff = float(np.mean(diff))

    logger.info(
        f"Accuracy difference: experimental mean={np.mean(experimental):.4f}, "
        f"baseline mean={np.mean(baseline):.4f}, diff={mean_diff:.4f}"
    )

    return mean_diff


def run_ttest_paired(
    experimental: List[float],
    baseline: List[float],
    alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Run paired t-test to compare experimental vs baseline accuracies.

    Args:
        experimental: List of experimental model accuracies (paired by seed)
        baseline: List of baseline model accuracies (paired by seed)
        alpha: Significance level (default 0.05)

    Returns:
        Tuple of (t_statistic, p_value, is_significant)
    """
    if len(experimental) < 2:
        raise ValueError(
            f"Paired t-test requires at least 2 samples, got {len(experimental)}"
        )

    if len(experimental) != len(baseline):
        raise ValueError(
            f"Mismatched sample sizes: experimental={len(experimental)}, "
            f"baseline={len(baseline)}"
        )

    # Convert to numpy arrays
    exp_arr = np.array(experimental)
    base_arr = np.array(baseline)

    # Run paired t-test using scipy.stats.ttest_rel
    t_stat, p_value = ttest_rel(exp_arr, base_arr)

    is_significant = p_value < alpha

    logger.info(
        f"Paired t-test results: t={t_stat:.4f}, p={p_value:.6f}, "
        f"significant at α={alpha}: {is_significant}"
    )

    return float(t_stat), float(p_value), is_significant


def run_wilcoxon_test(
    experimental: List[float],
    baseline: List[float]
) -> Tuple[float, float]:
    """
    Run Wilcoxon signed-rank test as a non-parametric alternative.

    Args:
        experimental: List of experimental model accuracies
        baseline: List of baseline model accuracies

    Returns:
        Tuple of (statistic, p_value)
    """
    if len(experimental) < 2:
        raise ValueError(
            f"Wilcoxon test requires at least 2 samples, got {len(experimental)}"
        )

    if len(experimental) != len(baseline):
        raise ValueError(
            f"Mismatched sample sizes: experimental={len(experimental)}, "
            f"baseline={len(baseline)}"
        )

    exp_arr = np.array(experimental)
    base_arr = np.array(baseline)

    stat, p_value = wilcoxon(exp_arr, base_arr)

    logger.info(
        f"Wilcoxon test results: statistic={stat:.4f}, p={p_value:.6f}"
    )

    return float(stat), float(p_value)


def analyze_model_performance(
    experimental: List[float],
    baseline: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Comprehensive analysis comparing experimental and baseline models.

    Args:
        experimental: List of experimental accuracies
        baseline: List of baseline accuracies
        alpha: Significance level

    Returns:
        Dictionary containing all analysis results
    """
    # Compute basic statistics
    exp_mean = float(np.mean(experimental))
    exp_std = float(np.std(experimental, ddof=1))
    base_mean = float(np.mean(baseline))
    base_std = float(np.std(baseline, ddof=1))

    # Compute difference
    mean_diff = compute_accuracy_difference(experimental, baseline)

    # Run paired t-test
    t_stat, p_value, is_significant = run_ttest_paired(experimental, baseline, alpha)

    # Run Wilcoxon test
    wilcoxon_stat, wilcoxon_p = run_wilcoxon_test(experimental, baseline)

    result = {
        'sample_size': len(experimental),
        'alpha': alpha,
        'experimental': {
            'mean': exp_mean,
            'std': exp_std,
            'values': experimental
        },
        'baseline': {
            'mean': base_mean,
            'std': base_std,
            'values': baseline
        },
        'difference': {
            'mean': mean_diff,
            'direction': 'experimental_better' if mean_diff > 0 else 'baseline_better'
        },
        'paired_t_test': {
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': is_significant,
            'method': 'ttest_rel (paired t-test)'
        },
        'wilcoxon_test': {
            'statistic': wilcoxon_stat,
            'p_value': wilcoxon_p,
            'method': 'Wilcoxon signed-rank test'
        }
    }

    logger.info(
        f"Analysis complete: p-value={p_value:.6f}, "
        f"significant={is_significant}, diff={mean_diff:.4f}"
    )

    return result


def save_analysis_report(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save analysis results to a JSON file.

    Args:
        results: Dictionary of analysis results
        output_path: Path to save the report
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Analysis report saved to {output_path}")


def load_and_analyze(
    results_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convenience function to load results, perform analysis, and optionally save.

    Args:
        results_dir: Directory containing seed result files (defaults to config)
        output_path: Path to save report (if None, only returns results)

    Returns:
        Analysis results dictionary
    """
    config = Config()

    if results_dir is None:
        results_dir = Path(config.results_dir)

    logger.info(f"Loading results from {results_dir}")
    experimental, baseline = load_accuracy_results(results_dir)

    logger.info("Running statistical analysis")
    results = analyze_model_performance(experimental, baseline)

    if output_path is not None:
        save_analysis_report(results, output_path)

    return results


def main() -> None:
    """
    Main entry point for standalone statistical analysis execution.

    Loads results from configured directory, performs paired t-test analysis,
    and saves the report to data/results/statistical_analysis.json.
    """
    config = Config()
    results_dir = Path(config.results_dir)
    output_path = Path(config.results_dir) / "statistical_analysis.json"

    logger.info("=" * 60)
    logger.info("Starting Statistical Analysis (Task T025)")
    logger.info("=" * 60)

    try:
        # Perform analysis
        results = load_and_analyze(results_dir, output_path)

        # Print summary
        print("\n" + "=" * 60)
        print("STATISTICAL ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Sample Size (paired seeds): {results['sample_size']}")
        print(f"Alpha Level: {results['alpha']}")
        print()
        print(f"Experimental Model:")
        print(f"  Mean Accuracy: {results['experimental']['mean']:.4f}")
        print(f"  Std Deviation: {results['experimental']['std']:.4f}")
        print()
        print(f"Baseline Model:")
        print(f"  Mean Accuracy: {results['baseline']['mean']:.4f}")
        print(f"  Std Deviation: {results['baseline']['std']:.4f}")
        print()
        print(f"Mean Difference (Exp - Base): {results['difference']['mean']:.4f}")
        print(f"  Direction: {results['difference']['direction']}")
        print()
        print(f"Paired T-Test ({results['paired_t_test']['method']}):")
        print(f"  t-statistic: {results['paired_t_test']['t_statistic']:.4f}")
        print(f"  p-value: {results['paired_t_test']['p_value']:.6f}")
        print(f"  Significant (α={results['alpha']}): {results['paired_t_test']['is_significant']}")
        print()
        print(f"Wilcoxon Test ({results['wilcoxon_test']['method']}):")
        print(f"  Statistic: {results['wilcoxon_test']['statistic']:.4f}")
        print(f"  p-value: {results['wilcoxon_test']['p_value']:.6f}")
        print()
        print("=" * 60)
        print(f"Full report saved to: {output_path}")
        print("=" * 60 + "\n")

        if results['paired_t_test']['is_significant']:
            print("✓ RESULT: Dream-state learning shows statistically significant improvement!")
        else:
            print("✗ RESULT: No statistically significant difference detected.")

    except FileNotFoundError as e:
        logger.error(f"Data files not found: {e}")
        print(f"Error: Could not find result files. Ensure experiments have been run.")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        print(f"Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()