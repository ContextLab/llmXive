import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Import pipeline phases from existing modules
from data.validate_metadata import main as validate_metadata_main
from data.filter_subjects import main as filter_subjects_main
from data.download import main as download_main
from data.preprocess import main as preprocess_main
from analysis.metrics import main as metrics_main
from analysis.output_metrics import main as output_metrics_main
from analysis.stats import main as stats_main
from analysis.plot_results import main as plot_results_main
from analysis.ensure_null_reporting import main as ensure_null_reporting_main
from utils.memory_monitor import MemoryMonitor, check_memory_limit

# Configuration constants
MAX_RUNTIME_SECONDS = 4 * 3600  # 4 hours in seconds
RESULTS_DIR = Path("results")
RUNTIME_LOG_PATH = RESULTS_DIR / "runtime_log.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)

def get_phase_timer(phase_name: str):
    """Context manager to time a specific phase."""
    class PhaseTimer:
        def __init__(self, name):
            self.name = name
            self.start_time = None
            self.end_time = None
            self.duration = None

        def __enter__(self):
            self.start_time = time.time()
            logger.info(f"Starting phase: {self.name}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            logger.info(f"Completed phase: {self.name} in {self.duration:.2f} seconds")
            if exc_type:
                logger.error(f"Phase {self.name} failed with error: {exc_val}")
            return False

    return PhaseTimer(phase_name)

def run_pipeline():
    """
    Execute the full research pipeline with runtime verification.
    Raises RuntimeError if total runtime exceeds 4 hours.
    """
    start_time = time.time()
    phases = []
    success = True
    error_message = None

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Phase 1: Metadata Validation
        with get_phase_timer("Metadata Validation") as timer:
            validate_metadata_main()
        phases.append({"phase": "Metadata Validation", "duration_seconds": timer.duration, "status": "success"})

        # Phase 2: Subject Filtering
        with get_phase_timer("Subject Filtering") as timer:
            filter_subjects_main()
        phases.append({"phase": "Subject Filtering", "duration_seconds": timer.duration, "status": "success"})

        # Phase 3: Data Download
        with get_phase_timer("Data Download") as timer:
            download_main()
        phases.append({"phase": "Data Download", "duration_seconds": timer.duration, "status": "success"})

        # Phase 4: Preprocessing
        with get_phase_timer("Preprocessing") as timer:
            preprocess_main()
        phases.append({"phase": "Preprocessing", "duration_seconds": timer.duration, "status": "success"})

        # Phase 5: Metric Extraction
        with get_phase_timer("Metric Extraction") as timer:
            metrics_main()
        phases.append({"phase": "Metric Extraction", "duration_seconds": timer.duration, "status": "success"})

        # Phase 6: Output Metrics
        with get_phase_timer("Output Metrics") as timer:
            output_metrics_main()
        phases.append({"phase": "Output Metrics", "duration_seconds": timer.duration, "status": "success"})

        # Phase 7: Statistical Analysis
        with get_phase_timer("Statistical Analysis") as timer:
            stats_main()
        phases.append({"phase": "Statistical Analysis", "duration_seconds": timer.duration, "status": "success"})

        # Phase 8: Plot Generation
        with get_phase_timer("Plot Generation") as timer:
            plot_results_main()
        phases.append({"phase": "Plot Generation", "duration_seconds": timer.duration, "status": "success"})

        # Phase 9: Null Result Reporting
        with get_phase_timer("Null Result Reporting") as timer:
            ensure_null_reporting_main()
        phases.append({"phase": "Null Result Reporting", "duration_seconds": timer.duration, "status": "success"})

    except Exception as e:
        success = False
        error_message = str(e)
        logger.error(f"Pipeline failed at phase: {e}")
        traceback.print_exc()

    end_time = time.time()
    total_duration = end_time - start_time

    # Runtime Verification (T049)
    runtime_log = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
        "total_duration_seconds": total_duration,
        "max_allowed_seconds": MAX_RUNTIME_SECONDS,
        "status": "success" if success else "failed",
        "error": error_message,
        "phases": phases
    }

    # Write runtime log
    with open(RUNTIME_LOG_PATH, 'w') as f:
        json.dump(runtime_log, f, indent=2)

    logger.info(f"Total pipeline runtime: {total_duration:.2f} seconds")

    # Raise RuntimeError if limit exceeded
    if total_duration > MAX_RUNTIME_SECONDS:
        error_msg = f"Pipeline execution exceeded the 4-hour limit. Total runtime: {total_duration:.2f} seconds (Limit: {MAX_RUNTIME_SECONDS} seconds)."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    if not success:
        raise RuntimeError(f"Pipeline execution failed: {error_message}")

    return runtime_log

def main():
    """Entry point for the pipeline."""
    try:
        result = run_pipeline()
        print(f"Pipeline completed successfully. Results logged to {RUNTIME_LOG_PATH}")
        return 0
    except RuntimeError as e:
        print(f"Runtime Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())