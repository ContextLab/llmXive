import os
import sys
import json
import hashlib
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_mode, is_ci_mode, get_path
from utils.logger import get_logger, setup_project_logger
from utils.refactor_utils import ensure_directory, safe_json_load, safe_json_save

# Initialize logger
logger = setup_project_logger("quickstart_validator")

# Required artifacts mapping: category -> list of relative paths from project root
REQUIRED_ARTIFACTS = {
    "data_processed": [
        "data/processed/masked_images",  # Directory check
    ],
    "data_annotations": [
        "data/annotations/decoupled_scores.csv",
        "data/annotations/human_scores.csv",  # Optional for CI, required for Research
    ],
    "data_results": [
        "data/results/validation_log.txt",
        "data/results/inter_rater_reliability.json",  # Conditional
        "data/results/proxy_validation.json",
        "data/results/permutation_test.json",  # Conditional
        "data/results/latency_raw.csv",
        "data/results/evaluation_report.json",
        "data/results/ablation_report.json",
        "data/results/power_analysis.json",
    ],
    "code_models": [
        "code/models/moebius_dynamic.pt",
        "code/models/moebius_tiny.py",
        "code/models/gating_head.py",
        "code/models/moebius_dynamic.py",
    ],
    "docs": [
        "docs/README.md",
        "paper/draft.md",
    ],
}

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        return "ERROR"

def check_directory_exists(dir_path: Path) -> bool:
    """Check if a directory exists and is not empty."""
    if not dir_path.exists():
        return False
    if not dir_path.is_dir():
        return False
    # Check for non-empty (contains at least one file)
    try:
        return any(dir_path.iterdir())
    except PermissionError:
        return False

def validate_artifact(path_str: str, mode: str) -> Dict[str, Any]:
    """Validate a single artifact (file or directory)."""
    full_path = project_root / path_str
    exists = False
    is_valid = False
    file_hash = None
    message = ""

    if full_path.is_dir():
        exists = check_directory_exists(full_path)
        is_valid = exists
        message = "Directory exists and is not empty" if exists else "Directory missing or empty"
    else:
        exists = full_path.exists()
        if exists:
            file_hash = compute_file_hash(full_path)
            # Basic validation: non-empty file
            try:
                size = full_path.stat().st_size
                is_valid = size > 0
                message = f"File exists, size={size} bytes, hash={file_hash[:16]}..."
            except Exception as e:
                is_valid = False
                message = f"File exists but unreadable: {e}"
        else:
            message = "File not found"

    # Mode-specific logic for optional files
    if "human_scores.csv" in path_str:
        if mode == "CI":
            is_valid = True  # Optional in CI mode
            message = "Optional in CI mode (skipped)"

    return {
        "path": path_str,
        "exists": exists,
        "valid": is_valid,
        "hash": file_hash,
        "message": message
    }

def run_quickstart_validation(mode: str) -> Dict[str, Any]:
    """Run the full validation pipeline."""
    logger.info(f"Starting Quickstart Validation for Mode: {mode}")
    
    results = {
        "mode": mode,
        "timestamp": str(Path(project_root / "data/results/validation_log.txt").stat().st_mtime if (project_root / "data/results/validation_log.txt").exists() else "N/A"),
        "artifacts": {},
        "summary": {
            "total_checked": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    }

    all_passed = True

    for category, paths in REQUIRED_ARTIFACTS.items():
        category_results = []
        for path_str in paths:
            result = validate_artifact(path_str, mode)
            category_results.append(result)
            results["summary"]["total_checked"] += 1
            
            if result["valid"]:
                results["summary"]["passed"] += 1
            elif "Optional in CI" in result["message"]:
                results["summary"]["skipped"] += 1
            else:
                results["summary"]["failed"] += 1
                all_passed = False

        results["artifacts"][category] = category_results

    results["summary"]["overall_status"] = "PASSED" if all_passed else "FAILED"
    logger.info(f"Validation Complete: {results['summary']['overall_status']}")
    
    return results

def generate_checksum_manifest(results: Dict[str, Any], output_path: Path):
    """Generate a checksum manifest file."""
    manifest = {
        "generated_at": str(Path(__file__).stat().st_mtime),
        "mode": results["mode"],
        "overall_status": results["summary"]["overall_status"],
        "files": []
    }

    for category, items in results["artifacts"].items():
        for item in items:
            if item["hash"] and item["hash"] != "ERROR":
                manifest["files"].append({
                    "path": item["path"],
                    "sha256": item["hash"],
                    "status": "valid" if item["valid"] else "missing_or_invalid"
                })

    ensure_directory(output_path.parent)
    safe_json_save(manifest, output_path)
    logger.info(f"Checksum manifest saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run quickstart validation and checksum artifacts")
    parser.add_argument("--mode", type=str, default=None, choices=["CI", "RESEARCH"],
                        help="Override config mode (defaults to config.py)")
    parser.add_argument("--output", type=str, default="data/results/quickstart_manifest.json",
                        help="Path to save checksum manifest")
    args = parser.parse_args()

    # Determine mode
    if args.mode:
        mode = args.mode
    else:
        mode = get_mode()

    output_path = project_root / args.output

    # Run validation
    results = run_quickstart_validation(mode)

    # Save manifest
    generate_checksum_manifest(results, output_path)

    # Exit with appropriate code
    if results["summary"]["overall_status"] == "PASSED":
        logger.info("All required artifacts validated successfully.")
        sys.exit(0)
    else:
        logger.error(f"Validation failed. Missing/invalid artifacts: {results['summary']['failed']}")
        sys.exit(1)

if __name__ == "__main__":
    main()