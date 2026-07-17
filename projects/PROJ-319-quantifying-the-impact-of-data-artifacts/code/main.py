"""
Main pipeline entry point for the Quantifying the Impact of Data Artifacts project.

This script orchestrates the full analysis pipeline:
1. Generate synthetic planetary nebulae with known ground truth.
2. Inject artifacts (noise, saturation).
3. Measure metrics (ellipticity, asymmetry).
4. Compute bias against ground truth.
5. Run statistical significance tests.
6. Log results and save artifacts.

Usage:
    python code/main.py --mode generate --n-images 50
    python code/main.py --mode process --input data/synthetic --output data/processed
    python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json
    python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv
    python code/main.py --mode verify --output logs/verification.log
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

# Import project modules
from code.config import get_project_root, SEED, SATURATION_LEVELS, NOISE_LEVELS
from code.synthetic.generator import generate_synthetic_nebula, generate_nebula_base, calculate_true_ellipticity, calculate_true_asymmetry
from code.synthetic.artifacts import inject_noise, clip_saturation, run_saturation_sweep
from code.io.loader import load_fits_image, validate_fits_headers, MetadataValidationError
from code.io.writer import save_fits_image, save_metadata_json, save_run_log, write_artifact_manifest, compute_array_checksum
from code.metrics.ellipticity import calculate_ellipticity
from code.metrics.asymmetry import calculate_asymmetry
from code.analysis.statistical_tests import run_noise_sweep_statistics, run_saturation_significance_test
from code.analysis.sensitivity_sweep import run_sensitivity_sweep, save_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/research.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure all required directories exist."""
    project_root = get_project_root()
    dirs = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'synthetic',
        project_root / 'data' / 'processed',
        project_root / 'data' / 'validation',
        project_root / 'logs',
        project_root / 'code' / 'synthetic',
        project_root / 'code' / 'metrics',
        project_root / 'code' / 'analysis',
        project_root / 'code' / 'io',
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured at {project_root}")

def generate_data(n_images: int = 50):
    """Generate synthetic planetary nebulae with known ground truth."""
    project_root = get_project_root()
    output_dir = project_root / 'data' / 'synthetic'
    
    logger.info(f"Generating {n_images} synthetic nebulae with seed {SEED}")
    np.random.seed(SEED)
    
    images = []
    metadata_list = []
    
    for i in range(n_images):
        # Generate base nebula
        image, center = generate_nebula_base(seed=SEED + i)
        
        # Calculate true ellipticity and asymmetry
        true_ellipticity = calculate_true_ellipticity(image, center)
        true_asymmetry = calculate_true_asymmetry(image, center)
        
        # Save image
        image_path = output_dir / f"nebula_{i:04d}.fits"
        save_fits_image(image, image_path, {
            'image_id': f"nebula_{i:04d}",
            'center_x': center[0],
            'center_y': center[1],
            'true_ellipticity': true_ellipticity,
            'true_asymmetry': true_asymmetry,
            'checksum': compute_array_checksum(image)
        })
        
        images.append(image)
        metadata_list.append({
            'image_id': f"nebula_{i:04d}",
            'file_path': str(image_path),
            'true_ellipticity': true_ellipticity,
            'true_asymmetry': true_asymmetry,
            'checksum': compute_array_checksum(image)
        })
        
        if i % 10 == 0:
            logger.info(f"Generated {i+1}/{n_images} images")
    
    # Save ground truth metadata
    gt_path = output_dir / 'gt_metadata.json'
    save_metadata_json(metadata_list, gt_path)
    logger.info(f"Ground truth metadata saved to {gt_path}")
    
    # Write manifest
    manifest = {
        'total_images': n_images,
        'seed': SEED,
        'images': metadata_list
    }
    write_artifact_manifest(manifest, output_dir / 'synthetic_manifest.json')
    
    return images, metadata_list

