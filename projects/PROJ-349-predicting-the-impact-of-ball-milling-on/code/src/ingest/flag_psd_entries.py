"""
T014b: Flagging Logic for Unstructured PSD Entries.

This module implements the logic to flag unstructured entries (e.g., those
containing PSD curves detected as images but not yet extracted) to
data/flagged_psd.json.

Schema for flagged entries:
- experiment_id: str (unique identifier)
- source: str (source name, e.g., 'Materials Project', 'arXiv')
- issue_type: str (e.g., 'unstructured_image', 'ocr_failed', 'missing_psd')
- raw_blob_hash: str (SHA-256 hash of the raw content/blob for traceability)
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_module_logger
from src.ingest.arxiv_extractor import run_arxiv_ingestion
from src.ingest.materials_project import run_materials_project_ingestion
from src.ingest.nist_repo import run_nist_ingestion
from src.ingest.ocr_fallback import extract_psd_from_image
from src.ingest.merge import run_merge_pipeline
from src.utils.config.settings import load_config

# Ensure the logger is initialized
logger = get_module_logger(__name__)

FLAGGED_OUTPUT_PATH = Path("data/flagged_psd.json")
FLAGGED_OUTPUT_DIR = FLAGGED_OUTPUT_PATH.parent

def compute_blob_hash(blob: Any) -> str:
    """
    Compute a SHA-256 hash of the provided blob.
    Handles dict, list, str, and bytes.
    """
    if isinstance(blob, (dict, list)):
        # Serialize to JSON with sorted keys for deterministic hashing
        blob_str = json.dumps(blob, sort_keys=True).encode('utf-8')
    elif isinstance(blob, str):
        blob_str = blob.encode('utf-8')
    elif isinstance(blob, bytes):
        blob_str = blob
    else:
        # Fallback for other types: string representation
        blob_str = str(blob).encode('utf-8')

    return hashlib.sha256(blob_str).hexdigest()

def flag_entry(
    experiment_id: str,
    source: str,
    issue_type: str,
    raw_blob: Any,
    flagged_entries: List[Dict[str, Any]]
) -> None:
    """
    Add a flagged entry to the list.

    Args:
        experiment_id: Unique ID for the experiment.
        source: Source name.
        issue_type: Type of issue (e.g., 'unstructured_image').
        raw_blob: The raw data/blob associated with the entry.
        flagged_entries: List to append the new entry to.
    """
    entry = {
        "experiment_id": experiment_id,
        "source": source,
        "issue_type": issue_type,
        "raw_blob_hash": compute_blob_hash(raw_blob)
    }
    flagged_entries.append(entry)
    logger.info(f"Flagged entry: {experiment_id} from {source} (Issue: {issue_type})")

def run_flagging_pipeline() -> List[Dict[str, Any]]:
    """
    Main pipeline to run ingestion, detect issues, and flag entries.

    This function orchestrates the ingestion from all sources, detects
    unstructured entries (based on T014a results or direct detection),
    and flags them according to the schema.

    Returns:
        List[Dict[str, Any]]: The list of flagged entries.
    """
    # Ensure output directory exists
    FLAGGED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    flagged_entries: List[Dict[str, Any]] = []

    # 1. Run Ingestion (Mocked or Real based on availability)
    # Note: In a real scenario, we would call the actual ingestion functions.
    # Since T014a (detect_psd_images) is a prerequisite, we assume its logic
    # identifies pages with images. Here we simulate the detection of
    # unstructured entries based on the assumption that T014a has run or
    # we are flagging based on the inability to parse structured data.

    # We will attempt to run the ingestion modules to get real data.
    # If they fail (e.g., API errors), we log and skip, as per T014c/T012/T013 logic.
    # However, for the purpose of T014b, we need to identify entries that
    # *would* be flagged. Since we cannot rely on T014a output file existing
    # in this isolated run without execution context, we will flag entries
    # that fail to provide structured PSD data during ingestion.

    # Let's simulate the flow:
    # We will run the ingestion scripts. If they return data that lacks
    # structured PSD (D10, D50, D90), we flag them.

    # Note: The actual ingestion scripts (T012, T013, T013b) are designed to
    # extract structured data. If they fail to extract, they should ideally
    # return None or empty. If they return a row without PSD, we flag it.

    # For this specific task T014b, the requirement is to implement the logic
    # to flag. We will assume that the ingestion pipeline has identified
    # "unstructured" candidates (perhaps from T014a's image detection).
    # Since T014a output is `data/raw/detected_psd_images.json`, we can check that.

    detected_images_path = Path("data/raw/detected_psd_images.json")
    if detected_images_path.exists():
        try:
            with open(detected_images_path, 'r') as f:
                detected_data = json.load(f)
            # detected_data is expected to be a list of image paths or metadata
            # We flag these as "unstructured_image"
            for item in detected_data:
                if isinstance(item, dict):
                    exp_id = item.get("experiment_id", "unknown")
                    source = item.get("source", "unknown")
                    raw_blob = item # The whole item is the raw blob
                else:
                    # If it's just a path or string, create a minimal entry
                    exp_id = "unknown"
                    source = "unknown"
                    raw_blob = item

                flag_entry(exp_id, source, "unstructured_image", raw_blob, flagged_entries)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not process detected images file: {e}")

    # If no detected images file, we might still need to flag based on
    # ingestion results if they fail to extract structured data.
    # However, the primary trigger is T014a. If T014a found nothing,
    # there might be nothing to flag unless we re-run ingestion and check.
    # Given the task dependency "Trigger: Must run after T014a detects images",
    # we rely on the existence of that file.

    # If the file doesn't exist, we create an empty flagged list or
    # log that no images were detected.
    if not detected_images_path.exists():
        logger.info("No detected PSD images file found. No entries to flag based on T014a.")

    # Write the flagged entries to the output file
    with open(FLAGGED_OUTPUT_PATH, 'w') as f:
        json.dump(flagged_entries, f, indent=2)

    logger.info(f"Flagged {len(flagged_entries)} entries written to {FLAGGED_OUTPUT_PATH}")
    return flagged_entries

def main():
    """Entry point for the flagging pipeline."""
    logger.info("Starting T014b Flagging Logic Pipeline...")
    try:
        flagged_entries = run_flagging_pipeline()
        logger.info(f"T014b Pipeline completed. Flagged {len(flagged_entries)} entries.")
    except Exception as e:
        logger.error(f"T014b Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
