import os
import json
from datetime import datetime
from pathlib import Path

def ensure_directories(base_path: str) -> list:
    """
    Create the required project directory structure.
    
    Args:
        base_path: The root directory for the project (e.g., 'projects/PROJ-175-...')
        
    Returns:
        A list of full paths to the created directories.
    """
    required_dirs = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/processed",
        "data/final",
        "data/logs",
        "docs"
    ]
    
    created_paths = []
    for dir_name in required_dirs:
        full_path = os.path.join(base_path, dir_name)
        os.makedirs(full_path, exist_ok=True)
        created_paths.append(full_path)
        
    return created_paths

def verify_directories(paths: list) -> dict:
    """
    Verify that all required directories exist.
    
    Args:
        paths: List of directory paths to verify.
        
    Returns:
        A dictionary with verification status and details.
    """
    verified = []
    failed = []
    
    for path in paths:
        if os.path.isdir(path):
            verified.append(path)
        else:
            failed.append(path)
            
    return {
        "verified": verified,
        "failed": failed,
        "all_passed": len(failed) == 0
    }

def log_setup_status(base_path: str, status: str, paths: list, failed_paths: list = None) -> str:
    """
    Log the setup status to a JSON file.
    
    Args:
        base_path: The root directory for the project.
        status: "SUCCESS" or "FAILED".
        paths: List of paths that were verified/created.
        failed_paths: List of paths that failed verification (if any).
        
    Returns:
        The path to the log file.
    """
    log_data = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "paths_verified": paths
    }
    
    if failed_paths:
        log_data["paths_failed"] = failed_paths
        
    log_path = os.path.join(base_path, "data", "setup_log.json")
    
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)
        
    return log_path

def main():
    """
    Main entry point for task T001a: Create project directory structure.
    """
    # Define the project root based on the task description
    project_root = "projects/PROJ-175-statistical-analysis-of-publicly-availab"
    
    # Ensure the base project directory exists first
    os.makedirs(project_root, exist_ok=True)
    
    # Create the required subdirectories
    created_paths = ensure_directories(project_root)
    
    # Verify the directories were created successfully
    verification = verify_directories(created_paths)
    
    # Determine final status
    if verification["all_passed"]:
        status = "SUCCESS"
        paths_to_log = verification["verified"]
        failed_paths = None
    else:
        status = "FAILED"
        paths_to_log = verification["verified"]
        failed_paths = verification["failed"]
        
    # Log the result
    log_path = log_setup_status(project_root, status, paths_to_log, failed_paths)
    
    print(f"Setup completed with status: {status}")
    print(f"Log written to: {log_path}")
    
    if status == "FAILED":
        print(f"Failed paths: {failed_paths}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
