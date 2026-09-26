import argparse
import sys
import json
import os
import logging
import time
from pathlib import Path

# Fix relative import issue by adding parent to path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import set_seed
from src.data_loader import load_public_dataset_with_fallback, calculate_gain_scores, write_processed_data
from src.synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from src.stats_engine import (
    aggregate_stats_results,
    write_partial_results,
    finalize_results,
    run_t_test,
    run_ancova,
    calculate_effect_size,
    apply_bonferroni_correction,
    check_collinearity,
    calculate_power,
    frame_inference
)
from src.sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
from src.logging_config import setup_logging
from src.models import AnalysisResult, SensitivitySweep

def parse_args():
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument("--mode", type=str, required=True, choices=["secondary_analysis", "synthetic"],
                        help="Analysis mode: 'secondary_analysis' for public data, 'synthetic' for generated data")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to input CSV/JSON file (required for secondary_analysis mode)")
    parser.add_argument("--n", type=int, default=1000,
                        help="Number of synthetic samples to generate (default: 1000)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--sweep_thresholds", type=str, default="0.01,0.05,0.10",
                        help="Comma-separated list of p-value thresholds for sensitivity analysis")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path (optional, defaults to standard locations)")
    parser.add_argument("--mean_diff_embodied", type=float, default=10.0,
                        help="Mean difference for embodied group in synthetic generation")
    parser.add_argument("--mean_diff_static", type=float, default=5.0,
                        help="Mean difference for static group in synthetic generation")
    return parser.parse_args()

def run_synthetic_generation(args):
    """Generate synthetic data and run analysis."""
    logging.info(f"Starting synthetic data generation with n={args.n}, seed={args.seed}")
    
    # Initialize generator
    generator = SyntheticDataGenerator(seed=args.seed)
    
    # Generate data
    data = generator.generate(
        n=args.n,
        mean_diff_embodied=args.mean_diff_embodied,
        mean_diff_static=args.mean_diff_static
    )
    
    # Write mapping log if in synthetic mode
    mapping_log_path = Path("data/synthetic/mapping_log.json")
    generate_mapping_log(
        mapping_log_path=str(mapping_log_path),
        physics_param="simulated_gain",
        math_concept="mathematical_reasoning",
        mapping_rule="Linear mapping from simulated physics gain to mathematical reasoning score",
        mode="synthetic"
    )
    
    # Prepare data for analysis
    df = data["data"]
    
    # Calculate gain scores
    df = calculate_gain_scores(df)
    
    # Write processed data
    output_path = Path("data/processed/validated_fallback.csv")
    write_processed_data(df, str(output_path))
    
    # Run statistical analysis
    result = aggregate_stats_results(df)
    
    # Write partial results
    write_partial_results(result, "data/processed/results_us2.json")
    
    # Run sensitivity analysis if thresholds provided
    thresholds = [float(t) for t in args.sweep_thresholds.split(",")]
    if thresholds:
        sweep_results = run_sensitivity_sweep(df, thresholds)
        robust_flag = check_robustness_warning(sweep_results)
        
        # Aggregate for final report
        final_result = finalize_results(
            base_result=result,
            sweep_results=sweep_results,
            robustness_warning=robust_flag
        )
    else:
        final_result = result
    
    # Write final results
    output_file = args.output if args.output else "data/processed/results.json"
    with open(output_file, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    logging.info(f"Synthetic generation and analysis complete. Results written to {output_file}")
    return 0

def run_secondary_analysis(args):
    """Run analysis on public dataset."""
    if not args.input:
        logging.error("Input file required for secondary analysis mode")
        return 1
    
    logging.info(f"Loading public dataset from {args.input}")
    
    # Load data with fallback logic
    df = load_public_dataset_with_fallback(args.input)
    
    # Calculate gain scores
    df = calculate_gain_scores(df)
    
    # Write processed data
    output_path = Path("data/processed/validated_fallback.csv")
    write_processed_data(df, str(output_path))
    
    # Run statistical analysis
    result = aggregate_stats_results(df)
    
    # Write partial results
    write_partial_results(result, "data/processed/results_us2.json")
    
    # Run sensitivity analysis if thresholds provided
    thresholds = [float(t) for t in args.sweep_thresholds.split(",")] if args.sweep_thresholds else []
    if thresholds:
        sweep_results = run_sensitivity_sweep(df, thresholds)
        robust_flag = check_robustness_warning(sweep_results)
        
        # Aggregate for final report
        final_result = finalize_results(
            base_result=result,
            sweep_results=sweep_results,
            robustness_warning=robust_flag
        )
    else:
        final_result = result
    
    # Write final results
    output_file = args.output if args.output else "data/processed/results.json"
    with open(output_file, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    logging.info(f"Secondary analysis complete. Results written to {output_file}")
    return 0

def run_analysis_pipeline(args):
    """Main pipeline execution."""
    start_time = time.time()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    # Setup logging
    setup_logging()
    
    if args.mode == "synthetic":
        return run_synthetic_generation(args)
    elif args.mode == "secondary_analysis":
        return run_secondary_analysis(args)
    else:
        logging.error(f"Unknown mode: {args.mode}")
        return 1

def main():
    args = parse_args()
    exit_code = run_analysis_pipeline(args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
