import os
import sys
from pathlib import Path
import logging

def create_data_directories(base_path: Path) -> None:
    """
    Create the required data directory structure for the project.
    Creates:
      - data/raw/
      - data/processed/
      - data/reports/
    
    Each directory receives a .gitkeep file to ensure version control tracking.
    """
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "reports"
    ]

    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        
        # Create .gitkeep file with a standard comment
        with open(gitkeep_path, "w", encoding="utf-8") as f:
            f.write("# Keep this directory in version control\n")
        
        logging.info(f"Created directory: {dir_path}")
        logging.info(f"Created .gitkeep file: {gitkeep_path}")

def main() -> int:
    """Main entry point for directory setup."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Determine the project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    logging.info(f"Project root: {project_root}")
    
    try:
        create_data_directories(project_root)
        logging.info("Data directories created successfully.")
        return 0
    except Exception as e:
        logging.error(f"Failed to create data directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())