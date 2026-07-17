"""
Main CLI entry point for the Planetary Nebula Artifact Impact Pipeline.

Refactored into modular CLI entry points to support:
1. Data Generation (Synthetic Nebulae)
2. Artifact Injection & Processing (Noise, Saturation)
3. Calibration (Regression & Model Fitting)
4. Validation (Real HST & Residual Bias)
5. Verification (Pipeline Integrity)

This script acts as the orchestrator, calling specific functions from
code/synthetic/, code/metrics/, code/analysis/, and code/io/ modules.
"""
import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Project imports
from code.config import (
    get_project_root, 
    NOISE_LEVELS, 
    SATURATION_LEVELS, 
    DEFAULT_SEED,
    DATA_SYNTHETIC_DIR,
    DATA_PROCESSED_DIR,
    DATA_VALIDATION_DIR,
    LOGS_DIR
)
from code.setup_dirs import create_directories
from code.io.loader import load_fits_image, validate_fits_headers
from code.io.writer import save_fits_image, save_metadata_json, write_artifact_manifest
from code.synthetic.generator import generate_synthetic_nebula, calculate_true_ellipticity, calculate_true_asymmetry
from code.synthetic.artifacts import inject_noise, clip_saturation, run_saturation_sweep
from code.metrics.ellipticity import calculate_ellipticity
from code.metrics.asymmetry import calculate_asymmetry
from code.analysis.statistics import run_noise_significance_test, run_saturation_significance_test
from code.analysis.regression import fit_calibration_models
from code.analysis.validation import apply_calibration, validate_residuals, run_validation_on_real_hst
from code.analysis.power_analysis import run_power_analysis

# Configure Logging
def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging configuration for the pipeline."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def setup_directories(logger: logging.Logger) -> Path:
    """Initialize project directory structure."""
    root = get_project_root()
    dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "synthetic",
        root / "data" / "processed",
        root / "data" / "validation",
        root / "tests",
        root / "logs",
        root / "figures"
    ]
    create_directories(dirs, logger)
    logger.info(f"Project root: {root}")
    return root

def generate_data(args: argparse.Namespace, logger: logging.Logger) -> None:
    """
    Generate synthetic planetary nebulae with known ground truth.
    
    This implements T006: Generate synthetic data and save ground truth
    to data/synthetic/gt_metadata.json.
    """
    logger.info("Starting synthetic data generation...")
    root = get_project_root()
    output_dir = root / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    n_images = args.n_images if hasattr(args, 'n_images') and args.n_images else 50
    seed = args.seed if hasattr(args, 'seed') else DEFAULT_SEED
    
    rng = np.random.default_rng(seed)
    gt_metadata = []
    
    logger.info(f"Generating {n_images} synthetic nebulae with seed {seed}...")
    
    for i in range(n_images):
        # Generate base image
        image_id = f"synth_{i:04d}"
        img, params = generate_synthetic_nebula(rng, seed=seed + i)
        
        # Calculate true metrics
        true_ellip = calculate_true_ellipticity(params)
        true_asym = calculate_true_asymmetry(params)
        
        # Save image
        img_path = output_dir / f"{image_id}.fits"
        save_fits_image(img, img_path, params)
        
        # Record metadata
        gt_metadata.append({
            "image_id": image_id,
            "file_path": str(img_path),
            "ellipticity": true_ellip,
            "asymmetry": true_asym,
            "seed": seed + i
        })
        
        if i % 10 == 0:
            logger.info(f"Generated {i+1}/{n_images} images")
    
    # Save ground truth metadata (Single Source of Truth)
    gt_path = output_dir / "gt_metadata.json"
    save_metadata_json(gt_metadata, gt_path)
    logger.info(f"Saved ground truth metadata to {gt_path}")
    
    # Write manifest
    write_artifact_manifest(output_dir, logger)
    logger.info("Data generation complete.")

