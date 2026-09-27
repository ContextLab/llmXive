"""
T001b: Verify directory existence for the project setup.

This script validates that all directories created by T001a exist on the filesystem.
It logs the verification results to `data/.setup_verification.log`.

Required directories:
- data/raw
- data/processed
- data/models
- code
- code/utils
- tests
- tests/contract
- tests/unit
- tests/integration
- docs
- state
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Define the required directories relative to the project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/models",
    "code",
    "code/utils",
    "tests",
    "tests/contract",
    "tests/unit",
    "tests/integration",
    "docs",
    "state",
]

def verify_directories():
    """
    Verify that all required directories exist.
    
    Returns:
        tuple: (all_exist: bool, results: dict)
    """
    project_root = Path(__file__).parent.parent
    results = {}
    all_exist = True

    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        exists = full_path.is_dir()
        results[dir_path] = {
            "exists": exists,
            "full_path": str(full_path),
            "status": "OK" if exists else "MISSING"
        }
        if not exists:
            all_exist = False

    return all_exist, results

def log_results(results, log_path):
    """
    Write verification results to the log file.
    
    Args:
        results (dict): The verification results dictionary.
        log_path (Path): Path to the log file.
    """
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Verification Timestamp: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n")
        f.write("Directory Verification Report\n")
        f.write("=" * 60 + "\n\n")
        
        for dir_name, info in results.items():
            status_symbol = "[OK]" if info["exists"] else "[FAIL]"
            f.write(f"{status_symbol} {dir_name}\n")
            f.write(f"    Path: {info['full_path']}\n")
            f.write(f"    Status: {info['status']}\n")
            f.write("\n")
        
        f.write("=" * 60 + "\n")
        total = len(results)
        passed = sum(1 for r in results.values() if r["exists"])
        f.write(f"Summary: {passed}/{total} directories exist.\n")
        
        if passed == total:
            f.write("VERIFICATION: PASSED\n")
        else:
            f.write("VERIFICATION: FAILED\n")

def main():
    """Main entry point for the verification script."""
    project_root = Path(__file__).parent.parent
    log_file = project_root / "data" / ".setup_verification.log"
    
    # Ensure data directory exists to write the log
    data_dir = project_root / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)

    print("Starting directory verification...")
    all_exist, results = verify_directories()
    
    log_results(results, log_file)
    print(f"Verification log written to: {log_file}")
    
    if all_exist:
        print("All required directories exist.")
        sys.exit(0)
    else:
        print("ERROR: Some required directories are missing.")
        # Print missing dirs for immediate feedback
        missing = [k for k, v in results.items() if not v["exists"]]
        print(f"Missing directories: {', '.join(missing)}")
        sys.exit(1)

if __name__ == "__main__":
    main()