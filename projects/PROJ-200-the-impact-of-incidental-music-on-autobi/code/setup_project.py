"""
Setup script for establishing the project layout.
"""
import sys
import logging
from config import ensure_directories, get_project_root
from llmxive_toolkit import get_logger

def main() -> int:
    # Use simple logging to avoid shadowing issues during setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Creating project layout...")
        ensure_directories()
        
        # Ensure additional structural directories exist
        root = get_project_root()
        for extra in ["code", "tests", "contracts", "specs"]:
            (root / extra).mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Project layout successfully created under {root}")
        return 0
    except Exception as exc:
        logger.error(f"Failed to create project layout: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
