"""
Command Line Interface for the embodied curriculum learning analysis pipeline.
"""
import argparse
import sys
import json
import os
import logging
from typing import List, Optional

from .logging_config import setup_logging
from .data_loader import load_public_dataset, calculate_gain_scores, write_processed_data
from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from .stats_engine import (
    run_t_test, calculate_effect_size, calculate_confidence_interval,
    apply_bonferroni_correction, frame_inference, check_collinearity,
    calculate_power, aggregate_results
)
from .sensitivity import run_sensitivity_sweep, aggregate_results_for_report
from .models import AnalysisResult, SensitivitySweep

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument("--mode", type=str, required=True, choices=["secondary_analysis", "synthetic"],
                        help="Mode of operation: 'secondary_analysis' for public data, 'synthetic' for generated data.")
    parser.add_argument("--input", type=str, help="Path to input data file (required for secondary_analysis).")
    parser.add_argument("--sweep_thresholds", type=str, help="Comma-separated list of thresholds for sensitivity sweep (e.g., 0.01,0.05,0.1).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=str, default="data/processed/results.json", help="Path to output results JSON.")
    return parser.parse_args()


def run_secondary_analysis(input_path: str, sweep_thresholds: Optional[List[float]], seed: int, output_path: str) -> None:
    """
    Run analysis on a public dataset.

    Args:
        input_path (str): Path to input data.
        sweep_thresholds (Optional[List[float]]): Thresholds for sensitivity sweep.
        seed (int): Random seed.
        output_path (str): Path to output file.
    """
    logger.info(f"Starting secondary analysis with input: {input_path}")
    records = load_public_dataset(input_path)
    records = calculate_gain_scores(records)

    if not records:
        logger.error("No valid records to analyze.")
        return

    # Separate groups
    embodied = [r.post_test_score - r.pre_test_score for r in records if r.instruction_type == "embodied"]
    static = [r.post_test_score - r.pre_test_score for r in records if r.instruction_type == "static"]

    if not embodied or not static:
        logger.error("Missing one of the required groups (embodied or static).")
        return

    t_stat, p_val = run_t_test(embodied, static)
    effect = calculate_effect_size(embodied, static)
    ci = calculate_confidence_interval(embodied, static)
    power = calculate_power(embodied, static)

    caveats = frame_inference(effect, p_val, [])
    collinearity = check_collinearity({"embodied": embodied, "static": static})

    sweep_results = []
    if sweep_thresholds:
        sweep_results = run_sensitivity_sweep(embodied, static, sweep_thresholds)

    robustness_warning = None
    if sweep_results:
        from .sensitivity import check_robustness_warning
        robustness_warning = check_robustness_warning(sweep_results)

    result = aggregate_results(t_stat, p_val, effect, ci, caveats, power, collinearity, robustness_warning)

    report = aggregate_results_for_report(result, sweep_results)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Analysis complete. Results written to {output_path}")


def run_synthetic_generation(sweep_thresholds: Optional[List[float]], seed: int, output_path: str) -> None:
    """
    Generate synthetic data and run analysis.

    Args:
        sweep_thresholds (Optional[List[float]]): Thresholds for sensitivity sweep.
        seed (int): Random seed.
        output_path (str): Path to output file.
    """
    logger.info(f"Starting synthetic generation with seed: {seed}")

    # Generate mapping log for synthetic mode
    mapping_log_path = "data/synthetic/mapping_log.json"
    generate_mapping_log(mapping_log_path)

    records = SyntheticDataGenerator.generate(sample_size=100, seed=seed)

    embodied = [r.post_test_score - r.pre_test_score for r in records if r.instruction_type == "embodied"]
    static = [r.post_test_score - r.pre_test_score for r in records if r.instruction_type == "static"]

    if not embodied or not static:
        logger.error("Failed to generate valid groups.")
        return

    t_stat, p_val = run_t_test(embodied, static)
    effect = calculate_effect_size(embodied, static)
    ci = calculate_confidence_interval(embodied, static)
    power = calculate_power(embodied, static)

    caveats = frame_inference(effect, p_val, [])
    collinearity = check_collinearity({"embodied": embodied, "static": static})

    sweep_results = []
    if sweep_thresholds:
        sweep_results = run_sensitivity_sweep(embodied, static, sweep_thresholds)

    robustness_warning = None
    if sweep_results:
        from .sensitivity import check_robustness_warning
        robustness_warning = check_robustness_warning(sweep_results)

    result = aggregate_results(t_stat, p_val, effect, ci, caveats, power, collinearity, robustness_warning)

    report = aggregate_results_for_report(result, sweep_results)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Synthetic analysis complete. Results written to {output_path}")


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()
    setup_logging()

    try:
        thresholds = [float(x) for x in args.sweep_thresholds.split(',')] if args.sweep_thresholds else None
    except ValueError:
        logger.error("Invalid sweep_thresholds format. Use comma-separated floats.")
        sys.exit(1)

    if args.mode == "secondary_analysis":
        if not args.input:
            logger.error("--input is required for secondary_analysis mode.")
            sys.exit(1)
        run_secondary_analysis(args.input, thresholds, args.seed, args.output)
    elif args.mode == "synthetic":
        run_synthetic_generation(thresholds, args.seed, args.output)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)
