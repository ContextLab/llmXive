import os
import sys
from pathlib import Path
import logging

def setup_directories():
    """
    Creates the required directory structure for the project.
    Ensures data/raw, data/processed, and data/artifacts directories exist.
    Also creates other standard directories if missing.
    """
    # Define the project root relative to this script's location
    # Assuming this script is in code/, project root is parent
    project_root = Path(__file__).parent.parent
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "data" / "models",
        project_root / "data" / "results",
        project_root / "data" / "reports",
        project_root / "logs",
        project_root / "tests",
        project_root / "specs" / "001-predict-weibull-modulus" / "contracts",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logging.debug(f"Directory already exists: {dir_path}")

    if created_count > 0:
        logging.info(f"Successfully created {created_count} directories.")
    else:
        logging.info("All required directories already exist.")

    return True

if __name__ == "__main__":
    # Basic logging configuration for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    setup_directories()
    print("Directory setup complete.")
