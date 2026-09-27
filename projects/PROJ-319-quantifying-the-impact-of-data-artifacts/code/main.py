"""
Main CLI entry point for the llmXive automated science pipeline.
Orchestrates the full pipeline: Generate -> Inject Artifacts -> Measure -> Regress -> Validate.
"""
import argparse
import logging
import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import from local modules using the established API surface
from code.config import get_project_root, get_config_summary, DEFAULT_SYNTHETIC_COUNT, DEFAULT_SEED
from code.io.writer import generate_run_manifest, write_run_manifest_for_pipeline
from code.io.loader import load_fits_image, validate_fits_headers
from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
from code.synthetic.artifacts import run_noise_sweep, run_saturation_sweep
from code.metrics.ellipticity import calculate_ellipticity
from code.metrics.asymmetry import calculate_asymmetry
from code.analysis.statistics import run_noise_regression, run_saturation_regression
from code.analysis.regression import fit_calibration_models
from code.analysis.validation import apply_corrections, validate_residuals
from code.analysis.power_analysis import generate_power_report

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def setup_directories(root: Path) -> None:
    """Ensure all required directories exist."""
    dirs = [
        "data/raw", "data/synthetic", "data/processed", "data/validation",
        "code/synthetic", "code/metrics", "code/analysis", "code/io",
        "logs", "docs/reports"
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

def validate_pipeline_state(root: Path) -> None:
    """
    Validate that required artifacts exist before proceeding.
    Raises FileNotFoundError if dependencies are missing.
    """
    # Check for ground truth metadata (T006c)
    gt_path = root / "data" / "synthetic" / "gt_metadata.json"
    if not gt_path.exists():
        raise FileNotFoundError(
            f"Missing ground truth metadata: {gt_path}. "
            "Ensure T006 (Synthetic Generation) has completed successfully."
        )

    # Check for processed data if running calibration (US3)
    # This is a soft check; if missing, we assume we need to run US1/US2 first
    agg_path = root / "data" / "processed" / "aggregated_bias.csv"
    # If running --run-all, we will generate these, so no error here unless explicitly required

def generate_data(root: Path, n_images: int = DEFAULT_SYNTHETIC_COUNT, seed: int = DEFAULT_SEED) -> None:
    """Generate synthetic planetary nebulae and ground truth metadata."""
    logger = logging.getLogger("pipeline")
    logger.info(f"Generating {n_images} synthetic nebulae with seed {seed}...")

    synth_dir = root / "data" / "synthetic"
    synth_dir.mkdir(parents=True, exist_ok=True)

    # Generate images and metadata
    generate_gt_metadata(n_images, seed, synth_dir)
    logger.info("Synthetic data generation complete.")

def process_artifacts(root: Path) -> None:
    """Process synthetic data by injecting artifacts and measuring metrics."""
    logger = logging.getLogger("pipeline")
    logger.info("Running artifact injection and metric measurement sweeps...")

    # Run Noise Sweep (US1)
    logger.info("Executing Noise Sweep (US1)...")
    run_noise_sweep(root)

    # Run Saturation Sweep (US2)
    logger.info("Executing Saturation Sweep (US2)...")
    run_saturation_sweep(root)

    # Aggregate data for US3
    logger.info("Aggregating bias data...")
    # The aggregation logic is typically part of the statistics or validation step,
    # but we ensure the files exist for the regression step.
    # run_noise_regression and run_saturation_regression will produce the stats files.

def run_us1_pipeline(root: Path) -> None:
    """Execute User Story 1: Noise -> Ellipticity Bias."""
    logger = logging.getLogger("pipeline")
    logger.info("Running US1 Pipeline...")
    # The run_noise_sweep in process_artifacts already does the heavy lifting.
    # We call the regression analysis here to finalize stats.
    run_noise_regression(root)

def run_us2_pipeline(root: Path) -> None:
    """Execute User Story 2: Saturation -> Asymmetry Bias."""
    logger = logging.getLogger("pipeline")
    logger.info("Running US2 Pipeline...")
    run_saturation_regression(root)

def run_us3_pipeline(root: Path) -> None:
    """Execute User Story 3: Calibration and Validation."""
    logger = logging.getLogger("pipeline")
    logger.info("Running US3 Pipeline (Calibration & Validation)...")

    # Aggregate data (if not already done by previous steps)
    # The statistics steps produce noise_stats.csv and saturation_stats.csv
    # We need to fit models on these.
    fit_calibration_models(root)

    # Validate residuals
    validate_residuals(root)

    # Power Analysis
    generate_power_report(root)

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument("--run-all", action="store_true", help="Run the full pipeline (Generate -> Process -> Calibrate -> Validate)")
    parser.add_argument("--mode", type=str, choices=["generate", "process", "calibrate", "validate", "verify"],
                        help="Run a specific mode of the pipeline")
    parser.add_argument("--n-images", type=int, default=DEFAULT_SYNTHETIC_COUNT, help="Number of synthetic images to generate")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--output", type=str, help="Output directory (optional)")

    args = parser.parse_args()
    root = get_project_root()
    setup_directories(root)

    # Setup logging
    log_file = root / "logs" / "research.log"
    logger = setup_logging(log_file)
    logger.info("Pipeline started.")

    # Generate Run Manifest (T053)
    write_run_manifest_for_pipeline(root)

    if args.run_all:
        logger.info("Executing full pipeline (--run-all)...")
        try:
            validate_pipeline_state(root)
        except FileNotFoundError as e:
            logger.error(str(e))
            # If state is invalid, we might need to generate first
            logger.info("Attempting to generate data first...")
            generate_data(root, args.n_images, args.seed)

        process_artifacts(root)
        run_us1_pipeline(root)
        run_us2_pipeline(root)
        run_us3_pipeline(root)
        logger.info("Full pipeline completed successfully.")
    elif args.mode:
        if args.mode == "generate":
            generate_data(root, args.n_images, args.seed)
        elif args.mode == "process":
            process_artifacts(root)
        elif args.mode == "calibrate":
            run_us3_pipeline(root)
        elif args.mode == "validate":
            validate_residuals(root)
        elif args.mode == "verify":
            logger.info("Verification mode: Checking artifacts...")
            # Simple check
            required = [
                root / "data" / "synthetic" / "gt_metadata.json",
                root / "data" / "processed" / "noise_sweep_data.csv",
                root / "data" / "processed" / "saturation_sweep.csv",
                root / "data" / "processed" / "noise_stats.csv",
                root / "data" / "processed" / "saturation_stats.csv",
                root / "data" / "processed" / "calibration_functions.json",
                root / "data" / "processed" / "run_manifest.json"
            ]
            missing = [f for f in required if not f.exists()]
            if missing:
                logger.error(f"Missing artifacts: {missing}")
                sys.exit(1)
            else:
                logger.info("All required artifacts present.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
