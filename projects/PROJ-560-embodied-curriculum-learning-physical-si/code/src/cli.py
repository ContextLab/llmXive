import argparse
import sys
import json
import os
import logging
import time
from pathlib import Path

from .logging_config import setup_logging
from .utils import set_seed
from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from .data_loader import load_public_dataset_with_fallback, calculate_gain_scores, write_processed_data
from .stats_engine import (
    run_t_test,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    check_collinearity,
    calculate_power,
    frame_inference,
    aggregate_results,
    write_partial_results,
    finalize_results
)
from .sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report

def parse_args():
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument("--mode", type=str, required=True, choices=["secondary_analysis", "synthetic"],
                        help="Mode of operation: 'secondary_analysis' for public data, 'synthetic' for generated data")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to input public dataset CSV (required for secondary_analysis mode)")
    parser.add_argument("--output", type=str, default="data/processed/analysis_result.json",
                        help="Path for the final output JSON report")
    parser.add_argument("--sweep_thresholds", type=str, default="0.01,0.05,0.10",
                        help="Comma-separated list of thresholds for sensitivity analysis (default: 0.01,0.05,0.10)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--n", type=int, default=1000,
                        help="Number of synthetic samples to generate (for synthetic mode)")
    parser.add_argument("--mean_diff_embodied", type=float, default=0.5,
                        help="Mean difference for embodied group in synthetic generation")
    parser.add_argument("--mean_diff_static", type=float, default=0.0,
                        help="Mean difference for static group in synthetic generation")
    parser.add_argument("--n_participants", type=int, default=None,
                        help="Deprecated alias for --n, kept for backward compatibility")
    parser.add_argument("--effect_size", type=float, default=0.5,
                        help="Deprecated: kept for backward compatibility, not used in current generator logic")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="Base output directory for intermediate files (defaults to data/processed or data/synthetic)")

    args = parser.parse_args()

    # Handle deprecated alias
    if args.n_participants is not None:
        args.n = args.n_participants

    return args

