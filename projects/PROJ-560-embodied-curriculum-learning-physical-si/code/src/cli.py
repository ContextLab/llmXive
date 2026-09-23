import argparse
import sys
import json
import os
import logging
from typing import List, Optional

from .logging_config import setup_logging
from .data_loader import load_public_dataset, generate_synthetic_fallback, calculate_gain_scores, write_processed_data, handle_synthetic_fallback_failure
from .stats_engine import run_ancova, run_t_test, calculate_effect_size, calculate_confidence_interval, apply_bonferroni_correction, check_collinearity, calculate_power, frame_inference, aggregate_results, write_analysis_results
from .sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
from .models import DatasetRecord, AnalysisResult, SensitivitySweep
from .utils import set_seed

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis CLI")
    parser.add_argument("--mode", type=str, required=True, choices=["secondary_analysis", "synthetic"],
                        help="Mode of operation: 'secondary_analysis' for public data, 'synthetic' for generated data.")
    parser.add_argument("--input", type=str, default=None, help="Path to input CSV/JSON file (for secondary_analysis).")
    parser.add_argument("--sweep_thresholds", type=str, default="0.01,0.05,0.10",
                        help="Comma-separated list of significance thresholds for sensitivity sweep.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--concept_definition", type=str, default=None, help="Concept definition string (for synthetic mode).")
    parser.add_argument("--n", type=int, default=1000, help="Number of records to generate (for synthetic mode).")
    return parser.parse_args()

def run_secondary_analysis(input_path: str, sweep_thresholds: List[float], seed: int) -> dict:
    """
    Run analysis on public data.
    """
    set_seed(seed)
    logger.info(f"Loading public dataset from {input_path}")
    records = load_public_dataset(input_path)
    
    if not records:
        logger.error("No records loaded from public dataset.")
        return {}

    # Calculate gain scores
    gain_records = calculate_gain_scores(records)
    write_processed_data(gain_records, "data/processed/validated_fallback.csv")

    # Run primary stats
    ancova_result = run_ancova(gain_records)
    t_test_result = run_t_test(
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "embodied"],
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "static"]
    )
    effect_size = calculate_effect_size(
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "embodied"],
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "static"]
    )
    ci = calculate_confidence_interval(effect_size)
    collinearity = check_collinearity(gain_records)
    power = calculate_power(gain_records)
    inference = frame_inference(ancova_result)
    
    # Run sensitivity sweep
    sweep_results = run_sensitivity_sweep(gain_records, sweep_thresholds)
    robustness_warning = check_robustness_warning(sweep_results)

    # Aggregate results
    results = aggregate_results(
        ancova_f_statistic=ancova_result['f_statistic'],
        ancova_p_value=ancova_result['p_value'],
        t_statistic=t_test_result[0],
        p_value=t_test_result[1],
        effect_size_cohen_d=effect_size,
        confidence_interval=ci,
        inference_framing=inference,
        collinearity_diagnostics=collinearity,
        power_analysis=power,
        robustness_warning=robustness_warning,
        sensitivity_sweep=aggregate_results_for_report(sweep_results)
    )
    
    write_analysis_results(results, "data/processed/results.json")
    return results

def run_synthetic_generation(n: int, concept_definition: str, sweep_thresholds: List[float], seed: int) -> dict:
    """
    Generate synthetic data and run analysis.
    """
    set_seed(seed)
    logger.info(f"Generating synthetic data with n={n}, concept={concept_definition}")
    
    from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log
    
    # Generate mapping log first (required for synthetic mode)
    generate_mapping_log("data/synthetic/mapping_log.json", concept_definition)
    
    generator = SyntheticDataGenerator(seed=seed)
    records = generator.generate(n=n, concept_definition=concept_definition)
    
    if not records:
        logger.error("Failed to generate synthetic data.")
        return {}

    # Calculate gain scores
    gain_records = calculate_gain_scores(records)
    write_processed_data(gain_records, "data/synthetic/validated_synthetic.csv")

    # Run primary stats
    ancova_result = run_ancova(gain_records)
    t_test_result = run_t_test(
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "embodied"],
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "static"]
    )
    effect_size = calculate_effect_size(
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "embodied"],
        [r.post_test_score - r.pre_test_score for r in gain_records if r.instruction_type == "static"]
    )
    ci = calculate_confidence_interval(effect_size)
    collinearity = check_collinearity(gain_records)
    power = calculate_power(gain_records)
    inference = frame_inference(ancova_result)
    
    # Run sensitivity sweep
    sweep_results = run_sensitivity_sweep(gain_records, sweep_thresholds)
    robustness_warning = check_robustness_warning(sweep_results)

    # Aggregate results
    results = aggregate_results(
        ancova_f_statistic=ancova_result['f_statistic'],
        ancova_p_value=ancova_result['p_value'],
        t_statistic=t_test_result[0],
        p_value=t_test_result[1],
        effect_size_cohen_d=effect_size,
        confidence_interval=ci,
        inference_framing=inference,
        collinearity_diagnostics=collinearity,
        power_analysis=power,
        robustness_warning=robustness_warning,
        sensitivity_sweep=aggregate_results_for_report(sweep_results)
    )
    
    write_analysis_results(results, "data/synthetic/results.json")
    return results

def main():
    args = parse_args()
    setup_logging()
    
    thresholds = [float(x) for x in args.sweep_thresholds.split(",")]
    
    if args.mode == "secondary_analysis":
        if not args.input:
            logger.error("--input is required for secondary_analysis mode.")
            sys.exit(1)
        results = run_secondary_analysis(args.input, thresholds, args.seed)
    elif args.mode == "synthetic":
        if not args.concept_definition:
            logger.error("--concept_definition is required for synthetic mode.")
            sys.exit(1)
        results = run_synthetic_generation(args.n, args.concept_definition, thresholds, args.seed)
    
    logger.info("Analysis complete.")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    main()