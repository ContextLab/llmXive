"""
Script to filter invalid DAG traces from the manifest.

This script reads the `data/processed/dag_manifest.json`, removes entries
where `is_valid` is False (indicating cycles or structural invalidity),
updates the metadata counts, and writes the cleaned manifest back to disk.

It ensures that downstream prompt generation (US2) only processes valid traces.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import from the project's parser_utils to ensure consistent I/O
from code.src.parser_utils import load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "processed" / "dag_manifest.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "dag_manifest.json"

def load_manifest(path: Path) -> Dict[str, Any]:
    """Load the DAG manifest from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    
    logger.info(f"Loading manifest from {path}")
    data = load_json_file(path)
    
    if "entries" not in data:
        raise ValueError("Manifest missing 'entries' key")
    
    return data

def filter_invalid_entries(manifest_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int, int]:
    """
    Filter out invalid entries from the manifest.
    
    Returns:
        Tuple of (updated_manifest, count_removed, count_kept)
    """
    entries = manifest_data.get("entries", [])
    valid_entries = [e for e in entries if e.get("is_valid", False)]
    invalid_entries = [e for e in entries if not e.get("is_valid", False)]
    
    count_removed = len(invalid_entries)
    count_kept = len(valid_entries)
    
    if count_removed > 0:
        logger.warning(f"Removing {count_removed} invalid entries due to cycles or structural issues.")
        for inv in invalid_entries:
            logger.debug(f"  Removed: {inv.get('example_id')} (reason: invalid DAG structure)")
    else:
        logger.info("No invalid entries found. All traces are valid.")

    # Update the entries list
    manifest_data["entries"] = valid_entries

    # Update metadata
    if "metadata" in manifest_data:
        manifest_data["metadata"]["total_entries"] = len(entries)
        manifest_data["metadata"]["valid_entries"] = count_kept
        manifest_data["metadata"]["invalid_entries"] = count_removed
    
    return manifest_data, count_removed, count_kept

def save_manifest(manifest_data: Dict[str, Any], path: Path) -> None:
    """Save the filtered manifest back to JSON."""
    logger.info(f"Saving filtered manifest to {path}")
    save_json_file(path, manifest_data)
    logger.info("Manifest saved successfully.")

def main() -> int:
    """Main entry point for the script."""
    try:
        # Load
        manifest = load_manifest(MANIFEST_PATH)
        
        # Filter
        filtered_manifest, removed, kept = filter_invalid_entries(manifest)
        
        # Save
        save_manifest(filtered_manifest, OUTPUT_PATH)
        
        logger.info(f"Filter complete. Kept: {kept}, Removed: {removed}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
