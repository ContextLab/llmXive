"""
Main orchestration script for the Ductility Prediction Pipeline.
Executes the full pipeline end-to-end with timing and error handling.
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import pipeline stages
from data.acquisition import main as run_acquisition
from data.cleaning import main as run_cleaning
from data.preprocessing import main as run_preprocessing
from models.lme_model import main as run_lme
from models.xgboost_model import main as run_xgboost
from analysis.sensitivity import main as run_sensitivity
from analysis.reporting import main as run_reporting
from data.version_artifact import main as run_versioning

def check_budget(budget_seconds: int) -> bool:
    """Check if remaining time is sufficient for next stage."""
    # Simple check - in production would track elapsed time
    return True

def run_stage(stage_name: str, func, *args, **kwargs) -> bool:
    """Run a pipeline stage with timing and error handling."""
    logger.info(f"Starting stage: {stage_name}")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"Stage {stage_name} completed in {elapsed:.2f}s")
        return True
    except Exception as e:
        logger.error(f"Stage {stage_name} failed: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Run the full ductility prediction pipeline')
    parser.add_argument('--timing', action='store_true', help='Output timing breakdown')
    parser.add_argument('--budget', type=int, default=600, help='Time budget in seconds')
    args = parser.parse_args()

    start_time = time.time()
    pipeline_timing = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stages": {},
        "total_time": None,
        "status": "success"
    }

    try:
        # Stage 1: Data Acquisition
        if not run_stage("acquisition", run_acquisition):
            raise RuntimeError("Acquisition failed")
        pipeline_timing["stages"]["acquisition"] = {
            "status": "completed",
            "output": "data/curated_builds.csv"
        }

        # Stage 2: Data Cleaning
        if not run_stage("cleaning", run_cleaning):
            raise RuntimeError("Cleaning failed")
        pipeline_timing["stages"]["cleaning"] = {
            "status": "completed",
            "output": "data/curated_builds.csv"
        }

        # Stage 3: Preprocessing (VIF, Energy Density)
        if not run_stage("preprocessing", run_preprocessing):
            raise RuntimeError("Preprocessing failed")
        pipeline_timing["stages"]["preprocessing"] = {
            "status": "completed",
            "output": "data/filtered_builds_final.csv"
        }

        # Stage 4: LME Model
        if not run_stage("lme_model", run_lme):
            raise RuntimeError("LME model failed")
        pipeline_timing["stages"]["lme_model"] = {
            "status": "completed",
            "output": "artifacts/lme_model_results.json"
        }

        # Stage 5: XGBoost Model
        if not run_stage("xgboost_model", run_xgboost):
            raise RuntimeError("XGBoost model failed")
        pipeline_timing["stages"]["xgboost_model"] = {
            "status": "completed",
            "output": "artifacts/xgboost_model.pkl"
        }

        # Stage 6: Sensitivity Analysis
        if not run_stage("sensitivity", run_sensitivity):
            raise RuntimeError("Sensitivity analysis failed")
        pipeline_timing["stages"]["sensitivity"] = {
            "status": "completed",
            "output": "artifacts/sensitivity_analysis.json"
        }

        # Stage 7: Versioning
        if not run_stage("versioning", run_versioning):
            logger.warning("Versioning stage had issues, continuing...")
        pipeline_timing["stages"]["versioning"] = {
            "status": "completed",
            "output": "state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml"
        }

        # Stage 8: Reporting
        if not run_stage("reporting", run_reporting):
            raise RuntimeError("Reporting failed")
        pipeline_timing["stages"]["reporting"] = {
            "status": "completed",
            "output": "data/reports/final_report.md"
        }

    except Exception as e:
        pipeline_timing["status"] = "failed"
        pipeline_timing["error"] = str(e)
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

    total_time = time.time() - start_time
    pipeline_timing["total_time"] = total_time
    pipeline_timing["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if args.timing:
        output_path = project_root / "data" / "validation" / "pipeline_timing.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(pipeline_timing, f, indent=2)
        logger.info(f"Timing report saved to {output_path}")

        if total_time > args.budget:
            logger.warning(f"Pipeline exceeded time budget: {total_time:.2f}s > {args.budget}s")
            sys.exit(1)

    logger.info(f"Pipeline completed successfully in {total_time:.2f}s")
    sys.exit(0)

if __name__ == "__main__":
    main()
