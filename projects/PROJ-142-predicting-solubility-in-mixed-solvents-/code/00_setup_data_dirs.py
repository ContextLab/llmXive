"""
T006: Create data directory structure for the solubility prediction project.

This script creates the required directory hierarchy under 'data/' to support
the ingestion, processing, and artifact storage phases of the pipeline.

Directories created:
- data/raw/       : For raw data downloads from EPA/external sources.
- data/processed/ : For cleaned, filtered, and feature-engineered datasets.
- data/artifacts/ : For model outputs, logs, checksums, and analysis reports.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard data directory structure."""
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    required_dirs = [
        "raw",
        "processed",
        "artifacts"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Ensure it is actually a directory
            if not dir_path.is_dir():
                print(f"ERROR: {dir_path} exists but is not a directory.", file=sys.stderr)
                sys.exit(1)
            existing_count += 1
    
    print(f"Data directory setup complete. Created: {created_count}, Existing: {existing_count}")
    
    # Verify structure
    if not (data_root / "raw").exists() or \
       not (data_root / "processed").exists() or \
       not (data_root / "artifacts").exists():
        print("ERROR: Verification failed. Not all directories exist.", file=sys.stderr)
        sys.exit(1)
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
