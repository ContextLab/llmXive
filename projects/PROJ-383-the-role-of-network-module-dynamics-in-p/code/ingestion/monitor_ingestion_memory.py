"""
Script to run the ingestion pipeline with memory monitoring.
Integrates psutil peak RSS checks to verify the ≤7GB constraint (FR-010).
"""
import sys
import os
import logging
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from utils.memory_monitor import (
    get_peak_rss_bytes,
    reset_peak_rss,
    get_memory_usage_report,
    memory_guard,
    MEMORY_LIMIT_BYTES,
)
from ingestion.consolidate_data import main as run_consolidation
from utils.logging_config import setup_logging

def main():
    """
    Execute the ingestion pipeline with memory monitoring.
    Wraps the consolidation process in a memory guard to enforce the 7GB limit.
    """
    # Setup logging
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "ingestion_memory_monitor.log"
    logger = setup_logging(log_file=log_file)

    logger.info("Starting ingestion pipeline with memory monitoring (FR-010)")
    logger.info(f"Memory limit set to: {MEMORY_LIMIT_BYTES / (1024**3):.2f} GB")

    reset_peak_rss()

    try:
        # Run the consolidation pipeline within the memory guard
        # This ensures that if memory usage exceeds 7GB, a MemoryError is raised
        with memory_guard(limit_bytes=MEMORY_LIMIT_BYTES):
            logger.info("Running data consolidation...")
            run_consolidation()
            logger.info("Data consolidation completed successfully.")

        # Final check
        final_report = get_memory_usage_report()
        logger.info(f"Peak memory usage: {final_report['peak_rss_gb']:.2f} GB")
        logger.info(f"Final memory status: {'Within Limit' if final_report['within_limit'] else 'Exceeded Limit'}")

        # Save report to results
        results_dir = project_root / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        report_path = results_dir / "memory_monitor_report.json"

        with open(report_path, "w") as f:
            json.dump(final_report, f, indent=2)

        logger.info(f"Memory report saved to: {report_path}")

    except MemoryError as e:
        logger.error(f"Memory limit exceeded during ingestion: {e}")
        # Save failure report
        report = get_memory_usage_report()
        report["error"] = str(e)
        results_dir = project_root / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        report_path = results_dir / "memory_monitor_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()
