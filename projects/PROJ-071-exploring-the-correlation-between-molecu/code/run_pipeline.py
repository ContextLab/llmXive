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

def run_pipeline():
    """Execute the full pipeline stages."""
    start_time = time.time()
    status = "PASS"
    error_msg = None

    try:
        # 1. Setup
        ensure_directories()

        # 2. Ingest (US1)
        logger.info("Stage 1: Ingest (T012)")
        try:
            ingest_main()
        except Exception as e:
            logger.error(f"Ingest stage failed: {e}")
            log_pipeline_failure("Ingest", str(e))
            # Check if gate status was created (might have failed gracefully)
            gate_file = PROJECT_ROOT / "data" / "gate_status.json"
            if not gate_file.exists():
                raise DataIngestionError(f"Ingest failed without creating gate status: {e}")

        # Check gate status to decide if we continue
        gate_file = PROJECT_ROOT / "data" / "gate_status.json"
        if gate_file.exists():
            with open(gate_file, "r") as f:
                gate_data = json.load(f)
            if gate_data.get("status") == "FAIL":
                logger.warning("Data Availability Gate Failed. Stopping pipeline.")
                # Still need to generate reports for failure, so we continue to report generation
        else:
            logger.warning("Gate status file not found after ingest. Assuming fail.")
            status = "FAIL"
            error_msg = "Gate status file missing after ingest"

        # 3. Descriptors (US1)
        logger.info("Stage 2: Descriptors (T014)")
        try:
            descriptors_main()
        except Exception as e:
            logger.error(f"Descriptors stage failed: {e}")
            log_pipeline_failure("Descriptors", str(e))
            # Continue to allow downstream failure handling

        # 4. Standardize (US2)
        logger.info("Stage 3: Standardize (T020)")
        try:
            standardize_main()
        except StatisticalInsufficiencyError as e:
            logger.warning(f"Statistical Gate Failed: {e}")
            log_pipeline_failure("Standardize", str(e))
            # Continue to generate failure artifacts if needed
        except Exception as e:
            logger.error(f"Standardize stage failed: {e}")
            log_pipeline_failure("Standardize", str(e))

        # 5. Analysis (US2)
        logger.info("Stage 4: Analysis (T026)")
        try:
            analysis_main()
        except Exception as e:
            logger.error(f"Analysis stage failed: {e}")
            log_pipeline_failure("Analysis", str(e))

        # 6. Visualization (US3)
        logger.info("Stage 5: Visualization (T032, T033)")
        try:
            viz_main()
        except Exception as e:
            logger.error(f"Visualization stage failed: {e}")
            log_pipeline_failure("Visualization", str(e))

        # 7. Report (US3)
        logger.info("Stage 6: Report (T034, T035)")
        try:
            report_main()
        except Exception as e:
            logger.error(f"Report stage failed: {e}")
            log_pipeline_failure("Report", str(e))

        # 8. Verification (T036)
        logger.info("Stage 7: Verification (T036)")
        try:
            verify_main()
        except Exception as e:
            logger.error(f"Verification stage failed: {e}")
            log_pipeline_failure("Verification", str(e))

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
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Pipeline completed. Status: {status}, Duration: {duration:.2f}s")
    return status

def main():
    run_pipeline()

if __name__ == '__main__':
    main()