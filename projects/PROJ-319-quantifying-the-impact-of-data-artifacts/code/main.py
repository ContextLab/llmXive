import argparse
import logging
import sys
import json
import os
import subprocess
from pathlib import Path

from code.config import get_project_root, get_config_summary, NOISE_LEVELS, SATURATION_RANGE
from code.io.writer import generate_run_manifest, write_run_manifest_for_pipeline
from code.io.loader import load_fits_image, validate_fits_headers
from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
from code.synthetic.artifacts import run_noise_sweep, run_saturation_sweep, inject_noise, clip_saturation
from code.metrics.ellipticity import calculate_ellipticity
from code.metrics.asymmetry import calculate_asymmetry
from code.analysis.statistics import run_noise_regression, run_saturation_regression
from code.analysis.validation import apply_corrections, validate_residuals
from code.analysis.regression import fit_calibration_models
from code.analysis.power_analysis import calculate_power, calculate_mdes, generate_power_report

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/research.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_directories(root: Path):
    """Ensure required directories exist."""
    dirs = [
        root / "data" / "raw",
        root / "data" / "synthetic",
        root / "data" / "processed",
        root / "data" / "validation",
        root / "logs",
        root / "code" / "synthetic",
        root / "code" / "metrics",
        root / "code" / "analysis",
        root / "code" / "io"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_pipeline_state(root: Path):
    """Check for required input files before execution."""
    gt_path = root / "data" / "synthetic" / "gt_metadata.json"
    if not gt_path.exists():
        raise FileNotFoundError(
            f"Missing ground truth metadata. Ensure T006 (Synthetic Generation) has completed successfully. "
            f"Expected file: {gt_path}"
        )
    logger.info("Pipeline state validation passed.")

def generate_data(root: Path, n_images: int = 50):
    """Generate synthetic planetary nebulae."""
    logger.info(f"Generating {n_images} synthetic nebulae...")
    config = get_config_summary()
    
    # Generate images
    for i in range(n_images):
        generate_synthetic_nebula(i, root / "data" / "synthetic")
    
    # Generate ground truth metadata
    generate_gt_metadata(root / "data" / "synthetic", n_images)
    
    logger.info("Synthetic data generation complete.")

def process_artifacts(root: Path):
    """Process synthetic data by injecting artifacts and measuring metrics."""
    logger.info("Processing artifacts (Noise and Saturation)...")
    
    # Run Noise Sweep (US1)
    run_noise_sweep(root)
    
    # Run Saturation Sweep (US2)
    run_saturation_sweep(root)
    
    logger.info("Artifact injection and measurement complete.")

def run_us1_pipeline(root: Path):
    """
    User Story 1: Evaluate Noise-Induced Bias on Ellipticity.
    1. Load clean image -> 2. Inject noise -> 3. Measure ellipticity -> 
    4. Load ground truth -> 5. Compute bias -> 6. Run regression -> 7. Log results.
    """
    logger.info("Starting User Story 1 Pipeline (Noise vs Ellipticity)...")
    gt_path = root / "data" / "synthetic" / "gt_metadata.json"
    
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth metadata missing at {gt_path}")

    with open(gt_path, 'r') as f:
        gt_data = json.load(f)

    results = []
    for item in gt_data:
        img_id = item['image_id']
        clean_path = root / "data" / "synthetic" / f"synth_{img_id:03d}.fits"
        
        if not clean_path.exists():
            logger.warning(f"Clean image missing for {img_id}, skipping.")
            continue

        # Inject noise for each level defined in config
        for sigma in NOISE_LEVELS:
            try:
                # Inject noise
                noisy_img, _ = inject_noise(clean_path, sigma)
                
                # Measure ellipticity
                ellipticity, _ = calculate_ellipticity(noisy_img)
                
                # Compute bias against ground truth
                true_ell = item['ellipticity']
                bias = ellipticity - true_ell
                
                results.append({
                    'image_id': img_id,
                    'sigma': sigma,
                    'true_ellipticity': true_ell,
                    'measured_ellipticity': ellipticity,
                    'bias': bias
                })
            except Exception as e:
                logger.error(f"Error processing image {img_id} with sigma {sigma}: {e}")

    # Run regression analysis
    logger.info("Running noise regression analysis...")
    run_noise_regression(results, root / "data" / "processed" / "noise_stats.csv")
    logger.info("US1 Pipeline complete.")

def run_us2_pipeline(root: Path):
    """
    User Story 2: Quantify Saturation-Induced Bias on Asymmetry.
    1. Load clean image -> 2. Inject saturation -> 3. Measure asymmetry -> 
    4. Load ground truth -> 5. Call run_saturation_regression -> 6. Compute bias -> 7. Log results.
    """
    logger.info("Starting User Story 2 Pipeline (Saturation vs Asymmetry)...")
    
    gt_path = root / "data" / "synthetic" / "gt_metadata.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth metadata missing at {gt_path}")

    with open(gt_path, 'r') as f:
        gt_data = json.load(f)

    results = []
    for item in gt_data:
        img_id = item['image_id']
        clean_path = root / "data" / "synthetic" / f"synth_{img_id:03d}.fits"
        
        if not clean_path.exists():
            logger.warning(f"Clean image missing for {img_id}, skipping.")
            continue

        # Inject saturation for each level defined in config (0.0 to 0.5 step 0.05)
        for sat_frac in SATURATION_RANGE:
            try:
                # Inject saturation
                sat_img, valid = clip_saturation(clean_path, sat_frac)
                if not valid:
                    logger.warning(f"Saturation clipping invalid for {img_id} at {sat_frac}, skipping.")
                    continue

                # Measure asymmetry
                asymmetry, _ = calculate_asymmetry(sat_img)
                
                # Compute bias against ground truth
                true_asym = item['asymmetry']
                bias = asymmetry - true_asym
                
                results.append({
                    'image_id': img_id,
                    'saturation_fraction': sat_frac,
                    'true_asymmetry': true_asym,
                    'measured_asymmetry': asymmetry,
                    'bias': bias
                })
            except Exception as e:
                logger.error(f"Error processing image {img_id} with saturation {sat_frac}: {e}")

    # Run regression analysis
    logger.info("Running saturation regression analysis...")
    run_saturation_regression(results, root / "data" / "processed" / "saturation_stats.csv")
    logger.info("US2 Pipeline complete.")

