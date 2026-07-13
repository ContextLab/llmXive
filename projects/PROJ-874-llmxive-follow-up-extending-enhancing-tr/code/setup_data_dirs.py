import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    Specifically creates:
    - projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/data/raw/
    - projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/data/processed/
    - projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/data/results/
    
    This satisfies task T001b.
    """
    project_root = Path("projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr")
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Data directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_data_directories()