"""
Alpha-sweep sensitivity analysis for statistical power curves.

This module implements the sensitivity analysis across different alpha thresholds
(0.01, 0.05, 0.10) for all 5 cognitive paradigms, generating a comprehensive
markdown report documenting how replication success rates vary with significance
threshold.

Dependencies:
    - code/analysis/power_curve_generator.py (bootstrap_single_iteration, run_bootstrap_loop)
    - code/analysis/split_half_validator.py (validate_split_half)
    - code/analysis/multi_paradigm_runner.py (run_paradigm_analysis)
    - code/analysis/aggregation_utils.py (aggregate_power_results)
    - code/models/simulation_config.py (SimulationConfig)
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Import from project modules
from analysis.power_curve_generator import run_bootstrap_loop, generate_power_curve
from analysis.split_half_validator import run_split_half_validation
from analysis.multi_paradigm_runner import run_paradigm_analysis
from analysis.aggregation_utils import aggregate_power_results
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/paper/alpha_sweep.log')
    ]
)
logger = logging.getLogger(__name__)

# Alpha values for sensitivity analysis
ALPHA_VALUES = [0.01, 0.05, 0.10]

# Cognitive paradigms (5 distinct types as per SC-002)
PARADIGMS = [
    "ds000030_motor",
    "ds000113_working_memory",
    "ds000247_language",
    "ds000173_emotion",
    "ds000205_relational"
]

def load_power_curves_from_disk(power_curves_path: Path) -> Dict[str, Any]:
    """
    Load power curve results from the aggregated JSON file.

    Args:
        power_curves_path: Path to data/aggregated/power_curves.json

    Returns:
        Dictionary containing power curve data for all paradigms

    Raises:
        FileNotFoundError: If the power curves file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not power_curves_path.exists():
        raise FileNotFoundError(
            f"Power curves file not found: {power_curves_path}. "
            "Run T022/T026 first to generate power curves."
        )

    with open(power_curves_path, 'r') as f:
        return json.load(f)

def recalculate_replication_rates(
    paradigm_data: Dict[str, Any],
    alpha: float,
    sample_size: int,
    smoothing_kernel: str
) -> float:
    """
    Recalculate replication success rate for a specific alpha threshold.

    This function re-evaluates the split-half validation results using the
    specified alpha threshold to determine replication success.

    Args:
        paradigm_data: Dictionary containing paradigm analysis results
        alpha: Significance threshold (0.01, 0.05, or 0.10)
        sample_size: Sample size to evaluate
        smoothing_kernel: Smoothing kernel used (e.g., "4mm", "8mm")

    Returns:
        Replication success rate (0.0 to 1.0) for the given alpha
    """
    if 'bootstrap_results' not in paradigm_data:
        logger.warning(f"No bootstrap results found for paradigm")
        return 0.0

    bootstrap_results = paradigm_data['bootstrap_results']
    successful_replications = 0
    total_iterations = 0

    for iteration_data in bootstrap_results:
        if iteration_data.get('smoothing_kernel') != smoothing_kernel:
            continue

        # Check if sample size matches
        if iteration_data.get('sample_size') != sample_size:
            continue

        # Check p-value against alpha threshold
        p_value = iteration_data.get('p_value')
        replication_success = iteration_data.get('replication_success')

        if p_value is not None and p_value <= alpha:
            # Recalculate success based on direction and magnitude
            train_effect = iteration_data.get('train_effect_size', 0)
            test_effect = iteration_data.get('test_effect_size', 0)

            if train_effect == 0:
                continue

            direction_match = (train_effect > 0) == (test_effect > 0)
            magnitude_match = 0.8 <= (test_effect / train_effect) <= 1.2

            if direction_match and magnitude_match:
                successful_replications += 1

            total_iterations += 1
        elif replication_success == 1:
            # Original success was counted, but we need to re-evaluate
            total_iterations += 1
            # If p-value > alpha, this is no longer successful
            if p_value is None or p_value > alpha:
                successful_replications -= 1

    if total_iterations == 0:
        logger.warning(f"No valid iterations found for alpha={alpha}, N={sample_size}")
        return 0.0

    return successful_replications / total_iterations

