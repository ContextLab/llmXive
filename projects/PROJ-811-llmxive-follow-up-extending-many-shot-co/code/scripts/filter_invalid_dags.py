"""
Script to filter invalid traces (cycles) from the DAG manifest.

This script loads data/processed/dag_manifest.json, identifies entries
flagged as invalid (due to cycles or other structural issues), removes
them from the manifest, and writes the cleaned manifest back to disk.

It also updates the manifest metadata to reflect the filtering operation.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.parser_utils import load_json_file, save_json_file
from src.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the DAG manifest from disk."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    logger.info(f"Loading manifest from {manifest_path}")
    return load_json_file(manifest_path)

def filter_invalid_entries(manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Filter out invalid entries from the manifest.
    
    Invalid entries are those marked with 'is_valid': False or 
    containing 'cycle_detected': True.
    
    Returns:
        Tuple of (filtered_manifest, list of removed trace_ids)
    """
    entries = manifest.get("entries", [])
    valid_entries = []
    removed_ids = []
    
    logger.info(f"Processing {len(entries)} entries in manifest")
    
    for entry in entries:
        trace_id = entry.get("trace_id", "unknown")
        is_valid = entry.get("is_valid", True)
        cycle_detected = entry.get("cycle_detected", False)
        
        # An entry is invalid if explicitly marked invalid OR if a cycle was detected
        if not is_valid or cycle_detected:
            removed_ids.append(trace_id)
            logger.debug(f"Removing invalid trace: {trace_id} "
                       f"(is_valid={is_valid}, cycle_detected={cycle_detected})")
        else:
            valid_entries.append(entry)
    
    # Create filtered manifest
    filtered_manifest = manifest.copy()
    filtered_manifest["entries"] = valid_entries
    filtered_manifest["metadata"] = filtered_manifest.get("metadata", {})
    filtered_manifest["metadata"]["filtered_count"] = len(removed_ids)
    filtered_manifest["metadata"]["valid_count"] = len(valid_entries)
    filtered_manifest["metadata"]["removed_trace_ids"] = removed_ids
    
    logger.info(f"Filtered manifest: {len(removed_ids)} invalid entries removed, "
               f"{len(valid_entries)} valid entries remaining")
    
    return filtered_manifest, removed_ids

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save the filtered manifest to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json_file(manifest, output_path)
    logger.info(f"Saved filtered manifest to {output_path}")

def main():
    """Main entry point for the filtering script."""
    config = get_config()
    processed_dir = config.get_processed_dir()
    manifest_path = processed_dir / "dag_manifest.json"
    output_path = processed_dir / "dag_manifest_filtered.json"
    
    try:
        # Load manifest
        manifest = load_manifest(manifest_path)
        
        # Filter invalid entries
        filtered_manifest, removed_ids = filter_invalid_entries(manifest)
        
        # Save filtered manifest
        save_manifest(filtered_manifest, output_path)
        
        # Log summary
        logger.info("Filtering complete!")
        logger.info(f"  - Input: {manifest_path}")
        logger.info(f"  - Output: {output_path}")
        logger.info(f"  - Removed {len(removed_ids)} invalid traces")
        logger.info(f"  - Remaining {filtered_manifest['metadata']['valid_count']} valid traces")
        
        if removed_ids:
            logger.info("Removed trace IDs:")
            for trace_id in removed_ids[:10]:  # Show first 10
                logger.info(f"    - {trace_id}")
            if len(removed_ids) > 10:
                logger.info(f"    ... and {len(removed_ids) - 10} more")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during filtering: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
