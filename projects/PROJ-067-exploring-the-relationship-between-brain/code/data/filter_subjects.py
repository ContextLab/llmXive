"""
T015: Subject Filtering & N=50 Enforcement

Loads validated metadata, filters for subjects with "dream recall frequency",
sorts by subject ID, selects the first 50 valid subjects, and saves to
data/raw/valid_subjects.json. Raises FatalError if fewer than 50 are found.
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.config import get_config_summary

# Constants
TARGET_N = 50
DREAM_RECALL_FIELD = "dream recall frequency"
VALIDATED_METADATA_PATH = Path("data/raw/validated_metadata.json")
OUTPUT_PATH = Path("data/raw/valid_subjects.json")


class FatalError(Exception):
    """Custom exception for fatal pipeline errors that must halt execution."""
    pass


def load_validated_metadata(path: Path) -> List[Dict[str, Any]]:
    """
    Load the validated metadata JSON file produced by T014.
    
    Args:
        path: Path to the validated_metadata.json file.
        
    Returns:
        List of subject metadata dictionaries.
        
    Raises:
        FileNotFoundError: If the metadata file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Validated metadata file not found at {path}. "
            "Please ensure T014 (validate_metadata.py) has run successfully."
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle case where data might be a dict with a 'subjects' key or a direct list
    if isinstance(data, dict):
        if 'subjects' in data:
            return data['subjects']
        # If it's a single object wrapped in a dict, return as list
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected metadata format in {path}: {type(data)}")


def filter_subjects_with_dream_recall(subjects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter subjects that have the 'dream recall frequency' field present and not null.
    
    Args:
        subjects: List of subject metadata dictionaries.
        
    Returns:
        List of subjects containing the required field.
    """
    valid_subjects = []
    for subj in subjects:
        # Check if the key exists and is not None
        if DREAM_RECALL_FIELD in subj and subj[DREAM_RECALL_FIELD] is not None:
            # Ensure the value is numeric (int or float) if present
            val = subj[DREAM_RECALL_FIELD]
            if isinstance(val, (int, float)):
                valid_subjects.append(subj)
    return valid_subjects


def sort_and_select_subjects(subjects: List[Dict[str, Any]], n: int = TARGET_N) -> List[Dict[str, Any]]:
    """
    Sort subjects by subject ID ascending and select the first n subjects.
    
    Args:
        subjects: List of subject metadata dictionaries.
        n: Number of subjects to select.
        
    Returns:
        List of the first n sorted subjects.
        
    Raises:
        FatalError: If fewer than n subjects are available.
    """
    # Sort by subject ID. Assuming 'subject_id' or 'participant_id' key exists.
    # We try common keys, defaulting to sorting by the first key that looks like an ID.
    def get_sort_key(subj):
        for key in ['subject_id', 'participant_id', 'id', 'sub_id']:
            if key in subj:
                return str(subj[key])
        # Fallback: sort by the whole dict string representation if no ID found
        return str(subj)

    sorted_subjects = sorted(subjects, key=get_sort_key)
    
    if len(sorted_subjects) < n:
        raise FatalError(
            f"Insufficient subjects for N={n} target. "
            f"Found {len(sorted_subjects)} valid subjects with 'dream recall frequency'."
        )
    
    return sorted_subjects[:n]


def save_valid_subjects(subjects: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the selected subjects to a JSON file.
    
    Args:
        subjects: List of subject metadata dictionaries to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "n_subjects": len(subjects),
        "target_n": TARGET_N,
        "subjects": subjects
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Successfully saved {len(subjects)} subjects to {output_path}")


def main():
    """Main entry point for T015."""
    config = get_config_summary()
    print(f"Starting T015: Subject Filtering & N=50 Enforcement")
    print(f"Config: {config}")
    
    try:
        # 1. Load validated metadata from T014
        print(f"Loading validated metadata from {VALIDATED_METADATA_PATH}...")
        all_subjects = load_validated_metadata(VALIDATED_METADATA_PATH)
        print(f"Loaded {len(all_subjects)} total subjects.")
        
        # 2. Filter for subjects with 'dream recall frequency'
        print(f"Filtering for subjects with '{DREAM_RECALL_FIELD}'...")
        filtered_subjects = filter_subjects_with_dream_recall(all_subjects)
        print(f"Found {len(filtered_subjects)} subjects with 'dream recall frequency'.")
        
        # 3. Sort and select top N
        print(f"Selecting first {TARGET_N} subjects...")
        selected_subjects = sort_and_select_subjects(filtered_subjects, TARGET_N)
        
        # 4. Save to output file
        print(f"Saving to {OUTPUT_PATH}...")
        save_valid_subjects(selected_subjects, OUTPUT_PATH)
        
        print("T015 completed successfully.")
        
    except FatalError as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"FILE NOT FOUND ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