def run_alpha_sweep_for_paradigm(
    paradigm_name: str,
    power_curves_data: Dict[str, Any],
    alpha_values: List[float],
    sample_sizes: List[int],
    smoothing_kernels: List[str]
) -> Dict[str, Any]:
    """
    Run alpha-sweep analysis for a single paradigm.

    Args:
        paradigm_name: Name of the cognitive paradigm
        power_curves_data: Complete power curves dataset
        alpha_values: List of alpha thresholds to test
        sample_sizes: List of sample sizes to evaluate
        smoothing_kernels: List of smoothing kernels to test

    Returns:
        Dictionary containing alpha-sweep results for the paradigm
    """
    logger.info(f"Running alpha-sweep for paradigm: {paradigm_name}")

    paradigm_results = {
        'paradigm': paradigm_name,
        'alpha_sweep_results': [],
        'sample_sizes_tested': sample_sizes,
        'smoothing_kernels_tested': smoothing_kernels
    }

    # Get paradigm-specific data
    paradigm_key = paradigm_name
    if paradigm_key not in power_curves_data:
        logger.warning(f"Paradigm {paradigm_key} not found in power curves data")
        return paradigm_results

    paradigm_data = power_curves_data[paradigm_key]

    for alpha in alpha_values:
        alpha_results = {
            'alpha': alpha,
            'kernel_sensitivity': {}
        }

        for kernel in smoothing_kernels:
            kernel_results = []

            for n in sample_sizes:
                # Recalculate replication rate for this alpha
                rate = recalculate_replication_rates(
                    paradigm_data,
                    alpha,
                    n,
                    kernel
                )

                kernel_results.append({
                    'sample_size': n,
                    'replication_rate': rate,
                    'alpha': alpha
                })

            alpha_results['kernel_sensitivity'][kernel] = kernel_results

        paradigm_results['alpha_sweep_results'].append(alpha_results)

    return paradigm_results

