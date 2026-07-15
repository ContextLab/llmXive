"""
Main entry point for the Ductility Prediction Pipeline.
Orchestrates the end-to-end execution of data acquisition, cleaning,
modeling, and reporting stages, with timing and budget enforcement.
"""
import os
import sys
import time
import logging
import json
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-224-predicting-the-ductility-of-additively-m"

# Ensure output directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Stage definitions
STAGES = [
    {
        "name": "setup_directories",
        "script": "code/setup_directories.py",
        "description": "Initialize project directory structure",
        "required": True
    },
    {
        "name": "data_acquisition",
        "script": "code/data/acquisition.py",
        "description": "Fetch data from primary and secondary sources",
        "required": True
    },
    {
        "name": "data_cleaning",
        "script": "code/data/cleaning.py",
        "description": "Clean, unit-convert, and filter data",
        "required": True
    },
    {
        "name": "data_versioning",
        "script": "code/data/version_artifact.py",
        "description": "Version the curated dataset artifact",
        "required": True
    },
    {
        "name": "preprocessing",
        "script": "code/data/preprocessing.py",
        "description": "Feature engineering and VIF analysis",
        "required": True
    },
    {
        "name": "lme_modeling",
        "script": "code/models/lme_model.py",
        "description": "Fit Linear Mixed-Effects model",
        "required": True
    },
    {
        "name": "save_lme_artifact",
        "script": "code/models/save_lme_artifact.py",
        "description": "Save LME results to JSON",
        "required": True
    },
    {
        "name": "sensitivity_analysis",
        "script": "code/analysis/sensitivity.py",
        "description": "Compute partial R2 and likelihood ratio tests",
        "required": True
    },
    {
        "name": "xgboost_training",
        "script": "code/models/xgboost_model.py",
        "description": "Train XGBoost model and compare with LME",
        "required": True
    },
    {
        "name": "save_predictive_artifact",
        "script": "code/models/save_predictive_artifact.py",
        "description": "Save predictive model artifact",
        "required": True
    },
    {
        "name": "reporting",
        "script": "code/analysis/reporting.py",
        "description": "Generate final report",
        "required": True
    }
]

def check_budget(start_time: float, budget_seconds: int) -> bool:
    """Check if execution time is within budget."""
    elapsed = time.time() - start_time
    return elapsed <= budget_seconds

def run_stage(stage: dict, start_time: float, budget_seconds: int) -> dict:
    """Run a single stage script and return timing/result."""
    script_path = PROJECT_ROOT / stage["script"]
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return {
            "stage": stage["name"],
            "status": "failed",
            "error": f"Script not found: {script_path}",
            "duration": 0
        }

    if not check_budget(start_time, budget_seconds):
        logger.error(f"Budget exceeded before starting {stage['name']}")
        return {
            "stage": stage["name"],
            "status": "skipped",
            "error": "Budget exceeded",
            "duration": 0
        }

    logger.info(f"Starting stage: {stage['name']} - {stage['description']}")
    stage_start = time.time()
    try:
        # Run the script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 min per stage max
        )
        duration = time.time() - stage_start

        if result.returncode != 0:
            logger.error(f"Stage {stage['name']} failed with code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return {
                "stage": stage["name"],
                "status": "failed",
                "error": f"Exit code {result.returncode}: {result.stderr[:500]}",
                "duration": duration
            }

        logger.info(f"Stage {stage['name']} completed in {duration:.2f}s")
        return {
            "stage": stage["name"],
            "status": "success",
            "duration": duration
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - stage_start
        logger.error(f"Stage {stage['name']} timed out after 300s")
        return {
            "stage": stage["name"],
            "status": "failed",
            "error": "Timeout (300s)",
            "duration": duration
        }
    except Exception as e:
        duration = time.time() - stage_start
        logger.error(f"Stage {stage['name']} raised exception: {e}")
        return {
            "stage": stage["name"],
            "status": "failed",
            "error": str(e),
            "duration": duration
        }

def main():
    parser = argparse.ArgumentParser(description="Run the full ductility prediction pipeline.")
    parser.add_argument("--timing", action="store_true", help="Output timing breakdown to JSON")
    parser.add_argument("--budget", type=int, default=600, help="Execution budget in seconds")
    args = parser.parse_args()

    logger.info(f"Starting pipeline execution with budget: {args.budget}s")
    start_time = time.time()
    results = []
    all_success = True

    for stage in STAGES:
        result = run_stage(stage, start_time, args.budget)
        results.append(result)
        if result["status"] != "success":
            if stage["required"]:
                all_success = False
                logger.critical(f"Required stage {stage['name']} failed. Aborting.")
                break
            else:
                logger.warning(f"Non-required stage {stage['name']} failed. Continuing.")

    total_duration = time.time() - start_time
    logger.info(f"Pipeline execution finished in {total_duration:.2f}s")

    # Save timing results
    timing_output = {
        "total_duration": total_duration,
        "budget_seconds": args.budget,
        "within_budget": total_duration <= args.budget,
        "stages": results
    }

    output_path = DATA_DIR / "validation" / "pipeline_timing.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(timing_output, f, indent=2)
    logger.info(f"Timing results saved to {output_path}")

    if args.timing:
        print(json.dumps(timing_output, indent=2))

    if not all_success:
        logger.error("Pipeline failed due to required stage failure.")
        sys.exit(1)

    if total_duration > args.budget:
        logger.error(f"Pipeline exceeded budget ({total_duration:.2f}s > {args.budget}s)")
        sys.exit(1)

    logger.info("Pipeline completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
