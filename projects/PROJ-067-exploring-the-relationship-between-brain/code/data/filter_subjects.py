"""
T015: Subject Filtering & N=50 Enforcement

Loads validated metadata, filters for subjects with 'dream recall frequency',
sorts by subject ID, selects the first 50 valid subjects, and writes
data/raw/valid_subjects.json.
Raises FatalError if fewer than 50 valid subjects are found.
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import the validation error from the sibling module to maintain consistency
# though we define our own FatalError for this specific logic.
from data.validate_metadata import MetadataValidationError

logger = logging.getLogger(__name__)

class FatalError(Exception):
    """Critical error that halts execution."""
    pass

def load_validated_metadata(metadata_path: Path) -> List[Dict[str, Any]]:
    """Load the validated metadata JSON file produced by T014."""
    if not metadata_path.exists():
        raise FatalError(f"Validated metadata file not found at {metadata_path}. "
                         "Ensure T014 (validate_metadata.py) has run successfully.")
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise FatalError(f"Failed to parse JSON from {metadata_path}: {e}")
    
    # Handle both list format and dict with 'participants' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'participants' in data:
        return data['participants']
    else:
        # Fallback: assume the whole file is the list of participants
        # or raise error if structure is unexpected
        if isinstance(data, dict):
            # If it's a single object, wrap it or try to find a list
            return [data] 
        return data

def filter_subjects_by_drf(participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter participants that have a 'dream_recall_frequency' field."""
    valid = []
    for p in participants:
        if 'dream_recall_frequency' in p and p['dream_recall_frequency'] is not None:
            valid.append(p)
        else:
            logger.debug(f"Skipping subject {p.get('participant_id', 'unknown')}: missing dream_recall_frequency")
    return valid

def sort_and_truncate(participants: List[Dict[str, Any]], target_n: int = 50) -> List[Dict[str, Any]]:
    """Sort by subject ID ascending and truncate to target_n."""
    # Sort by participant_id (string sort is usually fine for OpenNeuro IDs like sub-01)
    sorted_participants = sorted(
        participants, 
        key=lambda x: x.get('participant_id', '')
    )
    
    if len(sorted_participants) < target_n:
        raise FatalError(f"Insufficient subjects for N={target_n} target. "
                         f"Found {len(sorted_participants)} valid subjects with dream recall frequency.")
    
    return sorted_participants[:target_n]

def save_valid_subjects(subjects: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the filtered list to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(subjects, f, indent=2)
    logger.info(f"Saved {len(subjects)} subjects to {output_path}")

def main() -> None:
    """Entry point for T015."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Define paths relative to project root
    # Assuming this script runs from the project root or code/ directory
    # We use relative paths that resolve from the script's perspective if run from root
    # or we can use absolute paths based on __file__
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    metadata_path = project_root / "data" / "raw" / "validated_metadata.json"
    output_path = project_root / "data" / "raw" / "valid_subjects.json"

    logger.info(f"Loading validated metadata from {metadata_path}")
    
    try:
        # 1. Load
        all_participants = load_validated_metadata(metadata_path)
        logger.info(f"Loaded {len(all_participants)} total participants.")

        # 2. Filter
        valid_participants = filter_subjects_by_drf(all_participants)
        logger.info(f"Found {len(valid_participants)} participants with dream recall frequency.")

        # 3. Sort and Truncate
        final_subjects = sort_and_truncate(valid_participants, target_n=50)
        
        # 4. Save
        save_valid_subjects(final_subjects, output_path)
        
        logger.info("T015 completed successfully. 50 subjects selected.")

    except FatalError as e:
        logger.error(f"CRITICAL: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
