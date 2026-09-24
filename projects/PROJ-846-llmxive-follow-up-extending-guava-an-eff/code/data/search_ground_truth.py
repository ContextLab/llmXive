"""
T013b: Ground Truth Search
Searches data/raw/guava/ for files containing keys 'annotations', 'bboxes', or 'objects'.
Outputs a list of candidate file paths to stdout and a JSON report to data/processed/gt_search_candidates.json.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.exceptions import GroundTruthSchemaMissingError
from utils.config import get_path

def scan_file_for_keys(file_path: Path, target_keys: List[str]) -> bool:
    """
    Scans a JSON or CSV file for the presence of any of the target keys at the top level.
    Returns True if at least one target key is found.
    """
    try:
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return any(key in data for key in target_keys)
                elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    # Check first item in list if it's a list of objects
                    return any(key in data[0] for key in target_keys)
        elif file_path.suffix.lower() == '.csv':
            # For CSV, we check the header
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    return any(key in reader.fieldnames for key in target_keys)
        return False
    except (json.JSONDecodeError, csv.Error, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Warning: Error reading {file_path}: {e}")
        return False

def find_ground_truth_annotations(
    raw_data_dir: Path,
    target_keys: List[str] = None
) -> List[Path]:
    """
    Iterates all JSON/CSV files in raw_data_dir and returns a list of paths
    that contain at least one of the target keys.
    """
    if target_keys is None:
        target_keys = ['annotations', 'bboxes', 'objects']
    
    candidates = []
    
    if not raw_data_dir.exists():
        print(f"Error: Raw data directory not found: {raw_data_dir}")
        return candidates

    # Walk through all files
    for root, _, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith(('.json', '.csv')):
                file_path = Path(root) / file
                if scan_file_for_keys(file_path, target_keys):
                    candidates.append(file_path)
                    print(f"Found candidate: {file_path}")
    
    return candidates

def verify_ground_truth(candidates: List[Path]) -> List[Path]:
    """
    Verifies that the found candidates are valid ground truth files.
    For this task, we assume if keys are found, it's a valid candidate.
    In a more robust implementation, we might check schema structure.
    """
    if not candidates:
        raise GroundTruthSchemaMissingError(
            "No ground truth annotation files found containing keys 'annotations', 'bboxes', or 'objects'."
        )
    return candidates

def main():
    """
    Main entry point for T013b.
    1. Searches data/raw/guava/ for candidate files.
    2. Verifies candidates are not empty.
    3. Outputs list of candidate paths to stdout.
    4. Writes a JSON report to data/processed/gt_search_candidates.json.
    """
    print("Starting Ground Truth Search (T013b)...")
    
    # Define paths
    raw_guava_dir = get_path("raw_guava")
    processed_dir = get_path("processed")
    output_report = processed_dir / "gt_search_candidates.json"
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Search for candidates
    try:
        candidates = find_ground_truth_annotations(raw_guava_dir)
        valid_candidates = verify_ground_truth(candidates)
        
        if not valid_candidates:
            # verify_ground_truth should raise if empty, but double check
            raise GroundTruthSchemaMissingError(
                "Verification passed but no candidates remain. This is unexpected."
            )
        
        # Convert paths to strings for JSON serialization
        candidate_paths_str = [str(p) for p in valid_candidates]
        
        # Output to stdout
        print(f"Found {len(valid_candidates)} candidate file(s):")
        for p in valid_candidates:
            print(f"  - {p}")
        
        # Write report
        report = {
            "status": "success",
            "timestamp": str(Path(__file__).parent.parent.parent), # Placeholder for real timestamp if needed
            "search_directory": str(raw_guava_dir),
            "target_keys": ["annotations", "bboxes", "objects"],
            "candidates": candidate_paths_str,
            "count": len(valid_candidates)
        }
        
        with open(output_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report written to: {output_report}")
        return 0

    except GroundTruthSchemaMissingError as e:
        print(f"Error: {e}")
        # Write failure report
        failure_report = {
            "status": "failed",
            "error": str(e),
            "candidates": []
        }
        with open(output_report, 'w', encoding='utf-8') as f:
            json.dump(failure_report, f, indent=2)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
