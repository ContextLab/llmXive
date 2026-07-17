import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from local modules
from code.config import get_project_root
from code.io.writer import write_run_manifest_for_pipeline
from code.synthetic.generator import main as generate_main
from code.synthetic.artifacts import run_saturation_sweep
from code.analysis.sensitivity_sweep import run_sensitivity_sweep
from code.analysis.statistical_tests import run_noise_sweep_statistics
from code.analysis.regression import fit_calibration_models
from code.analysis.validation import apply_corrections, validate_residuals
from code.analysis.power_analysis import generate_power_report

logger = logging.getLogger(__name__)

def setup_logging(log_file: str = "logs/research.log"):
    """Configure logging for the pipeline."""
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_directories():
    """Ensure all required directories exist."""
    dirs = [
        "code", "code/synthetic", "code/metrics", "code/analysis", "code/io",
        "data", "data/raw", "data/synthetic", "data/processed", "data/validation",
        "tests", "tests/unit", "tests/contract", "tests/integration",
        "logs", "figures", "docs", "docs/decisions"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def generate_data(n_images: int = 50):
    """Generate synthetic planetary nebulae."""
    logger.info(f"Generating {n_images} synthetic nebulae...")
    # Execute generation logic
    generate_main()

def process_artifacts():
    """Process synthetic data by injecting artifacts and measuring metrics."""
    logger.info("Processing artifacts (noise and saturation)...")
    
    # Run noise sweep (US1)
    run_sensitivity_sweep()
    
    # Run saturation sweep (US2)
    run_saturation_sweep()
    
    # Run statistical tests
    run_noise_sweep_statistics()

def calibrate_models():
    """Fit calibration models based on processed data."""
    logger.info("Calibrating models...")
    fit_calibration_models()

def validate_models():
    """Validate models and apply corrections."""
    logger.info("Validating models and applying corrections...")
    apply_corrections()
    validate_residuals()
    generate_power_report()

def verify_pipeline():
    """Verify pipeline state and generate run manifest."""
    logger.info("Verifying pipeline state...")
    
    # Check for critical dependencies
    root = get_project_root()
    gt_path = root / "data" / "synthetic" / "gt_metadata.json"
    agg_path = root / "data" / "processed" / "aggregated_bias.csv"
    
    if not gt_path.exists():
        logger.error("Critical dependency missing: data/synthetic/gt_metadata.json")
        sys.exit(1)
    
    # Generate reproducibility manifest
    params = {
        "git_commit": None, # Will be populated by writer
        "config": "default",
        "seed": 42
    }
    
    write_run_manifest_for_pipeline(
        pipeline_mode="verify",
        artifact_params=params,
        output_path="data/processed/run_manifest.json"
    )
    
    logger.info("Pipeline verification complete. Manifest written to data/processed/run_manifest.json")

def main():
    parser = argparse.ArgumentParser(description="Planetary Nebula Artifact Impact Pipeline")
    parser.add_argument("--mode", type=str, required=True,
                      choices=["generate", "process", "calibrate", "validate", "verify", "run-all"],
                      help="Pipeline mode to execute")
    parser.add_argument("--n-images", type=int, default=50, help="Number of synthetic images to generate")
    
    args = parser.parse_args()
    
    setup_logging()
    setup_directories()
    
    if args.mode == "generate":
        generate_data(args.n_images)
    elif args.mode == "process":
        process_artifacts()
    elif args.mode == "calibrate":
        calibrate_models()
    elif args.mode == "validate":
        validate_models()
    elif args.mode == "verify":
        verify_pipeline()
    elif args.mode == "run-all":
        logger.info("Running full pipeline...")
        generate_data(args.n_images)
        process_artifacts()
        calibrate_models()
        validate_models()
        verify_pipeline()
    
    logger.info(f"Pipeline mode '{args.mode}' completed successfully.")

if __name__ == "__main__":
    main()
