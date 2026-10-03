"""
Validation script for quickstart.md reproducibility.
Executes the pipeline steps defined in quickstart.md and verifies outputs.
"""
import os
import sys
import json
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config
from utils.logging import init_logging, get_logger
from data.ingestion import verify_data_availability_wrapper
from data.preprocessing import preprocess_slr_data
from data.output import run_output_pipeline
from analysis.eotvos import run_eotvos_analysis
from analysis.validation import run_sensitivity_analysis

def setup_logging():
    """Configure logging for the validation script."""
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "quickstart_validation.log"
    
    return init_logging(
        name="quickstart_validator",
        log_file=str(log_file),
        level=logging.INFO
    )

def check_config_files(logger):
    """Verify that required configuration files exist."""
    logger.info("Checking configuration files...")
    config = get_config()
    
    required_files = [
        "config.yaml",
        "data/verified_datasets.yaml",
        "data/satellite_metadata.yaml",
        "contracts/normal_point.schema.yaml",
        "contracts/eotvos_result.schema.yaml"
    ]
    
    missing = []
    for f in required_files:
        path = PROJECT_ROOT / f
        if not path.exists():
            missing.append(f)
        else:
            logger.debug(f"Found config file: {f}")
    
    if missing:
        logger.error(f"Missing required config files: {missing}")
        return False
    
    logger.info("All configuration files present.")
    return True

def verify_data_artifacts(logger):
    """Verify that expected data artifacts exist."""
    logger.info("Verifying data artifacts...")
    
    required_artifacts = [
        "data/processed/cleaned_slr_data.csv",
        "data/results/eotvos_metrics.json",
        "data/results/orbit_solutions.json"
    ]
    
    existing = []
    missing = []
    
    for artifact in required_artifacts:
        path = PROJECT_ROOT / artifact
        if path.exists() and path.stat().st_size > 0:
            existing.append(artifact)
            logger.debug(f"Verified artifact: {artifact}")
        else:
            missing.append(artifact)
    
    if missing:
        logger.warning(f"Missing data artifacts (will attempt to generate): {missing}")
    
    return len(missing) == 0, existing, missing

def run_lightweight_pipeline(logger):
    """
    Execute a lightweight version of the pipeline to verify reproducibility.
    This runs the core steps without heavy computation.
    """
    logger.info("Running lightweight pipeline validation...")
    start_time = time.time()
    
    try:
        # Step 1: Verify data availability
        logger.info("Step 1: Verifying data availability...")
        availability_ok = verify_data_availability_wrapper()
        if not availability_ok:
            logger.warning("Data availability check returned warnings (expected for some satellites)")
        
        # Step 2: Preprocess data (if raw data exists)
        logger.info("Step 2: Preprocessing data...")
        # This will use existing cleaned data if available, or attempt to fetch
        preprocess_slr_data()
        
        # Step 3: Run output pipeline
        logger.info("Step 3: Running output pipeline...")
        run_output_pipeline()
        
        # Step 4: Run Eötvös analysis
        logger.info("Step 4: Running Eötvös analysis...")
        run_eotvos_analysis()
        
        # Step 5: Run sensitivity analysis (lightweight)
        logger.info("Step 5: Running sensitivity analysis...")
        run_sensitivity_analysis()
        
        elapsed = time.time() - start_time
        logger.info(f"Lightweight pipeline completed in {elapsed:.2f} seconds")
        return True, elapsed
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return False, time.time() - start_time

def validate_outputs(logger):
    """Validate that all expected outputs were generated correctly."""
    logger.info("Validating outputs...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "validation_status": "passed",
        "artifacts_verified": [],
        "errors": []
    }
    
    # Check Eötvös metrics
    metrics_path = PROJECT_ROOT / "data" / "results" / "eotvos_metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            if "eta_value" in metrics and "confidence_interval" in metrics:
                results["artifacts_verified"].append("eotvos_metrics.json")
                logger.info(f"Validated Eötvös metrics: η = {metrics['eta_value']:.2e}")
            else:
                results["errors"].append("eotvos_metrics.json missing required fields")
                results["validation_status"] = "failed"
        except Exception as e:
            results["errors"].append(f"Failed to parse eotvos_metrics.json: {str(e)}")
            results["validation_status"] = "failed"
    else:
        results["errors"].append("eotvos_metrics.json not found")
        results["validation_status"] = "failed"
    
    # Check orbit solutions
    solutions_path = PROJECT_ROOT / "data" / "results" / "orbit_solutions.json"
    if solutions_path.exists():
        try:
            with open(solutions_path, 'r') as f:
                solutions = json.load(f)
            
            if isinstance(solutions, dict) and len(solutions) > 0:
                results["artifacts_verified"].append("orbit_solutions.json")
                logger.info(f"Validated orbit solutions: {len(solutions)} solutions")
            else:
                results["errors"].append("orbit_solutions.json is empty or invalid")
                results["validation_status"] = "failed"
        except Exception as e:
            results["errors"].append(f"Failed to parse orbit_solutions.json: {str(e)}")
            results["validation_status"] = "failed"
    else:
        results["errors"].append("orbit_solutions.json not found")
        results["validation_status"] = "failed"
    
    # Check cleaned data
    cleaned_data_path = PROJECT_ROOT / "data" / "processed" / "cleaned_slr_data.csv"
    if cleaned_data_path.exists():
        results["artifacts_verified"].append("cleaned_slr_data.csv")
        logger.info(f"Validated cleaned data: {cleaned_data_path.stat().st_size} bytes")
    else:
        results["errors"].append("cleaned_slr_data.csv not found")
        results["validation_status"] = "failed"
    
    # Save validation report
    report_path = PROJECT_ROOT / "data" / "results" / "quickstart_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation report saved to: {report_path}")
    return results

def main():
    """Main entry point for quickstart validation."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting quickstart.md validation")
    logger.info("=" * 60)
    
    # Step 1: Check config files
    if not check_config_files(logger):
        logger.error("Configuration check failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Verify existing artifacts
    artifacts_exist, existing, missing = verify_data_artifacts(logger)
    
    # Step 3: Run lightweight pipeline if needed
    if not artifacts_exist:
        success, elapsed = run_lightweight_pipeline(logger)
        if not success:
            logger.error("Pipeline execution failed. Aborting.")
            sys.exit(1)
    else:
        logger.info("All artifacts already exist, skipping pipeline execution.")
    
    # Step 4: Validate outputs
    results = validate_outputs(logger)
    
    # Final status
    logger.info("=" * 60)
    if results["validation_status"] == "passed":
        logger.info("✅ QUICKSTART VALIDATION PASSED")
        logger.info(f"Verified {len(results['artifacts_verified'])} artifacts")
        sys.exit(0)
    else:
        logger.error("❌ QUICKSTART VALIDATION FAILED")
        for error in results["errors"]:
            logger.error(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()