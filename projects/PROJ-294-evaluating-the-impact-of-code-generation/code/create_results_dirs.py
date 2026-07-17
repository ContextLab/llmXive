import os
import sys
import logging
from utils import get_logger, set_task_id, get_task_id

def main():
    """
    Creates the results directory structure required for the project.
    Specifically creates:
    - results/
    - results/figures/

    This satisfies task T009.
    """
    task_id = get_task_id()
    set_task_id(task_id)
    logger = get_logger(task_id)

    base_dir = "results"
    figures_dir = os.path.join(base_dir, "figures")

    directories = [base_dir, figures_dir]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

    logger.info(f"Results directory structure created successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
