"""
Task T044: Run quickstart.md validation to ensure end-to-end reproducibility.

This script orchestrates the full pipeline execution as described in quickstart.md,
verifying that all stages run successfully and produce the expected output artifacts.
It acts as a validation runner for the entire research pipeline.
"""
import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / "code"
data_dir = project_root / "data"
results_dir = project_root / "results"
logs_dir = project_root / "logs"

# Ensure directories exist
data_dir.mkdir(parents=True, exist_ok=True)
results_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logs_dir / "quickstart_validation.log")
    ]
)
logger = logging.getLogger(__name__)

# Define expected outputs based on quickstart.md and task descriptions
EXPECTED_OUTPUTS = [
    "data/processed/merged_data.csv",
    "data/phylogeny/tree.nwk",
    "results/model_summary.csv",
    "results/sensitivity_log.csv",
    "results/association_forest.png",
    "results/moderator_plot.png"
]

# Define the pipeline steps in order
PIPELINE_STEPS = [
    {
        "name": "00_init_config",
        "module": "00_init_config",
        "description": "Initialize configuration and environment"
    },
    {
        "name": "01_discover_data",
        "module": "01_discover_data",
        "description": "Query Dryad API and extract dataset IDs"
    },
    {
        "name": "02_ingest_data",
        "module": "02_ingest_data",
        "description": "Download raw CSVs from Dryad and AnAge"
    },
    {
        "name": "03_clean_merge",
        "module": "03_clean_merge",
        "description": "Filter, convert units, and merge data"
    },
    {
        "name": "04_model_pglS",
        "module": "04_model_pglS",
        "description": "Fit PGLS model and run sensitivity analysis"
    },
    {
        "name": "06_moderator",
        "module": "06_moderator",
        "description": "Fit moderator model with interaction term"
    },
    {
        "name": "05_visualize",
        "module": "05_visualize",
        "description": "Generate visualization plots"
    }
]

def run_pipeline_step(step: Dict[str, Any]) -> bool:
    """Execute a single pipeline step."""
    logger.info(f"Running step: {step['name']} - {step['description']}")
    
    try:
        # Construct the command to run the module
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{code_dir}'); "
            f"from {step['module']} import main; main()"
        ]
        
        # Execute the command
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per step
        )
        
        if result.returncode != 0:
            logger.error(f"Step {step['name']} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info(f"Step {step['name']} completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Step {step['name']} timed out")
        return False
    except Exception as e:
        logger.error(f"Step {step['name']} raised exception: {str(e)}")
        return False

def verify_outputs() -> bool:
    """Verify that all expected output files exist."""
    logger.info("Verifying output artifacts...")
    missing = []
    
    for output_path in EXPECTED_OUTPUTS:
        full_path = project_root / output_path
        if not full_path.exists():
            missing.append(output_path)
            logger.warning(f"Missing expected output: {output_path}")
        else:
            logger.info(f"Found expected output: {output_path}")
    
    if missing:
        logger.error(f"Missing {len(missing)} expected output files: {missing}")
        return False
    
    logger.info("All expected outputs verified successfully")
    return True

def main():
    """Main entry point for the quickstart validation."""
    logger.info("Starting quickstart validation for PROJ-055")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Python executable: {sys.executable}")
    
    start_time = time.time()
    success = True
    
    # Run all pipeline steps
    for step in PIPELINE_STEPS:
        if not run_pipeline_step(step):
            success = False
            logger.error(f"Pipeline failed at step: {step['name']}")
            break
    
    # Verify outputs if all steps succeeded
    if success:
        if not verify_outputs():
            success = False
    
    elapsed_time = time.time() - start_time
    logger.info(f"Validation completed in {elapsed_time:.2f} seconds")
    
    if success:
        logger.info("SUCCESS: End-to-end reproducibility validated")
        return 0
    else:
        logger.error("FAILURE: Validation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())