import os
import sys
import logging
from utils import get_logger, set_task_id, get_task_id

def create_directories():
    """
    Create the required data directory structure:
    data/raw/
    data/generated/
    data/analysis/

    Constraint: Does NOT create 'state/' (created in T001a at root level).
    """
    # Determine project root relative to this script's location
    # Assuming script is in code/, project root is one level up
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    data_dir = os.path.join(project_root, 'data')
    dirs_to_create = [
        os.path.join(data_dir, 'raw'),
        os.path.join(data_dir, 'generated'),
        os.path.join(data_dir, 'analysis')
    ]
    
    logger = get_logger()
    logger.info("Ensuring data directory structure exists...")
    
    created_count = 0
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    # Verify 'state' is NOT created here
    state_dir = os.path.join(data_dir, 'state')
    if os.path.exists(state_dir):
        logger.warning(f"Found existing 'state' directory in data/: {state_dir}. "
                     "This should be at the project root level (created in T001a).")
    else:
        logger.info("Confirmed 'state' directory is not in data/ (as expected).")
    
    logger.info(f"Data directory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Main entry point for T008."""
    logger = setup_logging(task_id="T008")
    set_task_id("T008")
    
    try:
        success = create_directories()
        if success:
            logger.info("T008 completed successfully.")
            sys.exit(0)
        else:
            logger.error("T008 failed to create directories.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"T008 failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
