import argparse
import sys
import json
import logging
import time
from pathlib import Path

# Absolute imports to ensure script execution works both as module and as script
from logging_config import setup_logging, write_skipped_record_jsonl
from synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from data_loader import (
    load_public_dataset,
    calculate_gain_scores,
    write_processed_data,
    handle_synthetic_fallback_failure,
    log_skipped_record,
)
from stats_engine import finalize_results
from sensitivity import run_sensitivity_sweep, check_robustness_warning, aggregate_results_for_report
from utils import set_seed
from config import INFERENTIAL_FRAMING_STRING

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Embodied Curriculum Learning Analysis Pipeline"
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["secondary_analysis", "synthetic"],
        help="Mode of operation: secondary_analysis (real data) or synthetic (generated data)",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to input CSV/JSON file (required for secondary_analysis)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output JSON file (optional, defaults based on mode)",
    )
    parser.add_argument(
        "--sweep_thresholds",
        type=str,
        help="Comma-separated list of thresholds for sensitivity analysis",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1000,
        help="Number of synthetic data points to generate (synthetic mode)",
    )
    parser.add_argument(
        "--mean_diff_embodied",
        type=float,
        default=0.5,
        help="Mean gain difference for embodied group (synthetic mode)",
    )
    parser.add_argument(
        "--mean_diff_static",
        type=float,
        default=0.0,
        help="Mean gain difference for static group (synthetic mode)",
    )
    # Aliases kept for backward compatibility
    parser.add_argument(
        "--n_participants",
        type=int,
        help="Alias for --n in synthetic mode",
    )
    parser.add_argument(
        "--effect_size",
        type=float,
        help="Target effect size (used for parameter derivation if provided)",
    )
    return parser.parse_args()

def parse_thresholds(thresholds_str):
    """
    Convert a comma‑separated string into a list of floats.
    Returns default thresholds if parsing fails or if the string is empty.
    """
    if not thresholds_str:
        return [0.01, 0.05, 0.10]
    try:
        return [float(x.strip()) for x in thresholds_str.split(",")]
    except ValueError:
        logger.error(f"Invalid threshold format: {thresholds_str}")
        return [0.01, 0.05, 0.10]

def _determine_output_path(args, default_name):
    """
    Helper to resolve the output path, creating parent directories as needed.
    """
    out_path = Path(args.output) if args.output else Path(default_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path

def run_synthetic_generation(args):
    """
    Generates synthetic data and immediately runs the full analysis pipeline
    on that data.  All required artefacts are written to their canonical locations:
    - data/synthetic/generated_data.csv
    - data/synthetic/mapping_log.json
    - data/processed/validated_fallback.csv (gain‑score CSV)
    - data/processed/results.json (full analysis)
    - data/processed/results_us2.json (US‑2 subset)
    """
    logger.info(
        f"Starting synthetic data generation with n={args.n}, seed={args.seed}"
    )
    set_seed(args.seed)

    n = args.n_participants if args.n_participants else args.n
    mean_diff_embodied = args.mean_diff_embodied
    mean_diff_static = args.mean_diff_static

    # 1. Generate synthetic dataset
    generator = SyntheticDataGenerator()
    df = generator.generate(
        n=n,
        seed=args.seed,
        mean_diff_embodied=mean_diff_embodied,
        mean_diff_static=mean_diff_static,
    )

    # 2. Write synthetic CSV
    synthetic_dir = Path("data/synthetic")
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    csv_path = synthetic_dir / "generated_data.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Synthetic data written to {csv_path}")

    # 3. Write mapping log (required by Constitution VI)
    mapping_log_path = synthetic_dir / "mapping_log.json"
    generate_mapping_log(
        n=n,
        seed=args.seed,
        mean_diff_embodied=mean_diff_embodied,
        mean_diff_static=mean_diff_static,
        output_path=str(mapping_log_path),
    )
    logger.info(f"Mapping log written to {mapping_log_path}")

    # 4. Run the analysis pipeline on the generated data
    # Re‑use the secondary‑analysis logic to avoid code duplication
    args.input = str(csv_path)
    args.mode = "secondary_analysis"
    if not args.output:
        args.output = "data/processed/results.json"
    return run_secondary_analysis(args)

def run_secondary_analysis(args):
    """
    Executes the full analysis pipeline on a real or synthetic dataset.
    The pipeline writes:
    - data/processed/validated_fallback.csv  (gain‑score CSV)
    - data/processed/results.json           (full report)
    - data/processed/results_us2.json       (US‑2 subset)
    - data/processed/perf_log.json          (performance log, written by perf_monitor)
    """
    logger.info(f"Starting secondary analysis on {args.input}")

    # 1. Load dataset (will fallback to synthetic if instruction_type missing)
    try:
        df = load_public_dataset(args.input)
    except Exception as exc:
        logger.error(f"Failed to load dataset: {exc}")
        sys.exit(1)

    # 2. Calculate gain scores (adds 'gain_score' column)
    try:
        df = calculate_gain_scores(df)
    except Exception as exc:
        logger.error(f"Gain‑score calculation failed: {exc}")
        sys.exit(1)

    # 3. Persist the processed dataframe (validated_fallback.csv)
    fallback_path = Path("data/processed/validated_fallback.csv")
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(fallback_path, index=False)
    logger.info(f"Validated fallback CSV written to {fallback_path}")

    # 4. Sensitivity sweep (if enough participants)
    thresholds = parse_thresholds(args.sweep_thresholds)
    if len(df) >= 30:
        logger.info(f"Running sensitivity sweep with thresholds: {thresholds}")
        sweep_results = run_sensitivity_sweep(df, thresholds)
        robustness_warning = check_robustness_warning(sweep_results)
    else:
        logger.warning(
            f"Insufficient data (N={len(df)}) for sensitivity sweep – skipping."
        )
        sweep_results = [
            {"threshold_value": t, "insufficient_data": True, "message": "insufficient data for robustness check"}
            for t in thresholds
        ]
        robustness_warning = False

    # 5. Run statistical engine and aggregate results
    try:
        final_results = finalize_results(
            df=df,
            sensitivity_results=sweep_results,
            robustness_warning=robustness_warning,
        )
    except Exception as exc:
        logger.error(f"Statistical analysis failed: {exc}")
        sys.exit(1)

    # 6. Write the full results JSON
    results_path = _determine_output_path(args, "data/processed/results.json")
    with results_path.open("w") as f:
        json.dump(final_results, f, indent=2)
    logger.info(f"Full results written to {results_path}")

    # 7. Write US‑2 subset (required by several downstream tasks)
    us2_path = Path("data/processed/results_us2.json")
    us2_keys = [
        "t_statistic",
        "p_value",
        "corrected_p_value",
        "effect_size_cohen_d",
        "confidence_interval",
        "inference_framing",
        "ancova_results",
        "power_analysis",
        "collinearity_diagnostics",
    ]
    us2_data = {k: v for k, v in final_results.items() if k in us2_keys}
    with us2_path.open("w") as f:
        json.dump(us2_data, f, indent=2)
    logger.info(f"US‑2 results written to {us2_path}")

    return 0

def main():
    args = parse_args()
    setup_logging()

    if args.mode == "synthetic":
        return run_synthetic_generation(args)
    elif args.mode == "secondary_analysis":
        if not args.input:
            logger.error("Input file required for secondary_analysis mode")
            sys.exit(1)
        return run_secondary_analysis(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main() or 0)