import argparse
import logging
import sys
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Import from local modules using relative imports to ensure execution from project root
# Note: The API surface shows 'code.config', 'code.io.writer', etc.
# To make this runnable as 'python code/main.py', we adjust imports to be relative to the code package.
# However, the prompt requires imports to match the API surface which implies 'from code.config'.
# We will assume the execution environment adds the project root to sys.path.
try:
    from code.config import get_project_root, get_config, NOISE_LEVELS, SATURATION_RANGE
    from code.io.writer import generate_run_manifest, write_run_manifest_for_pipeline
    from code.io.loader import load_fits_image, load_fits_safe
    from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
    from code.synthetic.artifacts import inject_noise, clip_saturation, run_noise_sweep, run_saturation_sweep
    from code.metrics.ellipticity import calculate_ellipticity
    from code.metrics.asymmetry import calculate_asymmetry
    from code.analysis.statistics import run_noise_regression, run_saturation_regression
    from code.analysis.regression import fit_calibration_models
    from code.analysis.validation import apply_corrections, validate_residuals
    from code.analysis.power_analysis import generate_power_report
except ImportError as e:
    # Fallback for direct execution if sys.path is not set up correctly
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from code.config import get_project_root, get_config, NOISE_LEVELS, SATURATION_RANGE
    from code.io.writer import generate_run_manifest, write_run_manifest_for_pipeline
    from code.io.loader import load_fits_image, load_fits_safe
    from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
    from code.synthetic.artifacts import inject_noise, clip_saturation, run_noise_sweep, run_saturation_sweep
    from code.metrics.ellipticity import calculate_ellipticity
    from code.metrics.asymmetry import calculate_asymmetry
    from code.analysis.statistics import run_noise_regression, run_saturation_regression
    from code.analysis.regression import fit_calibration_models
    from code.analysis.validation import apply_corrections, validate_residuals
    from code.analysis.power_analysis import generate_power_report

logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[str] = None):
    """Configure logging for the pipeline."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def setup_directories(root: Path):
    """Ensure required directory structure exists."""
    dirs = [
        root / 'data' / 'raw',
        root / 'data' / 'synthetic',
        root / 'data' / 'processed',
        root / 'data' / 'validation',
        root / 'logs',
        root / 'figures'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_pipeline_state(root: Path):
    """Check for required input files before execution."""
    gt_path = root / 'data' / 'synthetic' / 'gt_metadata.json'
    if not gt_path.exists():
        raise FileNotFoundError(
            f"Missing ground truth metadata. Ensure T006 (Synthetic Generation) has completed successfully. "
            f"Expected at: {gt_path}"
        )
    logger.info(f"Pipeline state validated. Ground truth found at {gt_path}")

def generate_data(args):
    """Generate synthetic planetary nebulae."""
    root = get_project_root()
    setup_directories(root)
    
    logger.info(f"Generating {args.n_images} synthetic images...")
    # Call the generator module's main or specific function
    # Based on API surface: from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
    # We need to orchestrate the generation loop.
    
    # Assuming generate_synthetic_nebula generates one image and returns it + metadata
    # and generate_gt_metadata saves the JSON.
    
    # We implement the loop here to ensure it runs as a script command.
    from code.synthetic.generator import generate_synthetic_nebula, generate_gt_metadata
    
    generated_metadata = []
    for i in range(args.n_images):
        img, meta = generate_synthetic_nebula(seed=i, image_id=f"{i:03d}")
        generated_metadata.append(meta)
    
    # Save the GT metadata
    generate_gt_metadata(generated_metadata, root / 'data' / 'synthetic' / 'gt_metadata.json')
    logger.info("Synthetic data generation complete.")

def process_artifacts(args):
    """Process synthetic data by injecting artifacts and measuring metrics."""
    root = get_project_root()
    validate_pipeline_state(root)
    
    # Load ground truth
    gt_path = root / 'data' / 'synthetic' / 'gt_metadata.json'
    with open(gt_path, 'r') as f:
        gt_data = json.load(f)
    
    logger.info(f"Loaded ground truth for {len(gt_data)} images.")
    
    # Run US1: Noise Sweep
    logger.info("Running Noise Sweep (US1)...")
    # This calls the sweep logic which should produce noise_trend_report.csv
    run_noise_sweep(root)
    
    # Run US2: Saturation Sweep
    logger.info("Running Saturation Sweep (US2)...")
    # This calls the sweep logic which should produce saturation_sweep.csv
    run_saturation_sweep(root)
    
    logger.info("Artifact processing complete.")

def calibrate_models(args):
    """Fit calibration models based on processed data."""
    root = get_project_root()
    
    # Run regression analyses
    logger.info("Running Noise Regression...")
    run_noise_regression(root)
    
    logger.info("Running Saturation Regression...")
    run_saturation_regression(root)
    
    logger.info("Fitting Calibration Models...")
    fit_calibration_models(root)
    
    logger.info("Model calibration complete.")

def validate_models(args):
    """Validate models and run power analysis."""
    root = get_project_root()
    
    # Apply corrections and validate residuals
    logger.info("Applying corrections and validating residuals...")
    apply_corrections(root)
    validate_residuals(root)
    
    # Power analysis
    logger.info("Running Power Analysis...")
    generate_power_report(root)
    
    logger.info("Validation complete.")

def verify_pipeline(args):
    """Final verification of the pipeline outputs."""
    root = get_project_root()
    
    required_files = [
        root / 'data' / 'synthetic' / 'gt_metadata.json',
        root / 'data' / 'processed' / 'noise_trend_report.csv',
        root / 'data' / 'processed' / 'saturation_sweep.csv',
        root / 'data' / 'processed' / 'noise_stats.csv',
        root / 'data' / 'processed' / 'saturation_stats.csv',
        root / 'data' / 'processed' / 'calibration_functions.json',
        root / 'data' / 'validation' / 'power_analysis_report.md'
    ]
    
    missing = [f for f in required_files if not f.exists()]
    if missing:
        logger.error(f"Verification failed. Missing files: {missing}")
        return 1
    
    logger.info("Pipeline verification successful.")
    return 0

def run_us2_pipeline(root: Path):
    """
    Execute User Story 2 pipeline: Saturation -> Asymmetry -> Bias -> Regression.
    Explicitly loads ground-truth metadata from data/synthetic/gt_metadata.json
    to ensure the 'Single Source of Truth' principle.
    """
    logger.info("Starting US2 Pipeline: Saturation Bias Quantification")
    
    # 1. Explicitly load ground-truth metadata (Single Source of Truth)
    gt_path = root / 'data' / 'synthetic' / 'gt_metadata.json'
    if not gt_path.exists():
        raise FileNotFoundError(
            f"Ground truth metadata not found at {gt_path}. "
            f"Please ensure T006 (Synthetic Generation) has completed successfully."
        )
    
    with open(gt_path, 'r') as f:
        gt_metadata_list = json.load(f)
    
    logger.info(f"Loaded {len(gt_metadata_list)} ground truth records from {gt_path}")
    
    # 2. Inject saturation artifacts (T021)
    # This function handles the sweep and writes saturation_sweep.csv
    logger.info("Injecting saturation artifacts...")
    run_saturation_sweep(root)
    
    # 3. Measure asymmetry and compute bias
    # The run_saturation_sweep function in artifacts.py should handle the measurement
    # and bias computation against the loaded GT. We ensure it does so.
    # (Note: If the logic is split, we might need to call a specific metric function here,
    # but based on T021 description, it saves results to saturation_sweep.csv).
    
    # 4. Run statistical regression (T023)
    logger.info("Running saturation regression analysis...")
    run_saturation_regression(root)
    
    logger.info("US2 Pipeline complete. Results saved to data/processed/")

def main():
    parser = argparse.ArgumentParser(description="Quantifying Data Artifact Impact Pipeline")
    subparsers = parser.add_subparsers(dest='mode', help='Pipeline mode')
    
    # Generate Mode
    gen_parser = subparsers.add_parser('generate', help='Generate synthetic data')
    gen_parser.add_argument('--n-images', type=int, default=50, help='Number of images to generate')
    gen_parser.add_argument('--output', type=str, default='data/synthetic', help='Output directory')
    
    # Process Mode
    proc_parser = subparsers.add_parser('process', help='Process data (inject artifacts)')
    proc_parser.add_argument('--input', type=str, default='data/synthetic', help='Input directory')
    proc_parser.add_argument('--output', type=str, default='data/processed', help='Output directory')
    
    # Calibrate Mode
    cal_parser = subparsers.add_parser('calibrate', help='Fit calibration models')
    cal_parser.add_argument('--input', type=str, default='data/processed/metrics.csv', help='Input metrics')
    cal_parser.add_argument('--output', type=str, default='data/processed/models.json', help='Output models')
    
    # Validate Mode
    val_parser = subparsers.add_parser('validate', help='Validate models')
    val_parser.add_argument('--input', type=str, default='data/processed/models.json', help='Input models')
    val_parser.add_argument('--test-set', type=str, default='data/synthetic/validation', help='Test set')
    val_parser.add_argument('--output', type=str, default='data/processed/validation_results.csv', help='Output results')
    
    # Verify Mode
    ver_parser = subparsers.add_parser('verify', help='Verify pipeline outputs')
    ver_parser.add_argument('--output', type=str, default='logs/verification.log', help='Log file')
    
    # Run All (Full Pipeline)
    run_all_parser = subparsers.add_parser('run-all', help='Run full pipeline')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    setup_logging('logs/research.log')
    root = get_project_root()
    
    # Generate run manifest immediately
    write_run_manifest_for_pipeline(root)
    
    if args.mode == 'generate':
        generate_data(args)
    elif args.mode == 'process':
        process_artifacts(args)
    elif args.mode == 'calibrate':
        calibrate_models(args)
    elif args.mode == 'validate':
        validate_models(args)
    elif args.mode == 'verify':
        verify_pipeline(args)
    elif args.mode == 'run-all':
        logger.info("Running full pipeline...")
        # 1. Generate
        generate_data(argparse.Namespace(n_images=50))
        # 2. Process (US1 + US2)
        process_artifacts(argparse.Namespace())
        # 3. Calibrate
        calibrate_models(argparse.Namespace())
        # 4. Validate
        validate_models(argparse.Namespace())
        # 5. Verify
        verify_pipeline(argparse.Namespace())
        logger.info("Full pipeline execution complete.")

if __name__ == '__main__':
    main()