"""
Phase 0 Orchestration Script - Task T000-run

Executes the Phase 0 tasks in the correct order to ensure data artifacts
are generated before T006 (Pre-Ingestion Validation Gate) checks them.

Order of execution:
1. T000: Download Moral Machine Dataset
2. T001a, T001b, T001c: Validation (Sources, ERA5 Sample, ERA5 Citation)
3. T002a, T002c, T002d, T002e: ERA5 Fetch & Checksums
4. T003, T004: Sample Validation & Checksums
5. T006: Pre-Ingestion Validation Gate

If any step fails, halts and reports the specific failure.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger

logger = get_data_quality_logger()

def run_task(task_name: str, module_name: str, func_name: str = "main"):
    """
    Dynamically import and run a task module's main function.
    """
    logger.info(f"--- Executing {task_name} ---")
    try:
        module = __import__(module_name, fromlist=[func_name])
        main_func = getattr(module, func_name)
        main_func()
        logger.info(f"--- {task_name} completed successfully ---")
        return True
    except Exception as e:
        logger.error(f"--- {task_name} FAILED: {e} ---")
        return False

def main():
    """Orchestrate Phase 0 tasks."""
    logger.info("=" * 60)
    logger.info("Starting Phase 0 Orchestration (T000-run)")
    logger.info("=" * 60)

    tasks = [
        ("T000: Download Moral Machine", "download_moral_machine"),
        ("T001a: Validate Moral Machine Source", "validate_sources"),
        ("T001b: Validate ERA5 Sample", "validate_era5"),
        ("T001c: Validate ERA5 Citation", "validate_sources"), # Reuses validate_sources for metadata
        ("T002a: Define Bounding Box", "define_bbox"),
        ("T002c: Fetch ERA5 Full (Streamed)", "fetch_era_full"),
        ("T002d: Stream & Save ERA5 Chunks", "stream_era5"),
        ("T002e: Checksum Full ERA5", "update_state_checksum_era5_full"),
        ("T003: Checksum ERA5 Sample", "update_state_checksum_sample"),
        ("T004: Validate ERA5 Sample Integrity", "validate_era5_sample_integrity"),
        ("T006: Pre-Ingestion Validation Gate", "pre_ingestion_validation_gate"),
    ]

    failed_tasks = []

    for task_name, module_name in tasks:
        if not run_task(task_name, module_name):
            failed_tasks.append(task_name)
            logger.error(f"Stopping orchestration due to failure in {task_name}")
            break

    if failed_tasks:
        logger.error("=" * 60)
        logger.error(f"PHASE 0 FAILED. Failed tasks: {', '.join(failed_tasks)}")
        logger.error("=" * 60)
        sys.exit(1)
    else:
        logger.info("=" * 60)
        logger.info("PHASE 0 COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()
