"""
Flagging Logic for Unstructured PSD Entries (T014b).

This module implements the logic to flag unstructured entries to data/flagged_psd.json
with the specific schema: experiment_id, source, issue_type, raw_blob_hash.

It is designed to run after T014a (image detection) has identified potential PSD images
that require manual curation or OCR fallback.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

# Output path defined in tasks.md
FLAGGED_OUTPUT_PATH = Path("data/flagged_psd.json")

def compute_blob_hash(data: bytes) -> str:
    """
    Compute a SHA-256 hash of the raw binary data.

    Args:
        data (bytes): The raw binary content to hash.

    Returns:
        str: Hexadecimal string of the SHA-256 hash.
    """
    return hashlib.sha256(data).hexdigest()

def flag_entry(
    experiment_id: str,
    source: str,
    issue_type: str,
    raw_data: bytes,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a flagged entry record.

    Args:
        experiment_id (str): Unique identifier for the experiment.
        source (str): Name of the data source (e.g., 'Materials Project', 'arXiv').
        issue_type (str): Type of issue detected (e.g., 'unstructured_psd_image').
        raw_data (bytes): The raw binary content (e.g., image bytes) for hashing.
        metadata (dict, optional): Additional context.

    Returns:
        dict: A dictionary conforming to the required schema.
    """
    raw_blob_hash = compute_blob_hash(raw_data)

    entry = {
        "experiment_id": experiment_id,
        "source": source,
        "issue_type": issue_type,
        "raw_blob_hash": raw_blob_hash,
    }

    if metadata:
        entry["metadata"] = metadata

    logger.info(
        f"Flagged entry: experiment_id={experiment_id}, "
        f"source={source}, issue_type={issue_type}, hash={raw_blob_hash[:16]}..."
    )

    return entry

def run_flagging_pipeline(
    detected_images: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Process detected images from T014a and generate flagged entries.

    Args:
        detected_images (list): List of dicts from image detector containing
                                'file_path', 'experiment_id', 'source', etc.
        output_path (Path, optional): Path to write the JSON output. Defaults to FLAGGED_OUTPUT_PATH.

    Returns:
        list: The list of flagged entries generated.
    """
    if output_path is None:
        output_path = FLAGGED_OUTPUT_PATH

    flagged_entries = []

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for item in detected_images:
        file_path = item.get("file_path")
        experiment_id = item.get("experiment_id", "unknown")
        source = item.get("source", "unknown")

        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Skipping missing file: {file_path}")
            continue

        try:
            with open(file_path, "rb") as f:
                raw_bytes = f.read()

            entry = flag_entry(
                experiment_id=experiment_id,
                source=source,
                issue_type="unstructured_psd_image",
                raw_data=raw_bytes,
                metadata={
                    "original_file": file_path,
                    "page_number": item.get("page_number"),
                    "detection_score": item.get("detection_score"),
                },
            )
            flagged_entries.append(entry)

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
            # Continue processing other entries (fail loud per entry, but don't crash pipeline)

    # Write to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flagged_entries, f, indent=2)

    logger.info(f"Flagged {len(flagged_entries)} entries written to {output_path}")
    return flagged_entries

def main():
    """
    Entry point for running the flagging pipeline as a script.
    Expects a JSON file of detected images (from T014a) as input argument.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest.flag_psd_entries <path_to_detected_images_json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading detected images from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        detected_images = json.load(f)

    run_flagging_pipeline(detected_images)
    logger.info("Flagging pipeline completed.")

if __name__ == "__main__":
    main()
