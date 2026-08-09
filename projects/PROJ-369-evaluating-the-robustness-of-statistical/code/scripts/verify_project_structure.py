"""
Verification script to confirm all required directories exist.
This provides the evidence required for T001 completion.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_path
from src.utils.logging import setup_logger, log_info

REQUIRED_DIRECTORIES = [
    "src",
    "src/data",
    "src/synthesis",
    "src/analysis",
    "src/viz",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data/raw",
    "data/processed",
    "data/results",
    "specs",
    "state"
]

def main():
    """Verify and report on directory structure."""
    logger = setup_logger("verify_structure")
    root = get_path("")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(root),
        "required_directories": REQUIRED_DIRECTORIES,
        "verification_status": "PASS",
        "missing_directories": [],
        "existing_directories": []
    }

    all_exist = True
    for dir_name in REQUIRED_DIRECTORIES:
        dir_path = root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            results["existing_directories"].append(dir_name)
            logger.info(f"✓ Found: {dir_name}")
        else:
            results["missing_directories"].append(dir_name)
            logger.error(f"✗ Missing: {dir_name}")
            all_exist = False

    if all_exist:
        logger.info("All required directories exist.")
        results["verification_status"] = "PASS"
    else:
        logger.error("Some required directories are missing.")
        results["verification_status"] = "FAIL"

    # Write verification report
    report_path = root / "data" / "results" / "directory_structure_report.json"
    if not report_path.parent.exists():
        report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Verification report written to: {report_path}")
    
    # Print tree-like summary
    print("\n--- Directory Structure Summary ---")
    for dir_name in REQUIRED_DIRECTORIES:
        status = "✓" if dir_name in results["existing_directories"] else "✗"
        print(f"{status} {dir_name}")
    print("-----------------------------------")

    return 0 if all_exist else 1

if __name__ == "__main__":
    sys.exit(main())
