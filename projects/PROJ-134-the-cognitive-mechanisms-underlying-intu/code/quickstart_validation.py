import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import existing hashing utilities
from utils.hashing import calculate_sha256, update_state_yaml, verify_artifact, checksum_derived_datasets, main as hash_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the execution order based on tasks.md dependencies
SCRIPTS_TO_RUN = [
    "code/setup_directories.py",
    "code/setup_subdirectories.py",
    "code/data/simulation_mfq.py",
    "code/data/simulation_stories.py",
    "code/data/ingest.py",
    "code/data/preprocess.py",
    "code/models/bayesian.py",
    "code/models/regression.py",
    "code/analysis/validation.py",
    "code/analysis/model_comparison.py",
    "code/reports/generate_report.py"
]

def run_script(script_path: str) -> Tuple[bool, str]:
    """
    Executes a Python script and returns success status and output/error.
    """
    logger.info(f"Executing script: {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=3600, # 1 hour timeout per script
            check=True
        )
        if result.returncode == 0:
            logger.info(f"Script {script_path} completed successfully.")
            return True, result.stdout
        else:
            logger.error(f"Script {script_path} failed with return code {result.returncode}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_path} timed out.")
        return False, "Timeout expired"
    except Exception as e:
        logger.error(f"Error running {script_path}: {str(e)}")
        return False, str(e)

def verify_artifacts(expected_outputs: List[str]) -> Dict[str, bool]:
    """
    Verifies that expected output files exist in the filesystem.
    """
    results = {}
    for path in expected_outputs:
        full_path = Path(path)
        exists = full_path.exists()
        results[path] = exists
        if exists:
            logger.info(f"Artifact found: {path}")
        else:
            logger.warning(f"Artifact missing: {path}")
    return results

def validate_checksums(state_file: str = "state/checksums.yaml") -> bool:
    """
    Validates that the state file exists and contains checksums for derived datasets.
    """
    state_path = Path(state_file)
    if not state_path.exists():
        logger.error(f"State file {state_file} does not exist.")
        return False

    # Run the checksumming utility to ensure state is updated and valid
    # This function reads the state, verifies existing checksums, and updates if needed
    try:
        # We call the main function of hashing module which handles state updates
        # Note: We are calling it directly here to ensure the state is consistent
        # after the pipeline run.
        checksum_derived_datasets()
        
        # Verify the state file now contains entries
        import yaml
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        
        if not state_data or 'artifacts' not in state_data:
            logger.error("State file exists but contains no artifact checksums.")
            return False
        
        logger.info(f"Validated checksums in {state_file}: {len(state_data.get('artifacts', {}))} entries.")
        return True
    except Exception as e:
        logger.error(f"Error validating checksums: {str(e)}")
        return False

def main():
    """
    Main entry point for quickstart validation.
    1. Runs all pipeline scripts in order.
    2. Verifies expected output artifacts exist.
    3. Validates checksums in state file.
    """
    logger.info("Starting Quickstart Validation Pipeline (T040)")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    all_success = True
    
    # 1. Run Scripts
    for script in SCRIPTS_TO_RUN:
        success, output = run_script(script)
        if not success:
            all_success = False
            logger.error(f"Pipeline halted due to failure in {script}")
            # We continue to log, but the final verdict will be failure
            # In a strict pipeline, we might exit here.
            # For validation, we report all failures.
    
    if not all_success:
        logger.error("Pipeline execution failed. Check logs for details.")
        print("VALIDATION FAILED: Pipeline execution errors detected.")
        return 1

    # 2. Verify Artifacts
    # Based on the pipeline, these are the expected outputs
    expected_artifacts = [
        "data/raw/mfq_data.csv",
        "data/raw/stories_data.csv",
        "data/raw/vr_logs.csv",
        "data/processed/merged_data.csv",
        "data/processed/preprocessed_data.csv",
        "reports/validation_results.json",
        "reports/final_report.txt",
        "state/checksums.yaml"
    ]
    
    artifact_status = verify_artifacts(expected_artifacts)
    missing_artifacts = [k for k, v in artifact_status.items() if not v]
    
    if missing_artifacts:
        logger.error(f"Missing expected artifacts: {missing_artifacts}")
        all_success = False
    
    # 3. Validate Checksums
    checksum_valid = validate_checksums()
    if not checksum_valid:
        logger.error("Checksum validation failed.")
        all_success = False

    # Final Verdict
    if all_success:
        logger.info("Quickstart Validation PASSED: All scripts ran, artifacts present, checksums valid.")
        print("VALIDATION PASSED: All checks successful.")
        return 0
    else:
        logger.error("Quickstart Validation FAILED.")
        print("VALIDATION FAILED: See logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())