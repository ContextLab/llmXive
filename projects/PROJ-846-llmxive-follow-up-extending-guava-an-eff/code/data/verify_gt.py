"""
Ground Truth Verification Script (T013c).

Verifies the integrity of the downloaded ground truth annotations file
produced by T013b (download_gt_annotations.py).

Checks for required keys: 'annotations' and 'bboxes'.
Generates a verification report in data/raw/guava/gt_verified.json.

Logic:
  - If valid: status = "valid"
  - If invalid/missing: status = "missing"

Dependencies:
  - T013b (must have run successfully to produce input file)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Project root relative to this file (3 levels up: code/data -> project root)
# We use the standard project root convention for this project
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "guava"
INPUT_FILE = DATA_RAW_DIR / "ground_truth_annotations.json"
OUTPUT_FILE = DATA_RAW_DIR / "gt_verified.json"

# Required keys for validation
REQUIRED_KEYS = ["annotations", "bboxes"]


def load_ground_truth(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the ground truth JSON file.
    Returns None if file does not exist or cannot be parsed.
    """
    if not file_path.exists():
        print(f"[ERROR] Ground truth file not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error reading {file_path}: {e}")
        return None


def verify_structure(data: Dict[str, Any]) -> bool:
    """
    Verify that the data contains the required keys.
    Returns True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        print("[ERROR] Ground truth data is not a dictionary.")
        return False

    missing_keys = [key for key in REQUIRED_KEYS if key not in data]
    if missing_keys:
        print(f"[ERROR] Missing required keys: {missing_keys}")
        return False

    # Optional deeper check: ensure 'annotations' is a list and 'bboxes' is present
    if not isinstance(data.get("annotations"), list):
        print("[ERROR] 'annotations' field must be a list.")
        return False

    # We assume 'bboxes' existence is enough for structural integrity here,
    # as per task description, but we check it's not null.
    if data.get("bboxes") is None:
        print("[ERROR] 'bboxes' field is null or missing.")
        return False

    return True


def write_verification_report(status: str, output_path: Path) -> None:
    """
    Write the verification result to the output JSON file.
    """
    report = {
        "status": status,
        "input_file": str(INPUT_FILE),
        "verified_at": datetime.utcnow().isoformat() + "Z"
    }

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[INFO] Verification report written to: {output_path}")


def main() -> int:
    """
    Main entry point for T013c.
    Returns 0 on success (regardless of validation result), non-zero on script failure.
    """
    print(f"[INFO] Starting Ground Truth Verification (T013c)...")
    print(f"[INFO] Input file: {INPUT_FILE}")

    # Load data
    data = load_ground_truth(INPUT_FILE)
    if data is None:
        # File missing or invalid JSON -> treat as missing/invalid
        write_verification_report("missing", OUTPUT_FILE)
        return 0

    # Verify structure
    if verify_structure(data):
        print("[INFO] Ground truth structure is VALID.")
        write_verification_report("valid", OUTPUT_FILE)
        return 0
    else:
        print("[INFO] Ground truth structure is INVALID.")
        write_verification_report("missing", OUTPUT_FILE)
        return 0


if __name__ == "__main__":
    sys.exit(main())