def process_artifacts():
    """Process synthetic images with artifact injection and metric calculation."""
    project_root = get_project_root()
    synthetic_dir = project_root / 'data' / 'synthetic'
    processed_dir = project_root / 'data' / 'processed'
    
    # Load ground truth
    gt_path = synthetic_dir / 'gt_metadata.json'
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth metadata not found at {gt_path}. Run generate mode first.")
    
    with open(gt_path, 'r') as f:
        import json
        gt_data = json.load(f)
    
    logger.info(f"Loaded {len(gt_data)} ground truth entries")
    
    # Process each image
    all_metrics = []
    
    for entry in gt_data:
        image_path = Path(entry['file_path'])
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}, skipping")
            continue
        
        # Load image
        image = load_fits_image(image_path)
        
        # Inject noise (using configured levels)
        for sigma in NOISE_LEVELS:
            noisy_image, _ = inject_noise(image, sigma)
            ellipticity = calculate_ellipticity(noisy_image)
            asymmetry = calculate_asymmetry(noisy_image)
            
            all_metrics.append({
                'image_id': entry['image_id'],
                'artifact_type': 'noise',
                'artifact_level': sigma,
                'measured_ellipticity': ellipticity,
                'measured_asymmetry': asymmetry,
                'true_ellipticity': entry['true_ellipticity'],
                'true_asymmetry': entry['true_asymmetry'],
                'ellipticity_bias': ellipticity - entry['true_ellipticity'],
                'asymmetry_bias': asymmetry - entry['true_asymmetry']
            })
        
        # Inject saturation (using configured levels)
        for sat_frac in SATURATION_LEVELS:
            sat_image, _ = clip_saturation(image, sat_frac)
            ellipticity = calculate_ellipticity(sat_image)
            asymmetry = calculate_asymmetry(sat_image)
            
            all_metrics.append({
                'image_id': entry['image_id'],
                'artifact_type': 'saturation',
                'artifact_level': sat_frac,
                'measured_ellipticity': ellipticity,
                'measured_asymmetry': asymmetry,
                'true_ellipticity': entry['true_ellipticity'],
                'true_asymmetry': entry['true_asymmetry'],
                'ellipticity_bias': ellipticity - entry['true_ellipticity'],
                'asymmetry_bias': asymmetry - entry['true_asymmetry']
            })
        
        if len(all_metrics) % 100 == 0:
            logger.info(f"Processed {len(all_metrics)} metric entries")
    
    # Save all metrics
    metrics_path = processed_dir / 'metrics.csv'
    df = pd.DataFrame(all_metrics)
    df.to_csv(metrics_path, index=False)
    logger.info(f"Metrics saved to {metrics_path}")
    
    # Run noise significance test
    logger.info("Running noise significance test...")
    noise_stats = run_noise_sweep_statistics(all_metrics, 'noise')
    noise_stats_path = processed_dir / 'noise_stats.csv'
    pd.DataFrame(noise_stats).to_csv(noise_stats_path, index=False)
    logger.info(f"Noise statistics saved to {noise_stats_path}")
    
    # Run saturation significance test
    logger.info("Running saturation significance test...")
    sat_stats = run_saturation_significance_test(all_metrics, 'saturation')
    sat_stats_path = processed_dir / 'saturation_stats.csv'
    pd.DataFrame(sat_stats).to_csv(sat_stats_path, index=False)
    logger.info(f"Saturation statistics saved to {sat_stats_path}")
    
    # Run saturation sweep for detailed analysis
    logger.info("Running saturation sensitivity sweep...")
    sweep_results = run_sensitivity_sweep(all_metrics, 'saturation')
    save_results(sweep_results, processed_dir / 'saturation_sweep.csv')
    logger.info(f"Saturation sweep results saved to {processed_dir / 'saturation_sweep.csv'}")
    
    return df