def run_synthetic_generation(args):
    """
    Generate synthetic data and run the full analysis pipeline.
    Produces:
      - data/synthetic/generated_data.csv
      - data/synthetic/mapping_log.json
      - data/processed/results.json (final report)
      - data/processed/results_us2.json (intermediate US2 report)
      - data/processed/validated_fallback.csv (intermediate processed data)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting synthetic generation with n={args.n}, seed={args.seed}")

    # Ensure output directories exist
    synth_dir = Path("data/synthetic")
    processed_dir = Path("data/processed")
    synth_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Set seed
    set_seed(args.seed)

    # Generate data
    generator = SyntheticDataGenerator()
    synthetic_data_path = synth_dir / "generated_data.csv"
    mapping_log_path = synth_dir / "mapping_log.json"

    logger.info(f"Generating {args.n} synthetic samples...")
    df = generator.generate(n=args.n, seed=args.seed,
                            mean_diff_embodied=args.mean_diff_embodied,
                            mean_diff_static=args.mean_diff_static)
    df.to_csv(synthetic_data_path, index=False)
    logger.info(f"Synthetic data written to {synthetic_data_path}")

    # Generate mapping log
    mapping_log = generate_mapping_log(n=args.n, seed=args.seed)
    with open(mapping_log_path, 'w') as f:
        json.dump(mapping_log, f, indent=2)
    logger.info(f"Mapping log written to {mapping_log_path}")

    # Process data (calculate gain scores)
    logger.info("Calculating gain scores...")
    df_with_gain = calculate_gain_scores(df)
    validated_path = processed_dir / "validated_fallback.csv"
    write_processed_data(df_with_gain, validated_path)
    logger.info(f"Validated data written to {validated_path}")

    # Run statistical analysis (US2)
    logger.info("Running statistical analysis (US2)...")
    t_stat, p_val = run_t_test(df_with_gain, group_col="instruction_type", gain_col="gain_score")
    cohens_d = calculate_effect_size(df_with_gain, group_col="instruction_type", gain_col="gain_score")
    ci = calculate_confidence_interval(df_with_gain, group_col="instruction_type", gain_col="gain_score")
    bonf_alpha = apply_bonferroni_correction(0.05, 1) # Assuming 1 concept for now
    collin_diag = check_collinearity(df_with_gain)
    power = calculate_power(t_stat, p_val, len(df_with_gain))
    framing = frame_inference()

    # Aggregate US2 results
    us2_results = aggregate_results(t_stat, p_val, cohens_d, ci, bonf_alpha, collin_diag, power, framing)
    write_partial_results(us2_results, processed_dir / "results_us2.json")
    logger.info(f"US2 results written to {processed_dir / 'results_us2.json'}")

    # Run sensitivity analysis (US3) if thresholds provided
    thresholds = [float(x) for x in args.sweep_thresholds.split(',')]
    sweep_results = run_sensitivity_sweep(df_with_gain, thresholds, group_col="instruction_type", gain_col="gain_score")
    robust_flag = check_robustness_warning(sweep_results)

    # Finalize results (merge US2 and US3)
    final_results = finalize_results(us2_results, sweep_results, robust_flag)
    final_output_path = Path(args.output) if args.output else processed_dir / "results.json"
    with open(final_output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"Final results written to {final_output_path}")

    return 0

def run_secondary_analysis(args):
    """
    Load public dataset (with fallback if needed) and run analysis.
    Produces:
      - data/processed/validated_fallback.csv (if fallback used)
      - data/processed/results.json
      - data/processed/results_us2.json
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting secondary analysis...")

    # Ensure output directories
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load data (with fallback logic)
    df = load_public_dataset_with_fallback(
        input_path=args.input,
        seed=args.seed,
        n=args.n,
        mean_diff_embodied=args.mean_diff_embodied,
        mean_diff_static=args.mean_diff_static
    )
    if df is None:
        logger.error("Data loading failed and fallback generation failed.")
        return 1

    # Calculate gain scores
    logger.info("Calculating gain scores...")
    df_with_gain = calculate_gain_scores(df)
    validated_path = processed_dir / "validated_fallback.csv"
    write_processed_data(df_with_gain, validated_path)
    logger.info(f"Validated data written to {validated_path}")

    # Run statistical analysis (US2)
    logger.info("Running statistical analysis (US2)...")
    t_stat, p_val = run_t_test(df_with_gain, group_col="instruction_type", gain_col="gain_score")
    cohens_d = calculate_effect_size(df_with_gain, group_col="instruction_type", gain_col="gain_score")
    ci = calculate_confidence_interval(df_with_gain, group_col="instruction_type", gain_col="gain_score")
    bonf_alpha = apply_bonferroni_correction(0.05, 1)
    collin_diag = check_collinearity(df_with_gain)
    power = calculate_power(t_stat, p_val, len(df_with_gain))
    framing = frame_inference()

    us2_results = aggregate_results(t_stat, p_val, cohens_d, ci, bonf_alpha, collin_diag, power, framing)
    write_partial_results(us2_results, processed_dir / "results_us2.json")
    logger.info(f"US2 results written to {processed_dir / 'results_us2.json'}")

    # Run sensitivity analysis (US3)
    thresholds = [float(x) for x in args.sweep_thresholds.split(',')]
    sweep_results = run_sensitivity_sweep(df_with_gain, thresholds, group_col="instruction_type", gain_col="gain_score")
    robust_flag = check_robustness_warning(sweep_results)

    # Finalize results
    final_results = finalize_results(us2_results, sweep_results, robust_flag)
    final_output_path = Path(args.output) if args.output else processed_dir / "results.json"
    with open(final_output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"Final results written to {final_output_path}")

    return 0

def run_analysis_pipeline(args):
    """
    Main entry point to dispatch based on mode.
    """
    if args.mode == "synthetic":
        return run_synthetic_generation(args)
    elif args.mode == "secondary_analysis":
        return run_secondary_analysis(args)
    else:
        logging.error(f"Unknown mode: {args.mode}")
        return 1

def main():
    args = parse_args()
    setup_logging()
    logger = logging.getLogger(__name__)

    start_time = time.time()
    try:
        exit_code = run_analysis_pipeline(args)
    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        exit_code = 1

    duration = time.time() - start_time
    if args.mode == "synthetic" and exit_code == 0:
        # Write performance log for synthetic mode as required by T039
        perf_log_path = Path("data/processed/perf_log.json")
        perf_log_path.parent.mkdir(parents=True, exist_ok=True)
        perf_log = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_records": args.n,
            "duration_seconds": duration,
            "command_executed": " ".join(sys.argv)
        }
        with open(perf_log_path, 'w') as f:
            json.dump(perf_log, f, indent=2)
        logger.info(f"Performance log written to {perf_log_path}")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()