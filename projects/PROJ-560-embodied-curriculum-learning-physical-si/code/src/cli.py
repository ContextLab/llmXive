import argparse
import sys
import json
import os
import logging
import time
from pathlib import Path

# Add parent directory to path to allow relative imports if run as script
# but rely on installed package structure for standard execution
try:
    from .logging_config import setup_logging
    from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log, parse_synthetic_params
    from .data_loader import (
        load_public_dataset,
        calculate_gain_scores,
        write_processed_data,
        handle_synthetic_fallback_failure,
        log_skipped_record
    )
    from .stats_engine import (
        finalize_results
    )
    from .sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
    from .utils import set_seed
    from .config import INFERENTIAL_FRAMING_STRING
except ImportError:
    # Fallback for direct execution (python -m src.cli or python src/cli.py)
    from logging_config import setup_logging
    from synthetic_gen import SyntheticDataGenerator, generate_mapping_log, parse_synthetic_params
    from data_loader import (
        load_public_dataset,
        calculate_gain_scores,
        write_processed_data,
        handle_synthetic_fallback_failure,
        log_skipped_record
    )
    from stats_engine import (
        finalize_results
    )
    from sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
    from utils import set_seed
    from config import INFERENTIAL_FRAMING_STRING

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument('--mode', type=str, required=True, choices=['secondary_analysis', 'synthetic'],
                        help='Mode of operation: secondary_analysis (real data) or synthetic (generated data)')
    parser.add_argument('--input', type=str, help='Path to input CSV/JSON file (required for secondary_analysis)')
    parser.add_argument('--output', type=str, help='Path to output file (optional, defaults based on mode)')
    parser.add_argument('--sweep_thresholds', type=str, help='Comma-separated list of thresholds for sensitivity analysis')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--n', type=int, default=1000, help='Number of synthetic data points to generate')
    parser.add_argument('--mean_diff_embodied', type=float, default=0.5, help='Mean difference for embodied group')
    parser.add_argument('--mean_diff_static', type=float, default=0.0, help='Mean difference for static group')
    parser.add_argument('--n_participants', type=int, help='Alias for --n in synthetic mode')
    parser.add_argument('--effect_size', type=float, help='Target effect size (used for parameter derivation if provided)')
    return parser.parse_args()

def parse_thresholds(thresholds_str):
    if not thresholds_str:
        return [0.01, 0.05, 0.10]
    try:
        return [float(x.strip()) for x in thresholds_str.split(',')]
    except ValueError:
        logger.error(f"Invalid threshold format: {thresholds_str}")
        return [0.01, 0.05, 0.10]

def run_synthetic_generation(args):
    """
    Generates synthetic data and runs the full analysis pipeline on it.
    Writes output to data/synthetic/ and data/processed/ as required.
    """
    logger.info(f"Starting synthetic data generation with n={args.n}, seed={args.seed}")
    set_seed(args.seed)

    n = args.n_participants if args.n_participants else args.n
    mean_diff_embodied = args.mean_diff_embodied
    mean_diff_static = args.mean_diff_static

    # Determine output paths
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "generated_data.csv"
    mapping_log_path = output_dir / "mapping_log.json"

    # Generate synthetic data
    generator = SyntheticDataGenerator()
    df = generator.generate(
        n=n,
        seed=args.seed,
        mean_diff_embodied=mean_diff_embodied,
        mean_diff_static=mean_diff_static
    )

    # Write CSV
    df.to_csv(csv_path, index=False)
    logger.info(f"Synthetic data written to {csv_path}")

    # Generate mapping log (required for synthetic mode per T014b)
    mapping_log = generate_mapping_log(
        n=n,
        seed=args.seed,
        mean_diff_embodied=mean_diff_embodied,
        mean_diff_static=mean_diff_static,
        output_path=str(mapping_log_path)
    )
    logger.info(f"Mapping log written to {mapping_log_path}")

    # Now run analysis on the generated data as if it were real
    # We treat the generated CSV as the input for the analysis pipeline
    args.input = str(csv_path)
    args.mode = 'secondary_analysis' # Switch to analysis mode to reuse logic
    
    # Determine output for analysis results
    if not args.output:
        args.output = "data/processed/results.json"
    
    # Run the analysis logic
    return run_secondary_analysis(args)

def run_secondary_analysis(args):
    """
    Runs the full analysis pipeline on a dataset (real or synthetic).
    Handles data loading, gain score calculation, statistical testing,
    sensitivity analysis, and result aggregation.
    """
    logger.info(f"Starting secondary analysis on {args.input}")

    # 1. Load Data
    try:
        df = load_public_dataset(args.input)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # 2. Calculate Gain Scores
    try:
        df = calculate_gain_scores(df)
    except Exception as e:
        logger.error(f"Failed to calculate gain scores: {e}")
        sys.exit(1)

    # 3. Determine Output Path
    output_path = args.output if args.output else "data/processed/results.json"
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4. Run Sensitivity Sweep (if thresholds provided or default)
    thresholds = parse_thresholds(args.sweep_thresholds)
    sensitivity_results = []
    robustness_warning = False

    if len(df) >= 30:
        logger.info(f"Running sensitivity sweep with thresholds: {thresholds}")
        sweep_data = run_sensitivity_sweep(df, thresholds)
        sensitivity_results = sweep_data.get('results', [])
        robustness_warning = check_robustness_warning(sensitivity_results)
        logger.info(f"Sensitivity sweep complete. Robustness warning: {robustness_warning}")
    else:
        logger.warning(f"Insufficient data (N={len(df)}) for robust sensitivity sweep.")
        sensitivity_results = [{'threshold_value': t, 'insufficient_data': True} for t in thresholds]

    # 5. Run Statistical Analysis and Aggregate
    # We need to call the stats engine to get the full result dict
    # The stats_engine.finalize_results expects the data and the sensitivity results
    try:
        final_results = finalize_results(
            df=df,
            sensitivity_results=sensitivity_results,
            robustness_warning=robustness_warning
        )
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        sys.exit(1)

    # 6. Write Results
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"Final results written to {output_path}")

    # 7. Write US2 partial results if requested or for validation
    # Per T026b, we should write results_us2.json. 
    # We can extract the US2 specific part or write the full result if it matches.
    # Assuming finalize_results returns the full structure including US2 data.
    # If the structure is flat, we might need to split it. 
    # For now, we assume finalize_results produces the full report which includes US2 keys.
    # If a specific US2 file is strictly required separate from the main report, 
    # we write a subset here.
    us2_path = "data/processed/results_us2.json"
    # Extract keys relevant to US2 (t-test, ancova, effect size, etc.)
    us2_keys = [
        't_statistic', 'p_value', 'corrected_p_value', 'effect_size_cohen_d',
        'confidence_interval', 'inference_framing', 'ancova_results',
        'power_analysis', 'collinearity_diagnostics'
    ]
    us2_data = {k: v for k, v in final_results.items() if k in us2_keys}
    with open(us2_path, 'w') as f:
        json.dump(us2_data, f, indent=2)
    logger.info(f"US2 results written to {us2_path}")

    return 0

def main():
    args = parse_args()
    setup_logging()

    if args.mode == 'synthetic':
        return run_synthetic_generation(args)
    elif args.mode == 'secondary_analysis':
        if not args.input:
            logger.error("Input file required for secondary_analysis mode")
            sys.exit(1)
        return run_secondary_analysis(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main() or 0)