def run_us3_pipeline(root: Path):
    """
    User Story 3: Derive Calibration Functions.
    1. Aggregate results -> 2. Fit models -> 3. Apply corrections -> 4. Validate.
    """
    logger.info("Starting User Story 3 Pipeline (Calibration)...")
    
    # Aggregate bias data (Conceptual step, assuming CSVs exist from US1/US2)
    noise_csv = root / "data" / "processed" / "noise_stats.csv"
    sat_csv = root / "data" / "processed" / "saturation_stats.csv"
    
    if not noise_csv.exists() or not sat_csv.exists():
        logger.error("US1 or US2 outputs missing. Cannot run US3.")
        return

    # Fit calibration models
    logger.info("Fitting calibration models...")
    models = fit_calibration_models(noise_csv, sat_csv, root / "data" / "processed" / "calibration_functions.json")
    
    # Validate residuals
    logger.info("Validating residuals...")
    validate_residuals(models, root / "data" / "processed" / "calibration_functions.json")
    
    logger.info("US3 Pipeline complete.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument('--mode', type=str, choices=['generate', 'process', 'calibrate', 'validate', 'verify', 'run-all'], required=True)
    parser.add_argument('--n-images', type=int, default=50)
    parser.add_argument('--output', type=str, default='data/synthetic')
    
    args = parser.parse_args()
    root = get_project_root()
    setup_directories(root)

    # Generate Run Manifest
    generate_run_manifest(root / "data" / "processed" / "run_manifest.json")

    if args.mode == 'generate':
        generate_data(root, args.n_images)
    elif args.mode == 'process':
        validate_pipeline_state(root)
        process_artifacts(root)
        run_us1_pipeline(root)
        run_us2_pipeline(root)
    elif args.mode == 'calibrate':
        validate_pipeline_state(root)
        run_us3_pipeline(root)
    elif args.mode == 'validate':
        # Placeholder for validation logic
        logger.info("Validation step placeholder.")
    elif args.mode == 'verify':
        logger.info("Verification step placeholder.")
    elif args.mode == 'run-all':
        validate_pipeline_state(root)
        generate_data(root, args.n_images)
        run_us1_pipeline(root)
        run_us2_pipeline(root)
        run_us3_pipeline(root)
    
    logger.info("Pipeline execution finished.")

if __name__ == '__main__':
    main()