def process_artifacts(args: argparse.Namespace, logger: logging.Logger) -> None:
    """
    Inject artifacts (noise, saturation) and compute metrics.
    
    This implements T015 (Noise) and T022/T024 (Saturation).
    It must load ground truth from data/synthetic/gt_metadata.json.
    """
    logger.info("Starting artifact injection and processing...")
    root = get_project_root()
    synth_dir = root / "data" / "synthetic"
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Ground Truth
    gt_path = synth_dir / "gt_metadata.json"
    if not gt_path.exists():
        raise FileNotFoundError(
            f"Ground truth metadata not found at {gt_path}. "
            "Please run 'generate' mode first (T006)."
        )
    
    with open(gt_path, 'r') as f:
        gt_metadata = json.load(f)
    
    logger.info(f"Loaded ground truth for {len(gt_metadata)} images.")
    
    # 1. Noise Sweep (US1)
    logger.info("Running Noise Sweep (US1)...")
    noise_results = []
    for entry in gt_metadata:
        img_path = Path(entry["file_path"])
        img = load_fits_image(img_path)
        true_ellip = entry["ellipticity"]
        
        for sigma in NOISE_LEVELS:
            noisy_img = inject_noise(img, sigma, rng=np.random.default_rng(entry["seed"]))
            measured_ellip = calculate_ellipticity(noisy_img)
            bias = measured_ellip - true_ellip
            
            noise_results.append({
                "image_id": entry["image_id"],
                "sigma": sigma,
                "true_ellipticity": true_ellip,
                "measured_ellipticity": measured_ellip,
                "bias": bias
            })
    
    # Save noise sweep results
    noise_csv = processed_dir / "noise_sweep.csv"
    if noise_results:
        import csv
        with open(noise_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=noise_results[0].keys())
            writer.writeheader()
            writer.writerows(noise_results)
        logger.info(f"Saved noise sweep to {noise_csv}")
    
    # Run noise significance test
    run_noise_significance_test(noise_results, processed_dir / "noise_stats.csv")
    
    # 2. Saturation Sweep (US2)
    logger.info("Running Saturation Sweep (US2)...")
    saturation_results = []
    valid_entries = [] # For regression later
    
    for entry in gt_metadata:
        img_path = Path(entry["file_path"])
        img = load_fits_image(img_path)
        true_asym = entry["asymmetry"]
        
        for sat_frac in SATURATION_LEVELS:
            try:
                sat_img = clip_saturation(img, sat_frac, rng=np.random.default_rng(entry["seed"]))
                measured_asym = calculate_asymmetry(sat_img)
                bias = measured_asym - true_asym
                
                saturation_results.append({
                    "image_id": entry["image_id"],
                    "saturation_fraction": sat_frac,
                    "true_asymmetry": true_asym,
                    "measured_asymmetry": measured_asym,
                    "bias": bias
                })
                valid_entries.append({
                    "image_id": entry["image_id"],
                    "saturation_fraction": sat_frac,
                    "bias": bias
                })
            except ValueError as e:
                logger.warning(f"Skipping image {entry['image_id']} at sat_frac {sat_frac}: {e}")
    
    # Save saturation sweep results (T024 requirement)
    sat_csv = processed_dir / "saturation_sweep.csv"
    if saturation_results:
        import csv
        with open(sat_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=saturation_results[0].keys())
            writer.writeheader()
            writer.writerows(saturation_results)
        logger.info(f"Saved saturation sweep to {sat_csv}")
    
    # Run saturation significance test
    run_saturation_significance_test(saturation_results, processed_dir / "saturation_stats.csv")
    
    logger.info("Artifact processing complete.")

def calibrate_models(args: argparse.Namespace, logger: logging.Logger) -> None:
    """
    Fit regression models to correct bias.
    
    Implements T027 and T029.
    """
    logger.info("Starting calibration model fitting...")
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    
    # Aggregate data (T041)
    noise_csv = processed_dir / "noise_sweep.csv"
    sat_csv = processed_dir / "saturation_sweep.csv"
    
    if not noise_csv.exists() or not sat_csv.exists():
        raise FileNotFoundError("Sweep results not found. Run 'process' mode first.")
    
    # Load and prepare data for regression
    import pandas as pd
    df_noise = pd.read_csv(noise_csv)
    df_sat = pd.read_csv(sat_csv)
    
    # Fit models
    models = fit_calibration_models(df_noise, df_sat)
    
    # Save models
    model_path = processed_dir / "calibration_functions.json"
    with open(model_path, 'w') as f:
        json.dump(models, f, indent=2)
    
    logger.info(f"Saved calibration models to {model_path}")
    logger.info("Calibration complete.")

