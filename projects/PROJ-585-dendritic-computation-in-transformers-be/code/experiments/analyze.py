"""
Statistical analysis module for dendritic transformer experiments.

This module implements statistical tests (Wilcoxon signed-rank, paired t-test)
and multiple hypothesis correction (Benjamini-Hochberg) to analyze the
performance of dendritic vs baseline models across layers and thresholds.
"""

import os
import sys
import json
import csv
import argparse
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProbeResult:
    """Result from a single probing experiment."""
    layer_name: str
    model_type: str  # 'baseline' or 'dendritic'
    threshold: Optional[float]  # None for baseline
    accuracy: float
    f1_score: float
    seed: int
    checkpoint_path: str


@dataclass
class AnalysisResult:
    """Result from statistical analysis of probe results."""
    layer_name: str
    test_type: str  # 'wilcoxon' or 't_test'
    statistic: float
    p_value: float
    effect_size: float  # Cohen's d or rank-biserial correlation
    significant: bool
    corrected_p_value: float
    significant_after_correction: bool
    n_pairs: int
    mean_diff: float
    std_diff: float


def load_probe_results(input_dir: str) -> List[ProbeResult]:
    """
    Load probe results from CSV files in the input directory.

    Args:
        input_dir: Directory containing probe result CSV files.

    Returns:
        List of ProbeResult objects.
    """
    results = []
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    csv_files = list(input_path.glob("probe_results_*.csv"))
    if not csv_files:
        logger.warning(f"No probe result CSV files found in {input_dir}")
        return results

    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(ProbeResult(
                    layer_name=row['layer_name'],
                    model_type=row['model_type'],
                    threshold=float(row['threshold']) if row['threshold'] != 'None' else None,
                    accuracy=float(row['accuracy']),
                    f1_score=float(row['f1_score']),
                    seed=int(row['seed']),
                    checkpoint_path=row['checkpoint_path']
                ))

    logger.info(f"Loaded {len(results)} probe results from {len(csv_files)} files")
    return results


def pair_results(results: List[ProbeResult]) -> Dict[str, List[Tuple[ProbeResult, ProbeResult]]]:
    """
    Pair baseline and dendritic results for the same layer, seed, and threshold.

    Args:
        results: List of ProbeResult objects.

    Returns:
        Dictionary mapping layer names to lists of (baseline, dendritic) pairs.
    """
    # Group by layer, seed, and threshold
    grouped: Dict[Tuple[str, int, Optional[float]], List[ProbeResult]] = {}

    for result in results:
        key = (result.layer_name, result.seed, result.threshold)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(result)

    # Pair baseline and dendritic
    paired: Dict[str, List[Tuple[ProbeResult, ProbeResult]]] = {}

    for (layer_name, seed, threshold), group in grouped.items():
        baseline = next((r for r in group if r.model_type == 'baseline'), None)
        dendritic = next((r for r in group if r.model_type == 'dendritic'), None)

        if baseline and dendritic:
            if layer_name not in paired:
                paired[layer_name] = []
            paired[layer_name].append((baseline, dendritic))

    logger.info(f"Paired {sum(len(v) for v in paired.values())} results across {len(paired)} layers")
    return paired


