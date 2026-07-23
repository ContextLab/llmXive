"""
T009: Create results directory structure for figures and reports.

Implements FR-006 and Plan: Project Structure by creating:
- results/figures/
- results/reports/

This task ensures the output directories exist before any visualization
or report generation logic runs.
"""
import os
import sys
import logging

from utils import get_logger, set_task_id, get_task_id

def ensure_results_directories():
    """
    Create the results directory structure if it does not exist.
    
    Creates:
    - results/figures/
    - results/reports/
    
    Returns:
        bool: True if directories were created or already existed, False on error.
    """
    task_id = get_task_id()
    logger = get_logger()
    
    base_dir = "results"
    sub_dirs = ["figures", "reports"]
    
    created_any = False
    
    for sub_dir in sub_dirs:
        full_path = os.path.join(base_dir, sub_dir)
        
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"[{task_id}] Created directory: {full_path}")
                created_any = True
            except OSError as e:
                logger.error(f"[{task_id}] Failed to create directory {full_path}: {e}")
                return False
        else:
            logger.debug(f"[{task_id}] Directory already exists: {full_path}")
    
    if created_any:
        logger.info(f"[{task_id}] Results directory structure ensured.")
    else:
        logger.info(f"[{task_id}] Results directory structure already present.")
        
    return True

def main():
    """
    Entry point for T009 execution.
    
    Sets up logging, initializes the task ID, and ensures the results
    directory structure exists.
    """
    set_task_id("T009")
    setup_logging()
    logger = get_logger()
    
    logger.info("Starting T009: Create results directory structure")
    
    success = ensure_results_directories()
    
    if success:
        logger.info("T009 completed successfully")
        sys.exit(0)
    else:
        logger.error("T009 failed to create directory structure")
        sys.exit(1)

if __name__ == "__main__":
    main()