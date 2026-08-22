import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the required directory structure for the project's data artifacts.
    
    This function implements task T001c by ensuring the existence of:
    - data/raw: For raw, unprocessed data downloads
    - data/processed: For cleaned, transformed data ready for analysis
    - data/results: For final analysis outputs, reports, and metrics
    - data/config: For configuration files and schema definitions
    - data/metadata: For metadata about datasets and processing steps
    - data/citations: For verified citation records
    """
    base_dir = Path("data")
    subdirs = [
        "raw",
        "processed",
        "results",
        "config",
        "metadata",
        "citations"
    ]
    
    for subdir in subdirs:
        target_path = base_dir / subdir
        target_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {target_path}")
    
    return True

if __name__ == "__main__":
    setup_data_directories()
    print("Data directory structure created successfully.")
