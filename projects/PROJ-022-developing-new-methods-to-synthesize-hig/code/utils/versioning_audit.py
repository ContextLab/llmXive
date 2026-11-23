"""
Versioning Audit Utility for llmXive Pipeline.

This module validates the integrity of the project state by comparing
current file hashes against those recorded in the state.yaml artifact.
It ensures no artifacts have been modified since the last recorded state.

Required by: T047 (Constitutional Principle V)
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import logging utility from project structure
from utils.logging_config import setup_pipeline_logger

# Constants
STATE_FILE_PATH = "state/projects/PROJ-022-developing-new-methods-to-synthesize-hig.yaml"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HASH_ALGORITHM = "sha256"

logger = setup_pipeline_logger("versioning_audit")


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def load_state_hashes(state_path: Path) -> Dict[str, str]:
    """
    Load the artifact_hashes map from the state.yaml file.

    Note: Since PyYAML is in requirements, we use it here to parse YAML.
    We assume the file format is a valid YAML dictionary.

    Args:
        state_path: Path to the state.yaml file.

    Returns:
        Dictionary mapping relative file paths to their recorded hashes.

    Raises:
        FileNotFoundError: If state.yaml does not exist.
        ValueError: If the state file is malformed or missing 'artifact_hashes'.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")

    try:
        import yaml
        with open(state_path, "r", encoding="utf-8") as f:
            state_data = yaml.safe_load(f)

        if not isinstance(state_data, dict):
            raise ValueError("State file must contain a dictionary mapping.")

        if "artifact_hashes" not in state_data:
            raise ValueError("State file missing 'artifact_hashes' key.")

        return state_data["artifact_hashes"]
    except ImportError:
        # Fallback to a simple parser if yaml is somehow missing, though it should be installed
        logger.warning("PyYAML not found. Attempting basic YAML parsing for artifact_hashes.")
        # Simple line-based parser for key: value structure
        hashes = {}
        in_hashes = False
        with open(state_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped == "artifact_hashes:":
                    in_hashes = True
                    continue
                if in_hashes:
                    if stripped.startswith("-") or (stripped and not stripped.startswith(" ") and not stripped.startswith("#")):
                        # End of the list/map block if we hit a new top-level key
                        if not stripped.startswith("-"):
                            break
                    if ":" in stripped:
                        key, val = stripped.split(":", 1)
                        hashes[key.strip()] = val.strip().strip('"').strip("'")
        return hashes
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML in state file: {e}")


def verify_artifact_hashes(
    recorded_hashes: Dict[str, str],
    base_dir: Optional[Path] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Verify that current file hashes match the recorded hashes.

    Args:
        recorded_hashes: Dictionary of {relative_path: expected_hash}.
        base_dir: Base directory to resolve relative paths against. Defaults to PROJECT_ROOT.

    Returns:
        Tuple of (all_valid: bool, details: List of status dicts).
    """
    if base_dir is None:
        base_dir = PROJECT_ROOT

    details = []
    all_valid = True

    for rel_path, expected_hash in recorded_hashes.items():
        full_path = base_dir / rel_path

        if not full_path.exists():
            msg = f"File missing: {rel_path}"
            details.append({"path": rel_path, "status": "MISSING", "message": msg})
            all_valid = False
            logger.error(msg)
            continue

        try:
            current_hash = calculate_file_hash(full_path)
            if current_hash == expected_hash:
                details.append({"path": rel_path, "status": "OK", "hash": current_hash})
            else:
                msg = f"Hash mismatch for {rel_path}"
                details.append({
                    "path": rel_path,
                    "status": "MISMATCH",
                    "expected": expected_hash,
                    "current": current_hash
                })
                all_valid = False
                logger.error(msg)
        except Exception as e:
            msg = f"Error hashing {rel_path}: {e}"
            details.append({"path": rel_path, "status": "ERROR", "message": str(e)})
            all_valid = False
            logger.error(msg)

    return all_valid, details


def generate_report(
    all_valid: bool,
    details: List[Dict[str, Any]],
    state_path: Path
) -> Dict[str, Any]:
    """
    Generate a structured report of the audit results.

    Args:
        all_valid: Boolean indicating if all checks passed.
        details: List of detailed status dictionaries.
        state_path: Path to the state file audited.

    Returns:
        Dictionary containing the full audit report.
    """
    return {
        "audit_status": "PASSED" if all_valid else "FAILED",
        "state_file": str(state_path),
        "total_files_checked": len(details),
        "passed_count": sum(1 for d in details if d["status"] == "OK"),
        "failed_count": sum(1 for d in details if d["status"] in ["MISMATCH", "MISSING", "ERROR"]),
        "timestamp": str(__import__('datetime').datetime.now()),
        "details": details
    }


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the audit report to a JSON file.

    Args:
        report: The audit report dictionary.
        output_path: Path where the report will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Audit report saved to: {output_path}")


def main() -> int:
    """
    Main entry point for the versioning audit script.

    Returns:
        0 if audit passed, 1 if audit failed.
    """
    logger.info("Starting Versioning Audit...")

    state_path = PROJECT_ROOT / STATE_FILE_PATH

    try:
        # 1. Load recorded hashes
        logger.info(f"Loading state from: {state_path}")
        recorded_hashes = load_state_hashes(state_path)
        logger.info(f"Found {len(recorded_hashes)} artifacts to verify.")

        if not recorded_hashes:
            logger.warning("No artifacts found in state.yaml. Audit trivially passed.")
            report = generate_report(True, [], state_path)
            save_report(report, PROJECT_ROOT / "data/reports/versioning_audit_report.json")
            return 0

        # 2. Verify hashes
        all_valid, details = verify_artifact_hashes(recorded_hashes)

        # 3. Generate and save report
        report = generate_report(all_valid, details, state_path)
        output_report_path = PROJECT_ROOT / "data/reports/versioning_audit_report.json"
        save_report(report, output_report_path)

        if all_valid:
            logger.info("Audit PASSED: All artifact hashes match.")
            return 0
        else:
            logger.error("Audit FAILED: One or more artifacts are missing or modified.")
            return 1

    except FileNotFoundError as e:
        logger.error(f"Critical Error: {e}")
        # Create a failure report
        report = {
            "audit_status": "FAILED",
            "error": str(e),
            "details": []
        }
        save_report(report, PROJECT_ROOT / "data/reports/versioning_audit_report.json")
        return 1
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        report = {
            "audit_status": "FAILED",
            "error": str(e),
            "details": []
        }
        save_report(report, PROJECT_ROOT / "data/reports/versioning_audit_report.json")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during audit: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())