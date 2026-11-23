"""
Master script to execute the full pipeline (US1 -> US2 -> US3).
Orchestrates:
1. Ingest (T012)
2. Descriptors (T014)
3. Standardize (T020)
4. Analysis (T023, T024, T025, T026)
5. Viz (T032, T033)
6. Report (T034, T035, T035b)
7. Verification (T036)

T082: Implements strict exit code verification for every sub-module.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories
from ingest import main as ingest_main
from descriptors import main as descriptors_main
from standardize import main as standardize_main
from analysis import main as analysis_main
from viz import main as viz_main
from report import main as report_main
from verify_outputs import main as verify_main
from error_handlers import DataIngestionError, StatisticalInsufficiencyError
from logging_config import log_pipeline_failure

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_stage(stage_name: str, func):
    """
    Execute a stage function and verify its exit code (return value).
    T082 Requirement: If any sub-module returns a non-zero exit code (or raises),
    the master script must immediately halt, log the specific error, and NOT proceed.
    """
    logger.info(f"Executing {stage_name}...")
    try:
        result = func()
        # Check for explicit non-zero return codes if the function returns one
        if result is not None and result != 0:
            error_msg = f"{stage_name} returned non-zero exit code: {result}"
            logger.error(error_msg)
            log_pipeline_failure(stage_name, error_msg)
            return False
        return True
    except SystemExit as e:
        # Handle explicit sys.exit() calls within the stage
        code = e.code if isinstance(e.code, int) else 1
        error_msg = f"{stage_name} exited with code {code}"
        logger.error(error_msg)
        log_pipeline_failure(stage_name, error_msg)
        return False
    except Exception as e:
        error_msg = f"{stage_name} failed with exception: {e}"
        logger.error(error_msg)
        log_pipeline_failure(stage_name, error_msg)
        return False

def run_pipeline():
    """Execute the full pipeline stages with strict exit code verification."""
    start_time = time.time()
    status = "PASS"
    error_msg = None

    try:
        # 1. Setup
        ensure_directories()

        # 2. Ingest (US1) - T082 Verification
        if not run_stage("Ingest (T012)", ingest_main):
            # T082: Immediate halt on failure
            logger.error("Pipeline halted due to Ingest failure.")
            status = "FAIL"
            error_msg = "Ingest stage failed"
            # Even on failure, we might need to generate reports, but we stop the main flow
            # We proceed to Report stage to handle the failure state gracefully if needed,
            # but we skip downstream processing steps.
        
        # Check gate status to decide if we continue processing
        gate_file = PROJECT_ROOT / "data" / "gate_status.json"
        gate_failed = False
        if gate_file.exists():
            try:
                with open(gate_file, "r") as f:
                    gate_data = json.load(f)
                if gate_data.get("status") == "FAIL":
                    logger.warning("Data Availability Gate Failed. Stopping processing pipeline.")
                    gate_failed = True
            except Exception as e:
                logger.error(f"Could not read gate status: {e}")
                gate_failed = True
        else:
            logger.warning("Gate status file not found after ingest. Assuming fail.")
            gate_failed = True

        if gate_failed and status != "FAIL":
            status = "FAIL"
            error_msg = "Data Availability Gate Failed"

        # 3. Descriptors (US1) - Only run if we haven't failed yet
        if status == "PASS":
            if not run_stage("Descriptors (T014)", descriptors_main):
                logger.error("Pipeline halted due to Descriptors failure.")
                status = "FAIL"
                error_msg = "Descriptors stage failed"
        
        # 4. Standardize (US2) - Only run if we haven't failed yet
        if status == "PASS":
            if not run_stage("Standardize (T020)", standardize_main):
                logger.error("Pipeline halted due to Standardize failure.")
                status = "FAIL"
                error_msg = "Standardize stage failed"
        
        # 5. Analysis (US2) - Only run if we haven't failed yet
        if status == "PASS":
            if not run_stage("Analysis (T026)", analysis_main):
                logger.error("Pipeline halted due to Analysis failure.")
                status = "FAIL"
                error_msg = "Analysis stage failed"
        
        # 6. Visualization (US3) - Only run if we haven't failed yet
        if status == "PASS":
            if not run_stage("Visualization (T032, T033)", viz_main):
                logger.error("Pipeline halted due to Visualization failure.")
                status = "FAIL"
                error_msg = "Visualization stage failed"
        
        # 7. Report (US3) - Always attempt to run to generate failure reports if needed
        # But if we failed earlier, we might just generate the insufficiency report
        logger.info("Executing Report (T034, T035)...")
        if not run_stage("Report (T034, T035)", report_main):
            logger.error("Pipeline halted due to Report failure.")
            # We don't necessarily set status=FAIL here if the report generation is the last step,
            # but T082 says halt and log. We log the failure.
            if status == "PASS":
                status = "FAIL"
                error_msg = "Report stage failed"

        # 8. Verification (T036) - Only run if we are still passing
        if status == "PASS":
            logger.info("Executing Verification (T036)...")
            if not run_stage("Verification (T036)", verify_main):
                logger.error("Pipeline halted due to Verification failure.")
                status = "FAIL"
                error_msg = "Verification stage failed"

    except DataIngestionError as e:
        logger.error(f"Data Ingestion Error: {e}")
        status = "FAIL"
        error_msg = str(e)
        log_pipeline_failure("Pipeline", str(e))
    except StatisticalInsufficiencyError as e:
        logger.error(f"Statistical Insufficiency Error: {e}")
        status = "FAIL"
        error_msg = str(e)
        log_pipeline_failure("Pipeline", str(e))
    except Exception as e:
        logger.error(f"Unexpected Error: {e}", exc_info=True)
        status = "FAIL"
        error_msg = str(e)
        log_pipeline_failure("Pipeline", str(e))

    end_time = time.time()
    duration = end_time - start_time

    # Save metrics
    metrics = {
        "total_duration_seconds": round(duration, 2),
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "error_message": error_msg
    }

    metrics_path = PROJECT_ROOT / "data" / "output" / "pipeline_metrics.json"
    # Ensure directory exists
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Pipeline completed. Status: {status}, Duration: {duration:.2f}s")
    
    # T082: Return non-zero exit code if the pipeline failed
    if status == "FAIL":
        return 1
    return 0

def main():
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()