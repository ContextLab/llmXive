import os
import sys
import logging

# Configure logging for the setup script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory_structure():
    """
    Creates the required directory structure for the project.
    Specifically creates data/raw and data/processed as per T001.
    Also ensures code and tests directories exist as per T002 (completing the setup).
    """
    # Define the project root (assuming this script is in code/, so root is parent)
    # However, to be safe and explicit, we assume relative paths from the project root.
    # The task requires: data/raw, data/processed, code, tests.
    
    # Since this script is in code/, we need to go up one level to find the root
    # or we assume the script is run from the root.
    # Let's use a robust approach: determine root based on the existence of 'data' relative to 'code'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    directories = [
        os.path.join(project_root, 'data', 'raw'),
        os.path.join(project_root, 'data', 'processed'),
        os.path.join(project_root, 'code'), # Ensure code exists (usually does)
        os.path.join(project_root, 'tests', 'unit'),
        os.path.join(project_root, 'tests', 'integration'),
        os.path.join(project_root, 'state'),
        os.path.join(project_root, 'figures'),
        os.path.join(project_root, 'docs')
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Directory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Main entry point for the directory setup script."""
    try:
        create_directory_structure()
        logger.info("Setup successful.")
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