def validate_models(args: argparse.Namespace, logger: logging.Logger) -> None:
    """
    Validate calibration models on held-out data and real HST images.
    
    Implements T028, T031, and T009 dependency.
    """
    logger.info("Starting model validation...")
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    validation_dir = root / "data" / "validation"
    
    model_path = processed_dir / "calibration_functions.json"
    if not model_path.exists():
        raise FileNotFoundError("Calibration models not found. Run 'calibrate' mode first.")
    
    with open(model_path, 'r') as f:
        models = json.load(f)
    
    # 1. Cross-validation on synthetic data (T045)
    logger.info("Validating on synthetic held-out data...")
    # (Assuming split logic is inside apply_calibration or separate function)
    # For this task, we call the validation logic
    residuals = validate_residuals(models, processed_dir / "noise_sweep.csv", processed_dir / "saturation_sweep.csv")
    
    # 2. Real HST Validation (T028, T031)
    # Requires T009 to be complete (Real HST images in data/validation/)
    real_hst_dir = root / "data" / "validation"
    manifest_path = real_hst_dir / "validation_manifest.json"
    
    if manifest_path.exists():
        logger.info("Validating on Real HST images...")
        hst_results = run_validation_on_real_hst(models, manifest_path)
        
        # Save validation report
        report_path = validation_dir / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(hst_results, f, indent=2)
        logger.info(f"Saved real HST validation report to {report_path}")
    else:
        logger.warning("Real HST validation manifest not found. Skipping real data validation.")
    
    logger.info("Validation complete.")

def verify_pipeline(args: argparse.Namespace, logger: logging.Logger) -> None:
    """
    Run power analysis and verify pipeline integrity.
    
    Implements T030 and T035 (Integration check).
    """
    logger.info("Running pipeline verification...")
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    validation_dir = root / "data" / "validation"
    
    # Power Analysis (T030)
    logger.info("Running power analysis...")
    power_report = run_power_analysis(
        processed_dir / "noise_sweep.csv",
        processed_dir / "saturation_sweep.csv",
        output_path=validation_dir / "power_analysis_report.md"
    )
    logger.info(f"Power analysis report saved to {validation_dir / 'power_analysis_report.md'}")
    
    # Check for critical artifacts
    required_files = [
        processed_dir / "gt_metadata.json",
        processed_dir / "noise_sweep.csv",
        processed_dir / "saturation_sweep.csv",
        processed_dir / "calibration_functions.json"
    ]
    
    missing = [f for f in required_files if not f.exists()]
    if missing:
        logger.error(f"Missing critical artifacts: {missing}")
        sys.exit(1)
    
    logger.info("Pipeline verification complete. All artifacts present.")

def main():
    parser = argparse.ArgumentParser(
        description="Planetary Nebula Artifact Impact Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='mode', help='Pipeline mode')
    
    # Generate Mode
    gen_parser = subparsers.add_parser('generate', help='Generate synthetic data')
    gen_parser.add_argument('--n-images', type=int, default=50, help='Number of images to generate')
    gen_parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help='Random seed')
    
    # Process Mode
    proc_parser = subparsers.add_parser('process', help='Inject artifacts and compute metrics')
    
    # Calibrate Mode
    cal_parser = subparsers.add_parser('calibrate', help='Fit calibration models')
    
    # Validate Mode
    val_parser = subparsers.add_parser('validate', help='Validate models')
    val_parser.add_argument('--test-set', type=str, default='synthetic', help='Test set type')
    
    # Verify Mode
    ver_parser = subparsers.add_parser('verify', help='Verify pipeline integrity')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    # Setup
    root = setup_directories(setup_logging(root / "logs" / "pipeline.log"))
    logger = logging.getLogger("pipeline")
    
    try:
        if args.mode == 'generate':
            generate_data(args, logger)
        elif args.mode == 'process':
            process_artifacts(args, logger)
        elif args.mode == 'calibrate':
            calibrate_models(args, logger)
        elif args.mode == 'validate':
            validate_models(args, logger)
        elif args.mode == 'verify':
            verify_pipeline(args, logger)
        elif args.mode == 'run-all':
            # T046: Unified entry point
            logger.info("Running full pipeline sequentially...")
            generate_data(args, logger)
            process_artifacts(args, logger)
            calibrate_models(args, logger)
            validate_models(args, logger)
            verify_pipeline(args, logger)
            logger.info("Full pipeline execution complete.")
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()