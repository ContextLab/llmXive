"""
Script to setup the data directory structure for the project.
Implements Task T004: Create data/raw, data/generated, and data/results
along with their corresponding .gitkeep files.
"""
import sys
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def ensure_dir_and_gitkeep(dir_name: str):
    """
    Ensures a directory exists within the data/ folder and contains a .gitkeep file.
    """
    # paths.data(dir_name) creates the directory if it doesn't exist
    dir_path = paths.data(dir_name)
    gitkeep_path = dir_path / ".gitkeep"
    
    # Create an empty .gitkeep file
    gitkeep_path.touch()
    log.info(f"Ensured directory and .gitkeep: {gitkeep_path}")

def main():
    """
    Main entry point to initialize the required data directories.
    """
    try:
        required_dirs = ["raw", "generated", "results"]
        for d in required_dirs:
            ensure_dir_and_gitkeep(d)
        
        log.info("Successfully initialized data directory structure.")
        return 0
    except Exception as e:
        log.error(f"Failed to setup data directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
