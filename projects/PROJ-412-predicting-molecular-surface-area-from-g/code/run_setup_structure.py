import os
import sys
import logging
from pathlib import Path
from code.utils.logging import setup_logging, get_logger
from code.utils.directories import create_all_directories

def main():
    """
    Main entry point to run the full setup structure creation.
    This script ensures all project directories (code, data, tests, results, logs)
    are created according to the project specification.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Running Project Directory Setup (T001a, T001b, T001c, T001d)")
    logger.info("=" * 60)
    
    try:
        # Create all directories including results structure (T001d)
        project_root = create_all_directories()
        
        logger.info("Directory structure creation completed successfully.")
        logger.info(f"Project root: {project_root}")
        
        # Verify specific T001d requirements
        results_dirs = [
            "results/reports",
            "results/plots",
            "results/baseline",
            "results/predictions"
        ]
        
        logger.info("Verifying results directory structure (T001d)...")
        for rel_path in results_dirs:
            full_path = project_root / rel_path
            if full_path.exists():
                logger.info(f"  [OK] {rel_path}")
            else:
                logger.error(f"  [MISSING] {rel_path}")
                raise FileNotFoundError(f"Required directory missing: {full_path}")
        
        logger.info("All verification checks passed.")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
