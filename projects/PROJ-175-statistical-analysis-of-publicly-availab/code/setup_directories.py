"""
Setup and verification of project directory structure for PROJ-175.
Implements T001a: Create project directory structure and log verification.
"""
import os
import json
from datetime import datetime
from pathlib import Path

# Define the project root relative to the code directory
# The script is expected to be run from the project root or code directory
# We assume the project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-175-statistical-analysis-of-publicly-availab"

# Define the required directories relative to the project root
REQUIRED_DIRS = [
    PROJECT_ROOT / PROJECT_NAME / "code",
    PROJECT_ROOT / PROJECT_NAME / "data",
    PROJECT_ROOT / PROJECT_NAME / "tests",
    PROJECT_ROOT / PROJECT_NAME / "data" / "raw",
    PROJECT_ROOT / PROJECT_NAME / "data" / "processed",
    PROJECT_ROOT / PROJECT_NAME / "data" / "final",
]

def ensure_directories():
    """Create all required directories if they do not exist."""
    for dir_path in REQUIRED_DIRS:
        dir_path.mkdir(parents=True, exist_ok=True)

def verify_directories():
    """Verify existence of directories and return a list of verified paths."""
    verified_paths = []
    for dir_path in REQUIRED_DIRS:
        if dir_path.is_dir():
            verified_paths.append(str(dir_path))
        else:
            # Attempt to create if missing (should have been done by ensure_directories)
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                if dir_path.is_dir():
                    verified_paths.append(str(dir_path))
            except OSError:
                pass
    return verified_paths

def log_setup_status(verified_paths, output_path):
    """
    Log the setup status to a JSON file.
    Schema: {"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"]}
    """
    all_verified = len(verified_paths) == len(REQUIRED_DIRS)
    status = "SUCCESS" if all_verified else "FAILED"
    
    log_data = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "paths_verified": verified_paths
    }
    
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    return log_data

def main():
    """Main entry point for the setup script."""
    # Ensure all directories exist
    ensure_directories()
    
    # Verify directories
    verified_paths = verify_directories()
    
    # Define output path
    # The log should be in data/setup_log.json relative to the project root
    # Note: The task description says "projects/PROJ-175.../data/setup_log.json"
    # We map this to PROJECT_ROOT / PROJECT_NAME / "data" / "setup_log.json"
    output_path = PROJECT_ROOT / PROJECT_NAME / "data" / "setup_log.json"
    
    # Log the status
    log_data = log_setup_status(verified_paths, output_path)
    
    # Print result for immediate feedback
    if log_data["status"] == "SUCCESS":
        print(f"Setup successful. Verified {len(verified_paths)} directories.")
        print(f"Log written to: {output_path}")
    else:
        print(f"Setup failed. Some directories could not be created/verified.")
        print(f"Log written to: {output_path}")
    
    return log_data

if __name__ == "__main__":
    main()
