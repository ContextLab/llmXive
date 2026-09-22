"""
Task T013b: Ground Truth Verification

Searches for existing ground-truth annotations in the raw Guava dataset.
If found, copies them to the standard location. If not found, raises
GroundTruthSchemaMissingError to halt the project pipeline.

Dependencies:
  - T013a (download_guava.py) must have run to populate data/raw/guava/
"""

import json
import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project exceptions
from utils.exceptions import GroundTruthSchemaMissingError
from utils.config import get_path


def scan_file_for_keys(file_path: Path, required_keys: List[str]) -> bool:
    """
    Scans a JSON file to see if it contains any of the required keys.
    Handles potentially large files by reading line-by-line or in chunks
    if necessary, but for JSON objects we usually load the top level.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to load the top-level structure.
            # If the file is a JSONL (one JSON per line), we iterate.
            content = f.read()
            
            # Check for JSONL format first
            if '\n' in content and content.strip().endswith('\n'):
                lines = content.strip().split('\n')
                for line in lines:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if any(key in data for key in required_keys):
                            return True
                    except json.JSONDecodeError:
                        continue
            else:
                # Standard JSON
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and any(key in item for key in required_keys):
                            return True
                elif isinstance(data, dict):
                    if any(key in data for key in required_keys):
                        return True
        
        return False
    except Exception as e:
        # If we can't parse the file, it's not a valid annotation source
        print(f"Warning: Could not parse {file_path}: {e}")
        return False


def find_ground_truth_annotations(raw_dir: Path, required_keys: List[str]) -> Optional[Path]:
    """
    Recursively searches raw_dir for a file containing ground truth annotations.
    Returns the path to the first matching file, or None.
    """
    print(f"Scanning {raw_dir} for ground truth annotations (keys: {required_keys})...")
    
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.endswith(('.json', '.jsonl')):
                file_path = Path(root) / file
                if scan_file_for_keys(file_path, required_keys):
                    print(f"  -> Found candidate: {file_path}")
                    return file_path
    return None


def verify_ground_truth() -> None:
    """
    Main verification logic for T013b.
    """
    # 1. Define paths
    raw_guava_dir = get_path("raw_guava")
    output_path = get_path("ground_truth_annotations")
    
    if not raw_guava_dir.exists():
        raise FileNotFoundError(
            f"Raw Guava directory not found at {raw_guava_dir}. "
            "Please run T013a (download_guava.py) first."
        )

    # 2. Define schema keys to search for
    # The task description specifies: annotations, bboxes, objects
    search_keys = ["annotations", "bboxes", "objects"]

    # 3. Search for existing ground truth
    source_file = find_ground_truth_annotations(raw_guava_dir, search_keys)

    if source_file is None:
        # CRITICAL: Raise the specific exception to halt the project
        raise GroundTruthSchemaMissingError(
            "Ground Truth annotations not found in raw data. "
            "Cannot compute Perception Ground-Truth Log (FR-007). Project halted."
        )

    # 4. Copy to the standard output location
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, output_path)
    
    print(f"Ground truth annotations successfully verified and copied to: {output_path}")
    print(f"Source: {source_file}")
    
    # Optional: Validate the copied file has the expected structure again
    with open(output_path, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
            if '\n' in content and content.strip().endswith('\n'):
                # JSONL
                first_line = content.split('\n')[0]
                data = json.loads(first_line)
            else:
                data = json.loads(content)
            
            found = False
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    found = any(k in data[0] for k in search_keys)
            elif isinstance(data, dict):
                found = any(k in data for k in search_keys)
            
            if not found:
                # Should not happen if find_ground_truth worked, but safety check
                raise GroundTruthSchemaMissingError(
                    "Copied file does not contain expected keys after copy. Integrity check failed."
                )
        except json.JSONDecodeError:
            raise ValueError("Copied ground truth file is not valid JSON.")


def main():
    """Entry point for script execution."""
    try:
        verify_ground_truth()
        print("T013b verification completed successfully.")
    except GroundTruthSchemaMissingError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"PRE-REQUISITE ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()