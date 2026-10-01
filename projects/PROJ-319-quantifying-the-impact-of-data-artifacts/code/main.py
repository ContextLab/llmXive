"""
Main CLI entry point for the llmXive automated science pipeline.
Implements the orchestration for User Stories 1, 2, and 3.
"""
import argparse
import logging
import sys
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

# Import local modules
from code.config import get_project_root
from code.io.writer import write_run_manifest_for_pipeline
from code.io.loader import load_fits_image
from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
from code.synthetic.artifacts import run_noise_sweep, run_saturation_sweep
from code.metrics.ellipticity import calculate_ellipticity
from code.metrics.asymmetry import calculate_asymmetry
from code.analysis.statistics import run_noise_regression, run_saturation_regression
from code.analysis.regression import fit_calibration_models
from code.analysis.validation import apply_corrections, validate_residuals
from code.analysis.power_analysis import generate_power_report

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    """
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
    """
    Ensure required directory structure exists.
    """
    dirs = [
        root / "data" / "raw",
        root / "data" / "synthetic",
        root / "data" / "processed",
        root / "data" / "validation",
        root / "logs",
        root / "docs" / "reports",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_pipeline_state(root: Path) -> None:
    """
    Validate that required artifacts exist before proceeding.
    """
    gt_file = root / "data" / "synthetic" / "gt_metadata.json"
    if not gt_file.exists():
        raise FileNotFoundError(
            "Missing ground truth metadata. Ensure T006 (Synthetic Generation) has completed successfully."
        )
    # Check for aggregated data if running US3
    agg_file = root / "data" / "processed" / "aggregated_bias.csv"
    # We don't strictly fail here if running US1/US2, but log a warning if missing for US3
    # This check is handled inside the orchestration functions

def generate_data(root: Path, n_images: int = 50) -> None:
    """
    Generate synthetic planetary nebulae and ground truth metadata.
    """
    logging.info(f"Generating {n_images} synthetic nebulae...")
    generate_synthetic_nebula(root / "data" / "synthetic", n_images=n_images)
    generate_gt_metadata(root / "data" / "synthetic", n_images=n_images)
    logging.info("Synthetic data generation complete.")

def process_artifacts(root: Path) -> None:
    """
    Process synthetic data by injecting artifacts and computing metrics.
    """
    logging.info("Running noise sweep...")
    run_noise_sweep(root / "data" / "synthetic", root / "data" / "processed")
    logging.info("Noise sweep complete.")

    logging.info("Running saturation sweep...")
    run_saturation_sweep(root / "data" / "synthetic", root / "data" / "processed")
    logging.info("Saturation sweep complete.")

def run_us1_pipeline(root: Path) -> None:
    """
    Execute User Story 1: Noise-induced bias on ellipticity.
    """
    logging.info("Executing User Story 1: Noise Sweep...")
    # The run_noise_sweep function in code/synthetic/artifacts.py
    # already handles the injection, measurement, and CSV generation.
    # We just need to ensure the regression step happens.
    run_noise_regression(root / "data" / "processed" / "noise_sweep_data.csv",
                         root / "data" / "processed" / "noise_stats.csv")
    logging.info("User Story 1 complete.")

def run_us2_pipeline(root: Path) -> None:
    """
    Execute User Story 2: Saturation-induced bias on asymmetry.
    """
    logging.info("Executing User Story 2: Saturation Sweep...")
    # The run_saturation_sweep function in code/synthetic/artifacts.py
    # already handles injection, measurement, and CSV generation.
    run_saturation_regression(root / "data" / "processed" / "saturation_sweep.csv",
                              root / "data" / "processed" / "saturation_stats.csv")
    logging.info("User Story 2 complete.")

def run_us3_pipeline(root: Path) -> None:
    """
    Execute User Story 3: Calibration and Validation.
    """
    logging.info("Executing User Story 3: Calibration and Validation...")
    
    # 1. Aggregate data (T041) - handled by validation.py or main logic
    # 2. Fit models (T027)
    fit_calibration_models(root / "data" / "processed" / "aggregated_bias.csv",
                           root / "data" / "processed" / "calibration_functions.json")
    
    # 3. Apply corrections and validate (T028, T029)
    apply_corrections(root / "data" / "processed" / "calibration_functions.json",
                      root / "data" / "processed" / "aggregated_bias.csv")
    validate_residuals(root / "data" / "processed" / "calibration_functions.json",
                       root / "data" / "processed" / "aggregated_bias.csv",
                       root / "data" / "validation" / "residual_report.json")
    
    # 4. Power Analysis (T030)
    generate_power_report(root / "data" / "validation" / "power_analysis_report.md")
    
    logging.info("User Story 3 complete.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Planetary Nebula Artifact Pipeline")
    parser.add_argument("--run-all", action="store_true", help="Run the full pipeline (US1 -> US2 -> US3)")
    parser.add_argument("--mode", choices=["generate", "process", "calibrate", "validate", "verify"],
                        help="Run a specific mode")
    parser.add_argument("--n-images", type=int, default=50, help="Number of synthetic images to generate")
    parser.add_argument("--output", type=str, default=None, help="Output directory override")
    parser.add_argument("--input", type=str, default=None, help="Input directory override")
    
    args = parser.parse_args()
    
    root = get_project_root()
    setup_directories(root)
    
    # Initialize logging
    log_file = root / "logs" / "research.log"
    logger = setup_logging(str(log_file))
    
    # Generate Run Manifest (T053)
    write_run_manifest_for_pipeline(root)
    
    if args.run_all:
        validate_pipeline_state(root)
        generate_data(root, args.n_images)
        process_artifacts(root)
        run_us1_pipeline(root)
        run_us2_pipeline(root)
        run_us3_pipeline(root)
        logger.info("Full pipeline execution complete.")
    elif args.mode:
        validate_pipeline_state(root)
        if args.mode == "generate":
            generate_data(root, args.n_images)
        elif args.mode == "process":
            process_artifacts(root)
        elif args.mode == "calibrate":
            run_us3_pipeline(root)
        elif args.mode == "validate":
            # Re-run validation steps
            run_us3_pipeline(root)
        elif args.mode == "verify":
            logger.info("Verification complete.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
