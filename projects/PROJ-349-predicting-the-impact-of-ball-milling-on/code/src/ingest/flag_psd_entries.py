"""
Flagging logic for unstructured PSD entries (images detected by T014a).
Produces data/flagged_psd.json with schema:
[
  {
    "experiment_id": str,
    "source": str,
    "issue_type": str,
    "raw_blob_hash": str
  }
]
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

FLAGGED_OUTPUT_PATH = Path("data/flagged_psd.json")
DETECTED_IMAGES_INPUT_PATH = Path("data/raw/detected_psd_images.json")


def compute_blob_hash(file_path: str) -> str:
    """
    Compute SHA256 hash of the file content.
    Used to uniquely identify the raw blob for manual review.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise


def flag_entry(
    image_path: str,
    source_name: str,
    source_id: str,
    issue_type: str = "unstructured_psd_image"
) -> Dict[str, Any]:
    """
    Create a flagged entry record for manual curation or OCR fallback.
    
    Args:
        image_path: Path to the detected PSD image.
        source_name: Name of the data source (e.g., "Materials Project", "arXiv").
        source_id: Unique identifier from the source.
        issue_type: Type of issue detected (default: "unstructured_psd_image").
        
    Returns:
        Dictionary with schema: experiment_id, source, issue_type, raw_blob_hash.
    """
    # Derive experiment_id from source_id and source_name if not explicitly provided
    # Using a hash of the combination to ensure uniqueness
    exp_id_str = f"{source_name}_{source_id}_{os.path.basename(image_path)}"
    experiment_id = hashlib.md5(exp_id_str.encode()).hexdigest()[:12]
    
    raw_blob_hash = compute_blob_hash(image_path)
    
    return {
        "experiment_id": experiment_id,
        "source": source_name,
        "issue_type": issue_type,
        "raw_blob_hash": raw_blob_hash,
        "image_path": image_path, # Included for reference, though schema focuses on hash
        "source_id": source_id
    }


def run_flagging_pipeline() -> List[Dict[str, Any]]:
    """
    Main entry point to run the flagging pipeline.
    
    Reads detected images from data/raw/detected_psd_images.json.
    For each entry, extracts metadata (source, source_id) and flags it.
    Writes results to data/flagged_psd.json.
    
    Returns:
        List of flagged entry dictionaries.
    """
    if not DETECTED_IMAGES_INPUT_PATH.exists():
        logger.warning(f"Input file not found: {DETECTED_IMAGES_INPUT_PATH}. Skipping flagging.")
        # Create empty output file to satisfy artifact requirement
        FLAGGED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FLAGGED_OUTPUT_PATH, "w") as f:
            json.dump([], f)
        return []

    logger.info(f"Reading detected images from {DETECTED_IMAGES_INPUT_PATH}")
    with open(DETECTED_IMAGES_INPUT_PATH, "r") as f:
        detected_data = json.load(f)

    if not isinstance(detected_data, list):
        logger.error(f"Expected list in {DETECTED_IMAGES_INPUT_PATH}, got {type(detected_data)}")
        raise ValueError("Detected images file must contain a list of entries.")

    flagged_entries = []
    
    for idx, entry in enumerate(detected_data):
        image_path = entry.get("image_path")
        source_name = entry.get("source_name")
        source_id = entry.get("source_id")
        
        if not image_path or not source_name or not source_id:
            logger.warning(f"Entry {idx} missing required metadata (image_path, source_name, source_id). Skipping.")
            continue
        
        if not os.path.exists(image_path):
            logger.warning(f"Image file not found: {image_path}. Skipping.")
            continue
        
        try:
            flagged_entry = flag_entry(
                image_path=image_path,
                source_name=source_name,
                source_id=source_id,
                issue_type="unstructured_psd_image"
            )
            flagged_entries.append(flagged_entry)
            logger.info(f"Flagged entry: {flagged_entry['experiment_id']} from {source_name}")
        except Exception as e:
            logger.error(f"Failed to flag entry {idx}: {e}")
            # Continue processing other entries

    # Ensure output directory exists
    FLAGGED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write flagged entries to JSON
    with open(FLAGGED_OUTPUT_PATH, "w") as f:
        json.dump(flagged_entries, f, indent=2)
    
    logger.info(f"Flagging pipeline complete. {len(flagged_entries)} entries written to {FLAGGED_OUTPUT_PATH}")
    return flagged_entries


def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_flagging_pipeline()


if __name__ == "__main__":
    main()
