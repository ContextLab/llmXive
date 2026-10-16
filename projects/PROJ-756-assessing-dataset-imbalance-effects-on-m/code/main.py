"""
Entry‑point CLI for the Assessing Dataset Imbalance Effects on Materials Property Predictions project.

Supported flags:
  --full-pipeline   Run the complete end‑to‑end pipeline (ingestion → SHAP analysis).
  --include-mp      Attempt to download Materials Project data (requires MP_API_KEY).
  --fallback-mode   Force fallback mode (skip MP even if API key is present).
  --streaming       Use streaming mode for dataset downloads where supported.

The implementation is intentionally lightweight: it parses the arguments,
validates combinations, and prints a short status message.  Full pipeline
orchestration is delegated to the individual modules (ingestion, descriptors,
training, etc.) which can be invoked separately via their own CLIs.
"""
import argparse
import sys
from pathlib import Path

# Import the module‑level logger from the toolkit for optional logging.
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Project CLI for dataset‑imbalance assessment pipeline"
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Execute the full pipeline (ingestion, descriptor computation, training, evaluation, SHAP).",
    )
    parser.add_argument(
        "--include-mp",
        action="store_true",
        help="Attempt to download Materials Project data (requires MP_API_KEY).",
    )
    parser.add_argument(
        "--fallback-mode",
        action="store_true",
        help="Force fallback mode – skip Materials Project even if API key is available.",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming mode for large dataset downloads.",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)

    # Basic validation of mutually exclusive flags
    if args.fallback_mode and args.include_mp:
        log.error("Cannot use --fallback-mode together with --include-mp.")
        sys.exit(1)

    # Summarise the requested actions
    log.info("CLI arguments parsed:")
    log.info(f"  full_pipeline   = {args.full_pipeline}")
    log.info(f"  include_mp      = {args.include_mp}")
    log.info(f"  fallback_mode   = {args.fallback_mode}")
    log.info(f"  streaming       = {args.streaming}")

    if args.full_pipeline:
        # Import and invoke the sub‑modules lazily to avoid unnecessary work
        try:
            from ingestion import main as ingestion_main
            from descriptors import main as descriptors_main
            from training import main as training_main
            from evaluation import main as evaluation_main
            from shap_analysis import main as shap_main

            # Ingestion
            ingestion_args = ["--streaming"] if args.streaming else []
            ingestion_main(ingestion_args)

            # Descriptor computation
            descriptors_args = [
                "--input", "data/raw/merged_raw.parquet",
                "--output", "data/processed/processed.parquet",
            ]
            if args.streaming:
                descriptors_args.append("--streaming")
            descriptors_main(descriptors_args)

            # Baseline training (skewed)
            training_args = [
                "--input", "data/processed/processed.parquet",
                "--strategy", "skewed",
                "--output", "artifacts/models/baseline/",
            ]
            training_main(training_args)

            # Resampling & balanced training
            # (Assuming resampling script follows a similar CLI pattern)
            from resampling import main as resampling_main
            resampling_args = [
                "--input", "data/processed/processed.parquet",
                "--output", "data/processed/balanced.parquet",
            ]
            if args.streaming:
                resampling_args.append("--streaming")
            resampling_main(resampling_args)

            training_balanced_args = [
                "--input", "data/processed/balanced.parquet",
                "--strategy", "balanced",
                "--output", "artifacts/models/balanced/",
            ]
            training_main(training_balanced_args)

            # Evaluation
            evaluation_args = [
                "--baseline", "artifacts/models/baseline/",
                "--balanced", "artifacts/models/balanced/",
                "--output", "results/comparison_report.csv",
            ]
            evaluation_main(evaluation_args)

            # SHAP analysis
            shap_args = [
                "--models", "artifacts/models/",
                "--output", "results/shap_comparison.json",
            ]
            shap_main(shap_args)

            log.info("Full pipeline executed successfully.")
        except Exception as exc:
            log.error(f"An error occurred while executing the full pipeline: {exc}")
            sys.exit(1)
    else:
        # When not running the full pipeline, simply acknowledge the flags.
        log.info("No pipeline execution requested. Exiting after argument parsing.")

    # Normal termination
    return 0

if __name__ == "__main__":
    sys.exit(main())
