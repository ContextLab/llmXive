"""
Script to create the required data directory structure.

This task (T006) ensures the existence of:
- data/raw
- data/processed
- data/results

It uses the project configuration and logging infrastructure established in T004 and T005.
"""
import os
from pathlib import Path
from config import get_config
from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import handle_error, ConfigError

def create_data_directories():
    """
    Create the standard data directory structure defined in the project plan.
    
    Directories created:
    - data/raw: For raw, unprocessed data downloads (e.g., Materials Project JSON)
    - data/processed: For cleaned, feature-engineered datasets
    - data/results: For model outputs, metrics, and decision logs
    - data/external: For external validation sets (literature PCMs)
    
    Raises:
        ConfigError: If the base data directory cannot be determined or created.
    """
    logger = get_pipeline_logger()
    logger.info("Starting data directory structure creation (Task T006).")
    
    try:
        config = get_config()
        base_dir = Path(config.get("paths", {}).get("data_root", "data"))
        
        # Ensure the base directory exists
        base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Base data directory confirmed at: {base_dir}")
        
        # Define the required subdirectories
        required_dirs = [
            "raw",
            "processed",
            "results",
            "external"
        ]
        
        created_count = 0
        for dir_name in required_dirs:
            target_path = base_dir / dir_name
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {target_path}")
        
        logger.info(f"Data directory structure setup complete. Created {created_count} new directories.")
        return True

    except Exception as e:
        handle_error(e, "Failed to create data directory structure", logger, ConfigError)
        return False

def main():
    """Entry point for the script."""
    success = create_data_directories()
    if success:
        print("Data directories created successfully.")
    else:
        print("Failed to create data directories. Check logs for details.")
        exit(1)

if __name__ == "__main__":
    main()