def calibrate_models():
    """Fit calibration models to correct bias."""
    project_root = get_project_root()
    processed_dir = project_root / 'data' / 'processed'
    
    metrics_path = processed_dir / 'metrics.csv'
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics not found at {metrics_path}. Run process mode first.")
    
    df = pd.read_csv(metrics_path)
    
    from code.analysis.regression import fit_calibration_model, select_best_model
    
    # Fit noise model
    noise_df = df[df['artifact_type'] == 'noise']
    noise_model = fit_calibration_model(noise_df, 'ellipticity_bias', 'artifact_level')
    noise_model = select_best_model(noise_model)
    
    # Fit saturation model
    sat_df = df[df['artifact_type'] == 'saturation']
    sat_model = fit_calibration_model(sat_df, 'asymmetry_bias', 'artifact_level')
    sat_model = select_best_model(sat_model)
    
    # Save models
    models = {
        'noise_ellipticity': noise_model,
        'saturation_asymmetry': sat_model
    }
    
    models_path = processed_dir / 'calibration_functions.json'
    save_metadata_json(models, models_path)
    logger.info(f"Calibration models saved to {models_path}")
    
    return models

def validate_models():
    """Validate calibration models on test set."""
    project_root = get_project_root()
    processed_dir = project_root / 'data' / 'processed'
    validation_dir = project_root / 'data' / 'validation'
    
    models_path = processed_dir / 'calibration_functions.json'
    if not models_path.exists():
        raise FileNotFoundError(f"Models not found at {models_path}. Run calibrate mode first.")
    
    with open(models_path, 'r') as f:
        import json
        models = json.load(f)
    
    # Load validation data
    validation_path = validation_dir / 'validation_manifest.json'
    if not validation_path.exists():
        logger.warning("No validation manifest found, skipping validation")
        return
    
    with open(validation_path, 'r') as f:
        import json
        validation_data = json.load(f)
    
    results = []
    for entry in validation_data:
        image_path = Path(entry['file_path'])
        if not image_path.exists():
            continue
        
        image = load_fits_image(image_path)
        ellipticity = calculate_ellipticity(image)
        asymmetry = calculate_asymmetry(image)
        
        # Apply corrections if models exist
        corrected_ellipticity = ellipticity
        corrected_asymmetry = asymmetry
        
        if 'noise_ellipticity' in models:
            # Apply correction logic here
            pass
        
        if 'saturation_asymmetry' in models:
            # Apply correction logic here
            pass
        
        results.append({
            'target_id': entry['target_id'],
            'measured_ellipticity': ellipticity,
            'measured_asymmetry': asymmetry,
            'corrected_ellipticity': corrected_ellipticity,
            'corrected_asymmetry': corrected_asymmetry
        })
    
    # Save results
    results_path = processed_dir / 'validation_results.csv'
    pd.DataFrame(results).to_csv(results_path, index=False)
    logger.info(f"Validation results saved to {results_path}")
    
    return results

def verify_pipeline():
    """Verify all artifacts are present and consistent."""
    project_root = get_project_root()
    processed_dir = project_root / 'data' / 'processed'
    
    required_files = [
        'metrics.csv',
        'noise_stats.csv',
        'saturation_stats.csv',
        'saturation_sweep.csv',
        'calibration_functions.json'
    ]
    
    missing = []
    for f in required_files:
        if not (processed_dir / f).exists():
            missing.append(f)
    
    if missing:
        logger.error(f"Missing required files: {missing}")
        return False
    
    logger.info("All required artifacts present")
    return True

def main():
    parser = argparse.ArgumentParser(description='Main pipeline for data artifact impact analysis')
    parser.add_argument('--mode', choices=['generate', 'process', 'calibrate', 'validate', 'verify'], required=True,
                      help='Pipeline mode to execute')
    parser.add_argument('--n-images', type=int, default=50, help='Number of images to generate')
    parser.add_argument('--input', type=str, help='Input directory for process mode')
    parser.add_argument('--output', type=str, help='Output directory for results')
    parser.add_argument('--test-set', type=str, help='Test set directory for validation')
    
    args = parser.parse_args()
    
    setup_directories()
    
    if args.mode == 'generate':
        generate_data(args.n_images)
    elif args.mode == 'process':
        process_artifacts()
    elif args.mode == 'calibrate':
        calibrate_models()
    elif args.mode == 'validate':
        validate_models()
    elif args.mode == 'verify':
        success = verify_pipeline()
        sys.exit(0 if success else 1)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")

if __name__ == '__main__':
    main()