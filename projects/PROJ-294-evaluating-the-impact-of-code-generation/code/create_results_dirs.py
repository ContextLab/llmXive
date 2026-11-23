import os
import sys
import logging
from utils import get_logger, set_task_id, get_task_id

def ensure_results_directories():
    """
    T030: Ensure results/figures/ directory exists.
    """
    logger = get_logger(__name__)
    set_task_id("T030")
    
    results_dir = "results"
    figures_dir = os.path.join(results_dir, "figures")

    try:
        os.makedirs(figures_dir, exist_ok=True)
        logger.info(f"Ensured directory exists: {figures_dir}")
    except OSError as e:
        logger.error(f"Failed to create directory {figures_dir}: {e}")
        raise

def main():
    ensure_results_directories()

if __name__ == "__main__":
    main()