def wilcoxon_signed_rank_test(baseline_values: List[float], dendritic_values: List[float]) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test.

    Args:
        baseline_values: List of baseline accuracy values.
        dendritic_values: List of dendritic accuracy values.

    Returns:
        Tuple of (statistic, p_value).
    """
    if len(baseline_values) != len(dendritic_values):
        raise ValueError("Input lists must have the same length")

    if len(baseline_values) < 3:
        logger.warning("Too few samples for Wilcoxon test, returning NaN")
        return float('nan'), float('nan')

    statistic, p_value = stats.wilcoxon(baseline_values, dendritic_values)
    return float(statistic), float(p_value)


def paired_t_test(baseline_values: List[float], dendritic_values: List[float]) -> Tuple[float, float]:
    """
    Perform paired t-test.

    Args:
        baseline_values: List of baseline accuracy values.
        dendritic_values: List of dendritic accuracy values.

    Returns:
        Tuple of (statistic, p_value).
    """
    if len(baseline_values) != len(dendritic_values):
        raise ValueError("Input lists must have the same length")

    if len(baseline_values) < 3:
        logger.warning("Too few samples for t-test, returning NaN")
        return float('nan'), float('nan')

    statistic, p_value = stats.ttest_rel(baseline_values, dendritic_values)
    return float(statistic), float(p_value)


def compute_effect_size(baseline_values: List[float], dendritic_values: List[float], test_type: str) -> float:
    """
    Compute effect size (Cohen's d for t-test, rank-biserial for Wilcoxon).

    Args:
        baseline_values: List of baseline accuracy values.
        dendritic_values: List of dendritic accuracy values.
        test_type: 't_test' or 'wilcoxon'.

    Returns:
        Effect size value.
    """
    if len(baseline_values) != len(dendritic_values) or len(baseline_values) < 2:
        return float('nan')

    if test_type == 't_test':
        # Cohen's d for paired samples
        diff = np.array(dendritic_values) - np.array(baseline_values)
        mean_diff = np.mean(diff)
        std_diff = np.std(diff, ddof=1)
        if std_diff == 0:
            return 0.0
        return float(mean_diff / std_diff)

    elif test_type == 'wilcoxon':
        # Rank-biserial correlation for Wilcoxon
        n = len(baseline_values)
        statistic, _ = stats.wilcoxon(baseline_values, dendritic_values)
        # Rank-biserial = 1 - (2 * W) / (n * (n + 1))
        r_biserial = 1 - (2 * statistic) / (n * (n + 1))
        return float(r_biserial)

    else:
        raise ValueError(f"Unknown test type: {test_type}")


def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, bool]]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level.

    Returns:
        List of (corrected_p_value, is_significant) tuples.
    """
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values with their original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]

    # Calculate corrected p-values
    corrected_p_values = [0.0] * n
    for i, p in enumerate(sorted_p_values):
        # BH procedure: p_corrected = p * n / rank
        rank = i + 1
        corrected_p = p * n / rank
        corrected_p = min(corrected_p, 1.0)  # Cap at 1.0
        corrected_p_values[sorted_indices[i]] = corrected_p

    # Determine significance
    results = []
    for i, p_corr in enumerate(corrected_p_values):
        is_sig = p_corr < alpha
        results.append((p_corr, is_sig))

    return results


def analyze_layer_performance(paired_results: Dict[str, List[Tuple[ProbeResult, ProbeResult]]],
                              use_wilcoxon: bool = True,
                              use_t_test: bool = False) -> List[AnalysisResult]:
    """
    Analyze performance differences across layers.

    Args:
        paired_results: Dictionary of paired baseline/dendritic results by layer.
        use_wilcoxon: Whether to use Wilcoxon signed-rank test.
        use_t_test: Whether to use paired t-test.

    Returns:
        List of AnalysisResult objects.
    """
    if not use_wilcoxon and not use_t_test:
        logger.warning("No test specified, defaulting to Wilcoxon")
        use_wilcoxon = True

    all_results = []
    all_p_values = []

    # First pass: collect all p-values for correction
    for layer_name, pairs in paired_results.items():
        baseline_vals = [p[0].accuracy for p in pairs]
        dendritic_vals = [p[1].accuracy for p in pairs]

        if use_wilcoxon:
            _, p_val = wilcoxon_signed_rank_test(baseline_vals, dendritic_vals)
            test_type = 'wilcoxon'
        else:
            _, p_val = paired_t_test(baseline_vals, dendritic_vals)
            test_type = 't_test'

        all_p_values.append(p_val)

    # Apply BH correction
    corrected_results = benjamini_hochberg_correction(all_p_values)

    # Second pass: create results with corrected p-values
    for idx, (layer_name, pairs) in enumerate(paired_results.items()):
        baseline_vals = [p[0].accuracy for p in pairs]
        dendritic_vals = [p[1].accuracy for p in pairs]

        if use_wilcoxon:
            statistic, p_value = wilcoxon_signed_rank_test(baseline_vals, dendritic_vals)
            test_type = 'wilcoxon'
        else:
            statistic, p_value = paired_t_test(baseline_vals, dendritic_vals)
            test_type = 't_test'

        effect_size = compute_effect_size(baseline_vals, dendritic_vals, test_type)
        corrected_p, is_sig_corr = corrected_results[idx]
        is_sig = p_value < 0.05

        mean_diff = np.mean(dendritic_vals) - np.mean(baseline_vals)
        std_diff = np.std([d - b for b, d in zip(baseline_vals, dendritic_vals)], ddof=1)

        all_results.append(AnalysisResult(
            layer_name=layer_name,
            test_type=test_type,
            statistic=statistic,
            p_value=p_value,
            effect_size=effect_size,
            significant=is_sig,
            corrected_p_value=corrected_p,
            significant_after_correction=is_sig_corr,
            n_pairs=len(pairs),
            mean_diff=mean_diff,
            std_diff=std_diff
        ))

    return all_results


