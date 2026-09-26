"""
Subject Filtering & N=50 Enforcement

Implements T015: Load validated metadata, filter for subjects with "dream recall frequency",
sort by subject ID ascending, select the first 50 valid subjects, and generate
data/raw/valid_subjects.json. Raise FatalError if fewer than 50 valid subjects are found.
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project API surface
from utils.config import get_config_summary

class FatalError(Exception):
    """Exception raised for fatal configuration or data errors that halt execution."""
    pass

def load_validated_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """
    Load the validated metadata JSON file produced by T014.
    
    Args:
        metadata_path: Path to the validated metadata JSON file.
        
    Returns:
        List of subject metadata dictionaries.
        
    Raises:
        FileNotFoundError: If the metadata file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Validated metadata file not found: {metadata_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'subjects' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'subjects' in data:
        return data['subjects']
    else:
        raise ValueError(f"Unexpected metadata format in {metadata_path}. Expected list or dict with 'subjects' key.")

def filter_subjects_with_dream_recall(subjects: List[Dict[str, Any]], field_name: str = "dream_recall_frequency") -> List[Dict[str, Any]]:
    """
    Filter subjects that have the specified dream recall frequency field.
    
    Args:
        subjects: List of subject metadata dictionaries.
        field_name: The name of the field to check for existence and validity.
        
    Returns:
        List of subjects that have a valid (non-null) dream recall frequency value.
    """
    valid_subjects = []
    for subject in subjects:
        if field_name in subject and subject[field_name] is not None:
            # Ensure the value is numeric
            try:
                float(subject[field_name])
                valid_subjects.append(subject)
            except (ValueError, TypeError):
                # Skip subjects with non-numeric values
                continue
    return valid_subjects

def sort_and_select_subjects(subjects: List[Dict[str, Any]], target_count: int = 50) -> List[Dict[str, Any]]:
    """
    Sort subjects by subject ID ascending and select the first N subjects.
    
    Args:
        subjects: List of subject metadata dictionaries.
        target_count: Number of subjects to select (default 50).
        
    Returns:
        List of up to target_count subjects, sorted by subject_id.
        
    Raises:
        FatalError: If fewer than target_count valid subjects are found.
    """
    # Sort by subject_id ascending
    # Handle various possible subject ID field names
    id_field = None
    for key in ['subject_id', 'sub_id', 'id', 'participant_id']:
        if subjects and key in subjects[0]:
            id_field = key
            break
    
    if id_field is None:
        # Fallback: try to use any field that looks like an ID
        if subjects:
            sample_keys = list(subjects[0].keys())
            if sample_keys:
                id_field = sample_keys[0]
            else:
                raise FatalError("No identifiable subject ID field found in metadata")
        else:
            raise FatalError("No subjects to sort")
    
    sorted_subjects = sorted(subjects, key=lambda x: str(x.get(id_field, '')))
    
    if len(sorted_subjects) < target_count:
        raise FatalError(f"Insufficient subjects for N={target_count} target")
    
    return sorted_subjects[:target_count]

def save_valid_subjects(subjects: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the selected subjects to a JSON file.
    
    Args:
        subjects: List of subject metadata dictionaries to save.
        output_path: Path where the JSON file should be written.
        
    Raises:
        IOError: If the file cannot be written.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(subjects, f, indent=2)
    
    print(f"Saved {len(subjects)} valid subjects to {output_path}")

def main():
    """
    Main entry point for the subject filtering pipeline.
    
    This function:
    1. Loads validated metadata from data/raw/validated_metadata.json
    2. Filters for subjects with valid dream recall frequency
    3. Sorts by subject ID and selects the first 50
    4. Saves the result to data/raw/valid_subjects.json
    5. Raises FatalError if fewer than 50 valid subjects are found
    """
    # Configuration
    config = get_config_summary()
    metadata_path = config.get('metadata_path', 'data/raw/validated_metadata.json')
    output_path = config.get('valid_subjects_path', 'data/raw/valid_subjects.json')
    target_count = config.get('target_subject_count', 50)
    
    print(f"Starting subject filtering (Target N={target_count})...")
    print(f"Loading metadata from: {metadata_path}")
    
    try:
        # Step 1: Load validated metadata
        subjects = load_validated_metadata(metadata_path)
        print(f"Loaded {len(subjects)} total subjects from metadata")
        
        # Step 2: Filter for subjects with dream recall frequency
        filtered_subjects = filter_subjects_with_dream_recall(subjects)
        print(f"Found {len(filtered_subjects)} subjects with valid dream recall frequency")
        
        # Step 3: Sort and select
        selected_subjects = sort_and_select_subjects(filtered_subjects, target_count)
        print(f"Selected {len(selected_subjects)} subjects for processing")
        
        # Step 4: Save results
        save_valid_subjects(selected_subjects, output_path)
        
        # Verify output
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        if len(saved_data) != target_count:
            raise FatalError(f"Output verification failed: expected {target_count} subjects, got {len(saved_data)}")
        
        print(f"SUCCESS: Generated {output_path} with exactly {target_count} subjects")
        return 0
        
    except FatalError as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        raise
    except FileNotFoundError as e:
        print(f"FILE NOT FOUND ERROR: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    sys.exit(main() if main() == 0 else 1)