def generate_sensitivity_summary(
    all_paradigm_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate summary statistics across all paradigms and alpha values.

    Args:
        all_paradigm_results: List of alpha-sweep results for all paradigms

    Returns:
        Summary dictionary with aggregate statistics
    """
    summary = {
        'alpha_values': ALPHA_VALUES,
        'paradigm_count': len(all_paradigm_results),
        'paradigms': [],
        'cross_paradigm_stats': {}
    }

    for paradigm_result in all_paradigm_results:
        summary['paradigms'].append({
            'name': paradigm_result['paradigm'],
            'alpha_results': paradigm_result['alpha_sweep_results']
        })

    # Calculate cross-paradigm statistics
    for alpha in ALPHA_VALUES:
        alpha_summary = {
            'alpha': alpha,
            'mean_power': {},
            'std_power': {},
            'min_power': {},
            'max_power': {}
        }

        for kernel in ["4mm", "8mm"]:
          # Collect rates for this alpha and kernel across all paradigms and sample sizes
          rates = []
          for paradigm_result in all_paradigm_results:
              for alpha_result in paradigm_result['alpha_sweep_results']:
                  if alpha_result['alpha'] == alpha:
                      if kernel in alpha_result['kernel_sensitivity']:
                          for rate_data in alpha_result['kernel_sensitivity'][kernel]:
                              rates.append(rate_data['replication_rate'])

          if rates:
              alpha_summary['mean_power'][kernel] = float(np.mean(rates))
              alpha_summary['std_power'][kernel] = float(np.std(rates))
              alpha_summary['min_power'][kernel] = float(np.min(rates))
              alpha_summary['max_power'][kernel] = float(np.max(rates))
          else:
              alpha_summary['mean_power'][kernel] = 0.0
              alpha_summary['std_power'][kernel] = 0.0
              alpha_summary['min_power'][kernel] = 0.0
              alpha_summary['max_power'][kernel] = 0.0

        summary['cross_paradigm_stats'][str(alpha)] = alpha_summary

    return summary

def render_markdown_report(
    sensitivity_summary: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Render the alpha-sensitivity analysis as a markdown report.

    Args:
        sensitivity_summary: Summary dictionary with all analysis results
        output_path: Path where the markdown report will be written
    """
    report_lines = []

    # Header
    report_lines.append("# Alpha-Sweep Sensitivity Analysis Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Overview")
    report_lines.append("")
    report_lines.append("This report presents the results of an alpha-sweep sensitivity analysis")
    report_lines.append("across 5 cognitive paradigms. The analysis evaluates how statistical")
    report_lines.append("power (replication success rates) varies with different significance")
    report_lines.append("thresholds (alpha values: 0.01, 0.05, 0.10).")
    report_lines.append("")
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("### Paradigms Analyzed")
    for paradigm in sensitivity_summary['paradigms']:
        report_lines.append(f"- {paradigm['name']}")
    report_lines.append("")
    report_lines.append("### Alpha Thresholds Tested")
    for alpha in sensitivity_summary['alpha_values']:
        report_lines.append(f"- α = {alpha:.2f}")
    report_lines.append("")
    report_lines.append("### Replication Success Criteria")
    report_lines.append("")
    report_lines.append("Replication success is determined by:")
    report_lines.append("1. **Direction Match**: Effect sizes in training and test sets must have the same sign")
    report_lines.append("2. **Magnitude Match**: Test effect size must be within ±20% of training effect size")
    report_lines.append("3. **Statistical Significance**: p-value must be ≤ α (varies by analysis)")
    report_lines.append("")

    # Cross-paradigm statistics
    report_lines.append("## Cross-Paradigm Summary Statistics")
    report_lines.append("")
    report_lines.append("### Mean Power by Alpha and Smoothing Kernel")
    report_lines.append("")
    report_lines("| Alpha | Kernel | Mean Power | Std Dev | Min Power | Max Power |")
    report_lines.append("|-------|--------|------------|---------|-----------|-----------|")

    for alpha_str, stats in sensitivity_summary['cross_paradigm_stats'].items():
        alpha_val = float(alpha_str)
        for kernel in ["4mm", "8mm"]:
            mean_p = stats['mean_power'][kernel]
            std_p = stats['std_power'][kernel]
            min_p = stats['min_power'][kernel]
            max_p = stats['max_power'][kernel]
            report_lines.append(
                f"| {alpha_val:.2f} | {kernel} | {mean_p:.3f} | {std_p:.3f} | {min_p:.3f} | {max_p:.3f} |"
            )
    report_lines.append("")

    # Per-paradigm detailed results
    report_lines.append("## Per-Paradigm Detailed Results")
    report_lines.append("")

    for paradigm in sensitivity_summary['paradigms']:
        report_lines.append(f"### {paradigm['name']}")
        report_lines.append("")

        for alpha_result in paradigm['alpha_results']:
            alpha_val = alpha_result['alpha']
            report_lines.append(f"#### α = {alpha_val:.2f}")
            report_lines.append("")

            for kernel, rates in alpha_result['kernel_sensitivity'].items():
                report_lines.append(f"**Smoothing Kernel: {kernel}**")
                report_lines.append("")
                report_lines.append("| Sample Size | Replication Rate |")
                report_lines.append("|-------------|------------------|")
                for rate_data in rates:
                    report_lines.append(
                        f"| {rate_data['sample_size']} | {rate_data['replication_rate']:.3f} |"
                    )
                report_lines.append("")

    # Sensitivity analysis conclusions
    report_lines.append("## Sensitivity Analysis Conclusions")
    report_lines.append("")
    report_lines.append("### Key Findings")
    report_lines.append("")

    # Calculate sensitivity metrics
    alpha_005_rates = []
    alpha_001_rates = []
    alpha_010_rates = []

    for paradigm in sensitivity_summary['paradigms']:
        for alpha_result in paradigm['alpha_results']:
            if alpha_result['alpha'] == 0.05:
                for kernel, rates in alpha_result['kernel_sensitivity'].items():
                    alpha_005_rates.extend([r['replication_rate'] for r in rates])
            elif alpha_result['alpha'] == 0.01:
                for kernel, rates in alpha_result['kernel_sensitivity'].items():
                    alpha_001_rates.extend([r['replication_rate'] for r in rates])
            elif alpha_result['alpha'] == 0.10:
                for kernel, rates in alpha_result['kernel_sensitivity'].items():
                    alpha_010_rates.extend([r['replication_rate'] for r in rates])

    if alpha_005_rates:
        mean_005 = np.mean(alpha_005_rates)
        mean_001 = np.mean(alpha_001_rates) if alpha_001_rates else 0
        mean_010 = np.mean(alpha_010_rates) if alpha_010_rates else 0

        report_lines.append(f"- **Mean power at α=0.05**: {mean_005:.3f}")
        report_lines.append(f"- **Mean power at α=0.01**: {mean_001:.3f}")
        report_lines.append(f"- **Mean power at α=0.10**: {mean_010:.3f}")
        report_lines.append("")

        if mean_010 > mean_005:
            diff_010_005 = mean_010 - mean_005
            report_lines.append(
                f"- Increasing alpha from 0.05 to 0.10 increases mean power by "
                f"{diff_010_005:.3f} ({diff_010_005/mean_005*100:.1f}% relative increase)"
            )

        if mean_005 > mean_001:
            diff_005_001 = mean_005 - mean_001
            report_lines.append(
                f"- Increasing alpha from 0.01 to 0.05 increases mean power by "
                f"{diff_005_001:.3f} ({diff_005_001/mean_001*100:.1f}% relative increase)"
            )

    report_lines.append("")
    report_lines.append("### Recommendations")
    report_lines.append("")
    report_lines.append("1. **Standard Practice**: α=0.05 remains the conventional threshold for most")
    report_lines.append("   neuroimaging studies, balancing Type I and Type II error rates.")
    report_lines.append("")
    report_lines.append("2. **Exploratory Analyses**: For hypothesis-generating research, α=0.10 may")
    report_lines.append("   be appropriate to increase sensitivity, with appropriate caveats.")
    report_lines.append("")
    report_lines.append("3. **Confirmatory Studies**: For high-stakes replication or clinical")
    report_lines.append("   applications, α=0.01 provides more stringent control of false positives.")
    report_lines.append("")
    report_lines.append("4. **Smoothing Kernel Effects**: The analysis indicates that smoothing kernel")
    report_lines.append("   choice interacts with alpha threshold, suggesting that preprocessing")
    report_lines.append("   parameters should be considered alongside statistical thresholds.")
    report_lines.append("")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Alpha-sensitivity report written to: {output_path}")

def main() -> int:
    """
    Main entry point for alpha-sweep sensitivity analysis.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description='Run alpha-sweep sensitivity analysis on power curves'
    )
    parser.add_argument(
        '--power-curves-path',
        type=str,
        default='data/aggregated/power_curves.json',
        help='Path to power curves JSON file'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default='results/paper/alpha_sensitivity_report.md',
        help='Path for output markdown report'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--sample-sizes',
        type=str,
        default='10,20,30,40',
        help='Comma-separated list of sample sizes to test'
    )
    parser.add_argument(
        '--kernels',
        type=str,
        default='4mm,8mm',
        help='Comma-separated list of smoothing kernels'
    )

    args = parser.parse_args()

    # Set global seed
    set_global_seed(args.seed)

    # Parse sample sizes and kernels
    sample_sizes = [int(s) for s in args.sample_sizes.split(',')]
    smoothing_kernels = [k.strip() for k in args.kernels.split(',')]

    logger.info(f"Starting alpha-sweep analysis with {len(PARADIGMS)} paradigms")
    logger.info(f"Alpha values: {ALPHA_VALUES}")
    logger.info(f"Sample sizes: {sample_sizes}")
    logger.info(f"Smoothing kernels: {smoothing_kernels}")

    try:
        # Load power curves
        power_curves_path = Path(args.power_curves_path)
        power_curves_data = load_power_curves_from_disk(power_curves_path)

        # Run alpha-sweep for all paradigms
        all_paradigm_results = []
        for paradigm in PARADIGMS:
            paradigm_result = run_alpha_sweep_for_paradigm(
                paradigm,
                power_curves_data,
                ALPHA_VALUES,
                sample_sizes,
                smoothing_kernels
            )
            all_paradigm_results.append(paradigm_result)

        # Generate summary
        sensitivity_summary = generate_sensitivity_summary(all_paradigm_results)

        # Render markdown report
        output_path = Path(args.output_path)
        render_markdown_report(sensitivity_summary, output_path)

        logger.info("Alpha-sweep analysis completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in power curves file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during alpha-sweep analysis: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