def analyze_threshold_sensitivity(paired_results: Dict[str, List[Tuple[ProbeResult, ProbeResult]]],
                                  thresholds: List[float]) -> Dict[str, List[AnalysisResult]]:
    """
    Analyze sensitivity to different dendritic thresholds.

    Args:
        paired_results: Dictionary of paired results by layer.
        thresholds: List of threshold values to analyze.

    Returns:
        Dictionary mapping thresholds to lists of AnalysisResult objects.
    """
    threshold_results = {}

    for threshold in thresholds:
        # Filter results for this threshold
        threshold_pairs = {
            layer: [(b, d) for b, d in pairs if d.threshold == threshold]
            for layer, pairs in paired_results.items()
            if any(d.threshold == threshold for _, d in pairs)
        }

        if threshold_pairs:
          results = analyze_layer_performance(threshold_pairs, use_wilcoxon=True)
          threshold_results[str(threshold)] = results
          logger.info(f"Analyzed threshold {threshold}: {len(results)} layers")

    return threshold_results


def save_results(results: List[AnalysisResult], output_path: str):
    """
    Save analysis results to CSV and JSON files.

    Args:
        results: List of AnalysisResult objects.
        output_path: Output file path (without extension).
    """
    # Save as CSV
    csv_path = f"{output_path}.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=AnalysisResult.__dataclass_fields__.keys())
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))

    # Save as JSON
    json_path = f"{output_path}.json"
    with open(json_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    logger.info(f"Saved results to {csv_path} and {json_path}")


def main():
    """Main entry point for analysis script."""
    parser = argparse.ArgumentParser(description='Analyze probe results with statistical tests')
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Directory containing probe result CSV files')
    parser.add_argument('--output-dir', type=str, default='artifacts/results',
                        help='Output directory for analysis results')
    parser.add_argument('--config', type=str, default='code/config/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--use-wilcoxon', action='store_true', default=True,
                        help='Use Wilcoxon signed-rank test (default)')
    parser.add_argument('--use-t-test', action='store_true', default=False,
                        help='Use paired t-test instead')

    args = parser.parse_args()

    # Load configuration if provided
    thresholds = [0.1, 0.5, 0.9]  # Default from FR-007
    if os.path.exists(args.config):
        try:
            import yaml
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
                if 'dendritic_thresholds' in config:
                    thresholds = config['dendritic_thresholds']
                    logger.info(f"Loaded thresholds from config: {thresholds}")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")

    # Load and pair results
    logger.info(f"Loading probe results from {args.input_dir}")
    results = load_probe_results(args.input_dir)

    if not results:
        logger.error("No probe results found. Exiting.")
        sys.exit(1)

    paired = pair_results(results)

    if not paired:
        logger.error("No paired results found. Exiting.")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Analyze overall performance
    logger.info("Analyzing layer performance...")
    analysis_results = analyze_layer_performance(
        paired,
        use_wilcoxon=args.use_wilcoxon,
        use_t_test=args.use_t_test
    )

    # Save overall results
    save_results(analysis_results, os.path.join(args.output_dir, 'layer_analysis'))

    # Analyze threshold sensitivity if dendritic thresholds are present
    dendritic_results = [r for r in results if r.model_type == 'dendritic']
    if dendritic_results:
        logger.info("Analyzing threshold sensitivity...")
        threshold_analysis = analyze_threshold_sensitivity(paired, thresholds)

        for threshold_str, thr_results in threshold_analysis.items():
            save_results(thr_results, os.path.join(args.output_dir, f'threshold_{threshold_str}_analysis'))

    # Print summary
    logger.info("\n=== Analysis Summary ===")
    significant_count = sum(1 for r in analysis_results if r.significant_after_correction)
    logger.info(f"Significant differences (BH-corrected): {significant_count}/{len(analysis_results)} layers")

    for result in analysis_results:
        sig_marker = "*" if result.significant_after_correction else " "
        logger.info(f"{sig_marker} {result.layer_name}: p={result.corrected_p_value:.4f}, "
                    f"effect_size={result.effect_size:.3f}, diff={result.mean_diff:.4f}")

    logger.info("Analysis complete.")


if __name__ == '__main__':
    main()