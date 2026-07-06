"""
Constitution Check Module for PROJ-005.

Verifies:
1. Citations: Ensures all data sources and models have corresponding entries in the citations manifest.
2. Checksums: Validates integrity of raw data artifacts against stored checksums.
3. Reproducibility: Confirms existence of critical pipeline outputs and configuration files.
"""
import json
import hashlib
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import existing logging utility
from src.utils.logging import get_logger, setup_logger

# Constants
CHECKSUM_FILE = "data/raw/checksums.json"
CITATIONS_FILE = "data/raw/citations_manifest.json"
REPRODUCIBILITY_KEYS = [
    "data/processed/graphs.parquet",
    "data/processed/splits.json",
    "data/processed/predictions.parquet",
    "data/processed/metrics.json",
    "data/results/feature_importance.csv",
    "data/results/statistical_tests.json",
    "data/results/speed_metrics.json",
    "data/results/final_metrics_table.csv",
    "requirements.txt",
    "src/utils/config.py"
]

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """Computes the checksum of a file."""
    if not file_path.exists():
        return None
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logging.error(f"Error computing checksum for {file_path}: {e}")
        return None

def load_json_file(file_path: Path) -> Optional[Dict]:
    """Loads a JSON file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return None

def verify_checksums() -> Tuple[bool, List[str]]:
    """
    Verifies checksums of raw data artifacts against stored checksums.
    Returns (success, list_of_errors).
    """
    errors = []
    root = get_project_root()
    checksum_file = root / CHECKSUM_FILE
    
    if not checksum_file.exists():
        errors.append(f"Checksum file not found: {checksum_file}")
        return False, errors

    stored_checksums = load_json_file(checksum_file)
    if not stored_checksums:
        errors.append(f"Failed to load checksums from {checksum_file}")
        return False, errors

    for filename, expected_hash in stored_checksums.items():
        file_path = root / filename
        if not file_path.exists():
            errors.append(f"Missing file for checksum verification: {filename}")
            continue

        actual_hash = compute_file_checksum(file_path)
        if actual_hash != expected_hash:
            errors.append(
                f"Checksum mismatch for {filename}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}"
            )
    
    return len(errors) == 0, errors

def verify_citations() -> Tuple[bool, List[str]]:
    """
    Verifies that required citations exist in the manifest.
    Returns (success, list_of_errors).
    """
    errors = []
    root = get_project_root()
    citations_file = root / CITATIONS_FILE
    
    # Define required citations based on the project scope
    required_citations = {
        "qm9_ts_dataset": "QM9-TS Dataset",
        "schnet_architecture": "SchNet Architecture",
        "shap_library": "SHAP Library",
        "pytorch_geometric": "PyTorch Geometric"
    }
    
    if not citations_file.exists():
        # If the file doesn't exist, we create a warning but don't fail if we can proceed
        # However, for a strict constitution check, we might require it.
        # Let's assume it must exist for a complete constitution.
        errors.append(f"Citations manifest not found: {citations_file}")
        return False, errors

    manifest = load_json_file(citations_file)
    if not manifest:
        errors.append(f"Failed to load citations from {citations_file}")
        return False, errors

    for key, description in required_citations.items():
        if key not in manifest:
            errors.append(f"Missing required citation: {description} (key: {key})")
        elif not manifest[key].get("citation", "").strip():
            errors.append(f"Citation content missing for: {description}")
    
    return len(errors) == 0, errors

def verify_reproducibility() -> Tuple[bool, List[str]]:
    """
    Verifies that all critical files for reproducibility exist.
    Returns (success, list_of_errors).
    """
    errors = []
    root = get_project_root()
    
    for rel_path in REPRODUCIBILITY_KEYS:
        file_path = root / rel_path
        if not file_path.exists():
            errors.append(f"Missing reproducibility artifact: {rel_path}")
    
    return len(errors) == 0, errors

def run_constitution_check() -> Dict[str, Any]:
    """
    Runs the full constitution check and returns a report.
    """
    logger = setup_logger("constitution_check")
    logger.info("Starting Constitution Check...")
    
    results = {
        "timestamp": "N/A", # Could add datetime if needed
        "checksums": {"passed": False, "errors": []},
        "citations": {"passed": False, "errors": []},
        "reproducibility": {"passed": False, "errors": []},
        "overall_passed": False
    }
    
    # Check Checksums
    logger.info("Verifying checksums...")
    passed, errors = verify_checksums()
    results["checksums"]["passed"] = passed
    results["checksums"]["errors"] = errors
    if passed:
        logger.info("Checksum verification passed.")
    else:
        logger.error(f"Checksum verification failed with {len(errors)} errors.")

    # Check Citations
    logger.info("Verifying citations...")
    passed, errors = verify_citations()
    results["citations"]["passed"] = passed
    results["citations"]["errors"] = errors
    if passed:
        logger.info("Citation verification passed.")
    else:
        logger.error(f"Citation verification failed with {len(errors)} errors.")

    # Check Reproducibility
    logger.info("Verifying reproducibility artifacts...")
    passed, errors = verify_reproducibility()
    results["reproducibility"]["passed"] = passed
    results["reproducibility"]["errors"] = errors
    if passed:
        logger.info("Reproducibility verification passed.")
    else:
        logger.error(f"Reproducibility verification failed with {len(errors)} errors.")

    results["overall_passed"] = (
        results["checksums"]["passed"] and
        results["citations"]["passed"] and
        results["reproducibility"]["passed"]
    )
    
    logger.info(f"Constitution Check Final Result: {'PASSED' if results['overall_passed'] else 'FAILED'}")
    return results

def main():
    """Main entry point for the constitution check."""
    report = run_constitution_check()
    
    # Save report to data/results
    root = get_project_root()
    output_path = root / "data" / "results" / "constitution_check_report.json"
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Constitution check report saved to: {output_path}")
    
    if not report["overall_passed"]:
        print("WARNING: Constitution check FAILED. Review errors in report.")
        sys.exit(1)
    else:
        print("SUCCESS: Constitution check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
