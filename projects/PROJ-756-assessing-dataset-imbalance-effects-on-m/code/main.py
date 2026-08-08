import os
import sys
import logging
from pathlib import Path

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_structure import create_directories
from setup_data_directory import create_data_directories
from setup_results_directory import create_results_directory
from setup_state import create_state_directory
from setup_tests_directory import create_tests_directory
from setup_artifacts_directory import create_artifacts_directory
from setup_raw_data_directory import create_raw_data_directory

def run_pipeline():
    """
    Main entry point to initialize the project structure and run the pipeline.
    This function orchestrates the creation of all necessary directories.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    project_root = Path.cwd()
    project_id = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    base_path = project_root / "projects" / project_id

    logger.info(f"Initializing project structure at {base_path}")

    # Ensure the base project directory exists
    base_path.mkdir(parents=True, exist_ok=True)

    # Initialize sub-structures
    try:
        create_directories(base_path)
        logger.info("Directory structure created successfully.")
    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}")
        raise

    # Additional specific directory setups if needed
    # These are separate modules as per the API surface
    create_data_directories(base_path)
    create_raw_data_directory(base_path)
    create_results_directory(base_path)
    create_state_directory(base_path)
    create_tests_directory(base_path)
    create_artifacts_directory(base_path)

    logger.info("Project initialization complete.")
    return True

if __name__ == "__main__":
    run_pipeline()
