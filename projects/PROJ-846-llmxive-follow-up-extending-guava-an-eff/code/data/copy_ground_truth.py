"""
T013c: Ground Truth Copy

Copies the identified ground truth file (from T013b) to the canonical location:
data/raw/guava/ground_truth_annotations.json

Logic:
1. Check if data/raw/guava/ground_truth_annotations.json already exists.
   If yes, verify its integrity (optional) or skip if up-to-date.
2. If not, run the search logic (or rely on T013b output if cached).
   For robustness, this script re-implements the search to find candidates
   in data/raw/guava/ containing 'annotations', 'bboxes', or 'objects'.
3. Copy the first valid candidate to the target path.
4. Raise GroundTruthSchemaMissingError if no candidates are found.
"""

import json
import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities and exceptions
from utils.exceptions import GroundTruthSchemaMissingError
from utils.config import get_path

# Constants
TARGET_FILENAME = "ground_truth_annotations.json"

def scan_file_for_keys(file_path: Path, required_keys: List[str]) -> bool:
    """
    Scans a JSON file to see if it contains any of the required keys.
    Returns True if at least one key is found at the top level or nested.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check top level
        if any(key in data for key in required_keys):
            return True

        # Check nested structures (common in trajectory JSONs)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and any(key in item for key in required_keys):
                    return True
        elif isinstance(data, dict):
            for value in data.values():
                if isinstance(value, dict) and any(key in value for key in required_keys):
                    return True

        return False
    except (json.JSONDecodeError, IOError) as e:
        # Skip unreadable files
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return False


def find_ground_truth_candidates(raw_dir: Path) -> List[Path]:
    """
    Iterates all JSON/CSV files in raw_dir and returns those containing
    'annotations', 'bboxes', or 'objects'.
    """
    required_keys = ['annotations', 'bboxes', 'objects']
    candidates = []

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    # Search recursively for JSON and CSV files
    for ext in ['*.json', '*.csv']:
        for file_path in raw_dir.rglob(ext):
            # Skip hidden or system files
            if file_path.name.startswith('.'):
                continue
            
            if scan_file_for_keys(file_path, required_keys):
                candidates.append(file_path)
    
    return candidates


def verify_ground_truth(file_path: Path) -> bool:
    """
    Basic verification that the file is valid JSON and not empty.
    """
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return False
            json.loads(content)
            return True
    except (json.JSONDecodeError, IOError):
        return False


def copy_ground_truth() -> Path:
    """
    Main logic for T013c.
    Finds candidates and copies the first valid one to the canonical location.
    """
    # Resolve project root and paths
    project_root = get_path("project_root")
    raw_dir = get_path("raw_guava")
    target_path = raw_dir / TARGET_FILENAME

    # Check if target already exists
    if target_path.exists():
        print(f"Ground truth already exists at {target_path}. Skipping copy.")
        # Optional: Verify integrity
        if verify_ground_truth(target_path):
            print(f"Verification passed for existing file.")
            return target_path
        else:
            print(f"Existing file is invalid. Overwriting...")

    print(f"Searching for ground truth candidates in {raw_dir}...")
    candidates = find_ground_truth_candidates(raw_dir)

    if not candidates:
        raise GroundTruthSchemaMissingError(
            f"No ground truth candidates found in {raw_dir}. "
            "Searched for files containing keys: 'annotations', 'bboxes', 'objects'. "
            "Please ensure T013a (download) and T013b (search) have been run successfully."
        )

    print(f"Found {len(candidates)} candidate(s). Selecting the first valid one.")
    
    selected_candidate = None
    for candidate in candidates:
        if verify_ground_truth(candidate):
            selected_candidate = candidate
            break
    
    if not selected_candidate:
        raise GroundTruthSchemaMissingError(
            f"Found candidates but none were valid JSON files. "
            f"Checked: {[str(c) for c in candidates]}"
        )

    print(f"Selected: {selected_candidate}")
    print(f"Copying to: {target_path}")

    # Ensure directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file
    shutil.copy2(selected_candidate, target_path)

    print(f"Successfully copied ground truth to {target_path}")
    return target_path


def main():
    """
    Entry point for the script.
    """
    try:
        result_path = copy_ground_truth()
        print(f"SUCCESS: Ground truth copied to {result_path}")
        sys.exit(0)
    except GroundTruthSchemaMissingError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: Directory not found - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()