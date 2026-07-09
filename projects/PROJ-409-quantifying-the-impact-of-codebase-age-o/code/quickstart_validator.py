"""
Quickstart Validation Script for PROJ-409
This script validates the end-to-end execution of the pipeline as described in quickstart.md.
It runs the extraction, inference, and analysis steps (or verifies their outputs if data exists)
and ensures all required artifacts are generated.
"""
import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import get_logger, setup_logging
from utils.config import ensure_directories

logger = get_logger(__name__)

# Define expected paths based on tasks.md and quickstart.md conventions
EXPECTED_DIRS = [
    "code",
    "code/extraction",
    "code/inference",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/extracted",
    "data/aggregated",
    "data/results",
    "data/models",
    "tests/unit",
    "tests/integration",
]

EXPECTED_ARTIFACTS = {
    "extraction": [
        "data/extracted/snippets.csv",
        "data/extracted/file_metrics_raw.csv", # Intermediate if exists
    ],
    "inference": [
        "data/extracted/inference_results.csv",
        "data/aggregated/file_metrics.csv",
    ],
    "analysis": [
        "data/results/correlation_results.json",
        "data/results/final_report.md",
        "data/results/final_report.json",
    ],
}

SCRIPTS_TO_RUN = [
    {
        "name": "Extraction",
        "script": "code/extraction/run_extraction.py",
        "args": ["--repos", "https://github.com/huggingface/transformers", "--limit", "1"],
        "output_check": "data/extracted/snippets.csv",
        "timeout": 300, # 5 minutes for extraction
    },
    {
        "name": "Inference",
        "script": "code/inference/run_inference.py",
        "args": ["--input", "data/extracted/snippets.csv"],
        "output_check": "data/extracted/inference_results.csv",
        "timeout": 600, # 10 minutes for inference
    },
    {
        "name": "Analysis",
        "script": "code/analysis/correlation.py",
        "args": ["--input", "data/aggregated/file_metrics.csv"],
        "output_check": "data/results/correlation_results.json",
        "timeout": 120,
    },
    {
        "name": "Report Generation",
        "script": "code/analysis/report_generator.py",
        "args": [],
        "output_check": "data/results/final_report.md",
        "timeout": 60,
    },
]

def check_directories() -> bool:
    """Verify that the required project directory structure exists."""
    logger.info("Checking project directory structure...")
    missing = []
    for dir_path in EXPECTED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("All required directories exist.")
    return True

def check_requirements() -> bool:
    """Verify that requirements.txt exists and contains key dependencies."""
    req_file = project_root / "requirements.txt"
    if not req_file.exists():
        logger.error("requirements.txt not found.")
        return False
    
    content = req_file.read_text()
    required_pkgs = ["huggingface_hub", "transformers", "torch", "gitpython", "pandas", "scipy", "networkx"]
    missing_pkgs = [pkg for pkg in required_pkgs if pkg.lower() not in content.lower()]
    
    if missing_pkgs:
        logger.warning(f"Missing expected packages in requirements.txt: {missing_pkgs}")
        # Not a hard fail for validation if they are installed, but good to know
    else:
        logger.info("requirements.txt contains expected dependencies.")
    
    return True

def run_script_step(step: Dict[str, Any]) -> bool:
    """Execute a specific pipeline step and verify output."""
    name = step["name"]
    script_path = project_root / step["script"]
    args = step.get("args", [])
    output_check = step.get("output_check")
    timeout = step.get("timeout", 300)

    logger.info(f"Running {name} step: {script_path}")

    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)] + args
    
    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            logger.error(f"{name} failed with exit code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False
        
        logger.info(f"{name} completed in {elapsed:.2f}s")

        if output_check:
            output_path = project_root / output_check
            if not output_path.exists():
                logger.error(f"Expected output not found: {output_path}")
                return False
            
            # Basic check: file is not empty
            if output_path.stat().st_size == 0:
                logger.error(f"Output file is empty: {output_path}")
                return False
            
            logger.info(f"Verified output: {output_path}")

        return True

    except subprocess.TimeoutExpired:
        logger.error(f"{name} timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"Error running {name}: {str(e)}")
        return False

def validate_artifacts() -> bool:
    """Check that all expected final artifacts exist."""
    logger.info("Validating final artifacts...")
    all_good = True
    
    for category, files in EXPECTED_ARTIFACTS.items():
        logger.debug(f"Checking {category} artifacts...")
        for file_rel in files:
            full_path = project_root / file_rel
            if not full_path.exists():
                logger.warning(f"Missing expected artifact: {file_rel}")
                all_good = False
            else:
                logger.debug(f"Found: {file_rel}")
    
    return all_good

def main():
    setup_logging(level="INFO")
    logger.info("Starting Quickstart Validation for PROJ-409")
    
    # 1. Check Structure
    if not check_directories():
        logger.error("Directory structure validation failed.")
        return 1

    # 2. Check Requirements
    if not check_requirements():
        logger.warning("Requirements validation had issues (non-fatal).")

    # 3. Run Pipeline Steps (if data doesn't exist, or force re-run)
    # For validation, we attempt to run the pipeline. 
    # Note: In a real CI/CD, we might skip if data exists, but for T030 
    # we want to ensure the scripts actually run and produce output.
    # We will attempt to run them. If they fail due to missing data (e.g. no snippets yet),
    # we treat that as a validation failure of the pipeline logic.
    
    success_count = 0
    for step in SCRIPTS_TO_RUN:
        if run_script_step(step):
            success_count += 1
        else:
            # If a step fails, subsequent steps might also fail due to missing input
            # We continue to log, but we know the pipeline is broken.
            pass

    # 4. Final Artifact Check
    if not validate_artifacts():
        logger.error("Final artifact validation failed.")
        return 1

    logger.info(f"Quickstart validation completed. {success_count}/{len(SCRIPTS_TO_RUN)} steps successful.")
    return 0 if success_count == len(SCRIPTS_TO_RUN) else 1

if __name__ == "__main__":
    sys.exit(main())