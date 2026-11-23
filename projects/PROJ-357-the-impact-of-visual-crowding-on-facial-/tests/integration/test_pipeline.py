"""
Integration Test: Full Pipeline Execution
This script executes the entire research pipeline end-to-end,
verifying that all stages produce the required artifacts and that
the final analysis results are consistent.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
STATE_DIR = PROJECT_ROOT / "state"

# Expected artifacts
EXPECTED_ARTIFACTS = {
    # Stimuli Generation (US1)
    "data/interim/stimuli": "directory",
    "data/interim/stimuli_manifest.json": "file",
    "data/interim/generation_errors.log": "file",
    
    # Clutter Metrics (US2)
    "data/processed/clutter_metrics.csv": "file",
    "data/processed/validation_report.json": "file",
    
    # Human Judgments (US4)
    "data/processed/human_judgments.csv": "file",
    
    # Analysis (US3)
    "data/processed/regression_results.json": "file",
    "artifacts/model_config.yaml": "file",
}

# Pipeline stages to execute
PIPELINE_STAGES = [
    {
        "name": "Verify RAVDESS Source",
        "script": "utils/verify_ravdess.py",
        "args": []
    },
    {
        "name": "Download RAVDESS Dataset",
        "script": "utils/download.py",
        "args": []
    },
    {
        "name": "Extract Frames",
        "script": "utils/frame_extractor.py",
        "args": []
    },
    {
        "name": "Generate Stimuli",
        "script": "utils/stimulus_gen.py",
        "args": []
    },
    {
        "name": "Generate Stimuli Manifest",
        "script": "utils/stimuli_manifest.py",
        "args": []
    },
    {
        "name": "Validate Manifest",
        "script": "utils/manifest_validator.py",
        "args": []
    },
    {
        "name": "Compute Clutter Metrics",
        "script": "utils/clutter_metrics.py",
        "args": []
    },
    {
        "name": "Generate Synthetic Pilot Data",
        "script": "analysis/pilot_runner.py",
        "args": []
    },
    {
        "name": "Aggregate Judgments",
        "script": "analysis/aggregate_judgments.py",
        "args": []
    },
    {
        "name": "Fit GLMM Model",
        "script": "analysis/glmm_model.py",
        "args": []
    },
    {
        "name": "Write Regression Results",
        "script": "analysis/write_regression_results.py",
        "args": []
    },
    {
        "name": "Generate Report",
        "script": "analysis/reporting.py",
        "args": []
    },
    {
        "name": "Update State Hygiene",
        "script": "utils/hygiene.py",
        "args": []
    }
]

def run_command(cmd: List[str], cwd: Path = None, timeout: int = 300) -> bool:
    """Run a command and return True if it succeeds."""
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Command succeeded: {' '.join(cmd)}")
            return True
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
        return False
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return False

def verify_artifacts() -> Dict[str, bool]:
    """Verify that all expected artifacts exist."""
    results = {}
    
    for artifact_path, artifact_type in EXPECTED_ARTIFACTS.items():
        full_path = PROJECT_ROOT / artifact_path
        
        if artifact_type == "directory":
            exists = full_path.exists() and full_path.is_dir()
            if exists:
                # Check if directory is not empty
                try:
                    files = list(full_path.iterdir())
                    exists = len(files) > 0
                except PermissionError:
                    exists = False
        else:
            exists = full_path.exists() and full_path.is_file()
        
        results[artifact_path] = exists
        
        if exists:
            logger.info(f"✓ Artifact exists: {artifact_path}")
        else:
            logger.error(f"✗ Artifact missing: {artifact_path}")
    
    return results

def verify_manifest_integrity() -> bool:
    """Verify the integrity of the stimuli manifest."""
    manifest_path = PROJECT_ROOT / "data/interim/stimuli_manifest.json"
    
    if not manifest_path.exists():
        logger.error("Manifest file does not exist")
        return False
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if not isinstance(manifest, list) or len(manifest) == 0:
            logger.error("Manifest is empty or not a list")
            return False
        
        # Check for required fields in each entry
        required_fields = ['file_path', 'emotion_label', 'flanker_count', 'eccentricity']
        for entry in manifest:
            for field in required_fields:
                if field not in entry:
                    logger.error(f"Missing required field '{field}' in manifest entry")
                    return False
        
        logger.info(f"✓ Manifest integrity verified with {len(manifest)} entries")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return False
    except Exception as e:
        logger.error(f"Error verifying manifest: {e}")
        return False

def verify_regression_results() -> bool:
    """Verify the regression results file."""
    results_path = PROJECT_ROOT / "data/processed/regression_results.json"
    
    if not results_path.exists():
        logger.error("Regression results file does not exist")
        return False
    
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Check for required fields
        required_fields = ['coefficients', 'p_values', 'confidence_intervals', 'model_type']
        for field in required_fields:
            if field not in results:
                logger.error(f"Missing required field '{field}' in regression results")
                return False
        
        # Verify FDR correction was applied
        if 'fdr_corrected' in results and results['fdr_corrected']:
            logger.info("✓ FDR correction was applied")
        
        logger.info("✓ Regression results verified")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in regression results: {e}")
        return False
    except Exception as e:
        logger.error(f"Error verifying regression results: {e}")
        return False

def run_full_pipeline() -> bool:
    """Execute the full pipeline and verify results."""
    logger.info("Starting full pipeline integration test")
    
    # Ensure directories exist
    for stage in PIPELINE_STAGES:
        script_path = CODE_DIR / stage["script"]
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
    
    # Execute each stage
    for i, stage in enumerate(PIPELINE_STAGES):
        logger.info(f"Executing stage {i+1}/{len(PIPELINE_STAGES)}: {stage['name']}")
        
        cmd = [sys.executable, str(CODE_DIR / stage["script"])] + stage["args"]
        
        if not run_command(cmd, cwd=PROJECT_ROOT):
            logger.error(f"Stage failed: {stage['name']}")
            return False
    
    return True

def main():
    """Main entry point for the integration test."""
    logger.info("=" * 60)
    logger.info("FULL PIPELINE INTEGRATION TEST")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Run the full pipeline
    pipeline_success = run_full_pipeline()
    
    if not pipeline_success:
        logger.error("Pipeline execution failed")
        print("\nINTEGRATION TEST FAILED: Pipeline execution errors")
        return 1
    
    # Verify artifacts
    logger.info("\nVerifying artifacts...")
    artifact_results = verify_artifacts()
    
    missing_artifacts = [path for path, exists in artifact_results.items() if not exists]
    if missing_artifacts:
        logger.error(f"Missing artifacts: {missing_artifacts}")
        print("\nINTEGRATION TEST FAILED: Missing artifacts")
        return 1
    
    # Verify manifest integrity
    logger.info("\nVerifying manifest integrity...")
    if not verify_manifest_integrity():
        logger.error("Manifest integrity check failed")
        print("\nINTEGRATION TEST FAILED: Manifest integrity check failed")
        return 1
    
    # Verify regression results
    logger.info("\nVerifying regression results...")
    if not verify_regression_results():
        logger.error("Regression results verification failed")
        print("\nINTEGRATION TEST FAILED: Regression results verification failed")
        return 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 60)
    logger.info("INTEGRATION TEST PASSED")
    logger.info(f"Total execution time: {duration:.2f} seconds")
    logger.info("=" * 60)
    
    print("\n✓ All pipeline stages executed successfully")
    print("✓ All expected artifacts generated")
    print("✓ Manifest integrity verified")
    print("✓ Regression results verified")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())