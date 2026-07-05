"""
Quickstart Validation Script for PROJ-134.

This script validates the pipeline execution as per quickstart.md:
1. Runs the full simulation and ingestion pipeline.
2. Verifies that all expected output artifacts exist.
3. Calculates and verifies SHA-256 checksums for all derived data.
4. Updates the state/...yaml file with the latest checksums.
5. Runs the Bayesian model and validation pipeline.
6. Generates the final report.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories
from utils.hashing import calculate_sha256, update_state_yaml, checksum_derived_datasets
from utils.logging_utils import log_pipeline_step, get_logger
from data.simulation_mfq import main as run_mfq_sim
from data.simulation_stories import main as run_stories_sim
from data.ingest import main as run_ingest
from models.bayesian import main as run_bayesian
from analysis.validation import run_validation_pipeline
from reports.generate_report import main as run_report_gen

logger = get_logger(__name__)

def run_script(script_name: str, module_path: str) -> bool:
    """Execute a specific script module."""
    logger.info(f"Running {script_name}...")
    try:
        # Import and run the main function directly to ensure execution
        # This avoids shell escaping issues and ensures we use the current environment
        if module_path == "data.simulation_mfq":
            run_mfq_sim()
        elif module_path == "data.simulation_stories":
            run_stories_sim()
        elif module_path == "data.ingest":
            run_ingest()
        elif module_path == "models.bayesian":
            run_bayesian()
        elif module_path == "analysis.validation":
            run_validation_pipeline()
        elif module_path == "reports.generate_report":
            run_report_gen()
        else:
            logger.error(f"Unknown module path: {module_path}")
            return False
        
        logger.info(f"{script_name} completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_artifacts(expected_files: List[str]) -> Tuple[bool, List[str]]:
    """Verify that all expected files exist."""
    missing = []
    for rel_path in expected_files:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
            logger.warning(f"Missing artifact: {rel_path}")
        else:
            logger.info(f"Found artifact: {rel_path}")
    
    if missing:
        return False, missing
    return True, []

def validate_checksums() -> bool:
    """Run checksum validation on derived datasets and update state."""
    logger.info("Validating checksums for derived datasets...")
    try:
        # This function updates state.yaml and verifies existing checksums
        checksum_derived_datasets()
        logger.info("Checksum validation successful.")
        return True
    except Exception as e:
        logger.error(f"Checksum validation failed: {e}")
        return False

def main():
    """Main validation entry point."""
    print("=== Starting Quickstart Validation ===")
    logger.info("Starting Quickstart Validation Pipeline")
    
    # Ensure directories exist
    ensure_directories()
    
    # Define expected artifacts based on pipeline execution
    expected_artifacts = [
        "data/simulated/mfq_data.csv",
        "data/simulated/stories_data.csv",
        "data/simulated/vr_logs.csv",
        "data/processed/merged_dataset.csv",
        "data/processed/validation_results.json",
        "state/pipeline_state.yaml",
        "reports/final_report.txt"
    ]
    
    # Step 1: Run Simulation
    logger.info("--- Step 1: Generating Synthetic Data ---")
    if not run_script("MFQ Simulation", "data.simulation_mfq"):
        logger.error("MFQ Simulation failed. Aborting.")
        return False
    
    if not run_script("Stories Simulation", "data.simulation_stories"):
        logger.error("Stories Simulation failed. Aborting.")
        return False
    
    # Step 2: Run Ingestion
    logger.info("--- Step 2: Ingesting and Merging Data ---")
    if not run_script("Data Ingestion", "data.ingest"):
        logger.error("Data Ingestion failed. Aborting.")
        return False
    
    # Verify ingestion artifacts
    ingestion_files = [
        "data/simulated/mfq_data.csv",
        "data/simulated/stories_data.csv",
        "data/simulated/vr_logs.csv",
        "data/processed/merged_dataset.csv"
    ]
    success, missing = verify_artifacts(ingestion_files)
    if not success:
        logger.error(f"Missing ingestion artifacts: {missing}")
        return False
    
    # Step 3: Run Bayesian Model
    logger.info("--- Step 3: Running Bayesian Model ---")
    if not run_script("Bayesian Model", "models.bayesian"):
        logger.error("Bayesian Model execution failed. Aborting.")
        return False
    
    # Step 4: Run Validation
    logger.info("--- Step 4: Running Validation Pipeline ---")
    if not run_script("Validation Pipeline", "analysis.validation"):
        logger.error("Validation Pipeline failed. Aborting.")
        return False
    
    # Step 5: Validate Checksums
    logger.info("--- Step 5: Validating Checksums ---")
    if not validate_checksums():
        logger.error("Checksum validation failed. Aborting.")
        return False
    
    # Step 6: Generate Report
    logger.info("--- Step 6: Generating Final Report ---")
    if not run_script("Report Generation", "reports.generate_report"):
        logger.error("Report Generation failed. Aborting.")
        return False
    
    # Final Verification
    logger.info("--- Final Verification ---")
    success, missing = verify_artifacts(expected_artifacts)
    if not success:
        logger.error(f"Final verification failed. Missing: {missing}")
        return False
    
    logger.info("=== Quickstart Validation PASSED ===")
    print("Quickstart Validation PASSED: All artifacts generated and checksummed.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)