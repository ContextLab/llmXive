"""
T046: Quickstart Validation Script
Runs the full pipeline as described in quickstart.md to ensure reproducible execution.
Verifies all expected artifacts are generated and valid.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event
from utils.timing import run_pipeline_script
from utils.memory_monitor import run_script_with_memory_monitoring
from utils.verify_hashes import main as verify_hashes_main
from utils.model_metadata import main as verify_metadata_main

logger = get_logger(__name__)

def validate_artifacts():
    """Check that all required artifacts exist and have content."""
    required_files = {
        "data/processed/features.csv": "Feature dataset",
        "results/model.pkl": "Trained model",
        "results/metrics.json": "Model metrics",
        "results/screening_full.csv": "Screening results",
        "results/screening_candidates.md": "Candidate report",
        "logs/pipeline.log": "Pipeline log",
        "results/manifest.json": "Hash manifest"
    }

    missing = []
    for path, desc in required_files.items():
        full_path = project_root / path
        if not full_path.exists():
            missing.append(f"{desc} ({path})")
        elif full_path.stat().st_size == 0:
            missing.append(f"{desc} ({path}) is empty")

    if missing:
        logger.error(f"Missing or empty artifacts: {', '.join(missing)}")
        return False
    
    logger.info("All required artifacts present and non-empty")
    return True

def validate_metrics():
    """Validate metrics file contains expected fields."""
    metrics_path = project_root / "results/metrics.json"
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        required_fields = ['test_rmse', 'best_params', 'cv_score']
        missing_fields = [f for f in required_fields if f not in metrics]
        
        if missing_fields:
            logger.error(f"Metrics missing fields: {missing_fields}")
            return False
        
        logger.info(f"Metrics validation passed: RMSE={metrics['test_rmse']:.4f}")
        return True
    except Exception as e:
        logger.error(f"Metrics validation failed: {e}")
        return False

def main():
    logger.info("Starting Quickstart Validation (T046)")
    start_time = time.time()

    try:
        # 1. Run the full pipeline if artifacts don't exist
        features_path = project_root / "data/processed/features.csv"
        model_path = project_root / "results/model.pkl"

        if not features_path.exists() or not model_path.exists():
            logger.info("Required artifacts missing. Running full pipeline...")
            
            # Run data processing
            run_pipeline_script(
                "code/data/download.py", 
                "Data Download", 
                timeout=3600
            )
            
            run_pipeline_script(
                "code/data/descriptors.py", 
                "Descriptor Calculation", 
                timeout=3600
            )
            
            run_pipeline_script(
                "code/data/preprocess.py", 
                "Data Preprocessing", 
                timeout=3600
            )
            
            # Run model training
            run_pipeline_script(
                "code/models/train.py", 
                "Model Training", 
                timeout=7200
            )
            
            # Run screening
            run_pipeline_script(
                "code/models/predict.py", 
                "Virtual Screening", 
                timeout=3600
            )
            
            # Generate report
            run_pipeline_script(
                "code/models/generate_candidates_report.py", 
                "Candidate Report Generation", 
                timeout=600
            )
        else:
            logger.info("Artifacts exist. Skipping pipeline execution.")

        # 2. Validate artifacts
        if not validate_artifacts():
            logger.error("Artifact validation failed")
            return 1

        # 3. Validate metrics
        if not validate_metrics():
            logger.error("Metrics validation failed")
            return 1

        # 4. Verify hashes
        logger.info("Verifying artifact hashes...")
        verify_hashes_main()

        # 5. Verify metadata
        logger.info("Verifying model metadata...")
        verify_metadata_main()

        elapsed = time.time() - start_time
        logger.info(f"Quickstart validation completed successfully in {elapsed:.2f}s")
        log_pipeline_event("T046_VALIDATION_SUCCESS", f"Duration: {elapsed:.2f}s")
        return 0

    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        log_pipeline_event("T046_VALIDATION_FAILED", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
