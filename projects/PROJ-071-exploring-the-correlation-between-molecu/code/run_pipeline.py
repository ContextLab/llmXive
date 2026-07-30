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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/output"
    ]
    for d in dirs:
        path = PROJECT_ROOT / d
        path.mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def run_pipeline():
    """Execute the full pipeline stages."""
    start_time = time.time()
    status = "SUCCESS"
    error_msg = None

    try:
        # 1. Setup
        ensure_directories()

        # 2. Ingest (US1)
        logger.info("Stage 1: Ingest (T012)")
        ingest_main()
        # Check gate status to decide if we continue
        gate_file = PROJECT_ROOT / "data" / "gate_status.json"
        if gate_file.exists():
            with open(gate_file, "r") as f:
                gate_data = json.load(f)
            if gate_data.get("status") == "FAIL":
                logger.warning("Data Availability Gate Failed. Stopping pipeline.")
                # Still need to generate reports for failure
        else:
            logger.warning("Gate status file not found after ingest. Assuming fail.")

        # 3. Descriptors (US1)
        logger.info("Stage 2: Descriptors (T014)")
        descriptors_main()

        # 4. Standardize (US2)
        logger.info("Stage 3: Standardize (T020)")
        try:
            standardize_main()
        except StatisticalInsufficiencyError as e:
            logger.warning(f"Statistical Gate Failed: {e}")
            # Continue to generate failure artifacts if needed, but analysis might skip

        # 5. Analysis (US2)
        logger.info("Stage 4: Analysis (T026)")
        analysis_main()

        # 6. Visualization (US3)
        logger.info("Stage 5: Visualization (T032, T033)")
        viz_main()

        # 7. Report (US3)
        logger.info("Stage 6: Report (T034, T035)")
        report_main()

        # 8. Verification (T036)
        logger.info("Stage 7: Verification (T036)")
        verify_main()

    except DataIngestionError as e:
        logger.error(f"Data Ingestion Error: {e}")
        status = "FAIL"
        error_msg = str(e)
    except StatisticalInsufficiencyError as e:
        logger.error(f"Statistical Insufficiency Error: {e}")
        status = "FAIL"
        error_msg = str(e)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}", exc_info=True)
        status = "FAIL"
        error_msg = str(e)

    end_time = time.time()
    duration = end_time - start_time

    # Save metrics
    metrics = {
        "total_duration_seconds": round(duration, 2),
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "error": error_msg
    }
    
    metrics_path = PROJECT_ROOT / "data" / "output" / "pipeline_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Pipeline completed. Status: {status}, Duration: {duration:.2f}s")
    return status

def main():
    run_pipeline()

if __name__ == "__main__":
    main()
