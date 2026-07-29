"""
Ingestion pipeline for MedMisBench dataset.
Downloads, filters, and validates the dataset with schema inspection.
"""
import os
import hashlib
import csv
import yaml
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import datasets
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "MedMisBench/MedMisBench"
FILTER_LABELS = ["Authority-framed", "Exception-poisoning"]
REQUIRED_COLUMNS = ["prompt_id", "prompt", "false_claim"]
OUTPUT_PATH = "data/raw/medmis_subset.csv"
STATE_PATH = "state/artifact_hashes.yaml"
CHECKSUM_KEY = "medmis_subset_csv"

def extract_false_claim_from_text(text: str) -> Optional[str]:
    """
    Fallback regex extraction for false_claim if column is missing.
    Looks for patterns like "False claim: ..." or "Misinformation: ..."
    """
    import re
    patterns = [
        r"(?i)false\s*claim[:\s]+(.+?)(?:\n|$)",
        r"(?i)misinformation[:\s]+(.+?)(?:\n|$)",
        r"(?i)incorrect[:\s]+(.+?)(?:\n|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None

def load_and_filter_dataset() -> List[Dict[str, Any]]:
    """
    Download MedMisBench via streaming and filter for specific labels.
    """
    logger.info(f"Loading dataset: {DATASET_NAME} with streaming=True")
    try:
        dataset = load_dataset(DATASET_NAME, streaming=True)
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise RuntimeError(f"Dataset download failed: {e}")

    # Determine which split to use (usually 'train' or the only available split)
    split_name = list(dataset.keys())[0]
    logger.info(f"Using split: {split_name}")

    filtered_rows = []
    logger.info(f"Filtering for labels: {FILTER_LABELS}")

    for idx, row in enumerate(dataset[split_name]):
        # Check if row has the expected structure
        if "label" not in row:
            logger.warning(f"Row {idx} missing 'label' field, skipping")
            continue

        label = row.get("label", "")
        if label in FILTER_LABELS:
            filtered_rows.append(row)

        # Progress logging
        if idx % 1000 == 0 and idx > 0:
            logger.info(f"Processed {idx} rows, collected {len(filtered_rows)} so far")

    if len(filtered_rows) == 0:
        raise RuntimeError("No rows matched the filter criteria. Check label values in dataset.")

    logger.info(f"Successfully filtered {len(filtered_rows)} rows")
    return filtered_rows

def validate_schema(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Explicitly check for 'false_claim' column.
    If missing, attempt regex extraction.
    If extraction fails, abort.
    """
    logger.info("Validating schema...")
    valid_rows = []
    missing_false_claim_count = 0

    # Check first row for column existence
    if rows:
        first_row = rows[0]
        has_false_claim_col = "false_claim" in first_row

        if not has_false_claim_col:
            logger.warning("'false_claim' column not found. Attempting regex extraction fallback.")

    for idx, row in enumerate(rows):
        if "false_claim" not in row:
            extracted = extract_false_claim_from_text(row.get("prompt", ""))
            if extracted:
                row["false_claim"] = extracted
                missing_false_claim_count += 1
            else:
                logger.error(f"Row {idx}: Could not extract false_claim from prompt text. Aborting.")
                raise RuntimeError(f"Schema validation failed: Row {idx} missing 'false_claim' and extraction failed.")

        valid_rows.append(row)

    if missing_false_claim_count > 0:
        logger.info(f"Extracted 'false_claim' for {missing_false_claim_count} rows via regex fallback.")

    logger.info("Schema validation passed.")
    return valid_rows

def save_to_csv(rows: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save filtered and validated rows to CSV.
    """
    logger.info(f"Saving to {output_path}")
    if not rows:
        raise RuntimeError("No data to save.")

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Determine fieldnames from first row
    fieldnames = list(rows[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Saved {len(rows)} rows to {output_path}")

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum_to_state(checksum: str, output_path: str) -> None:
    """
    Record checksum in state/artifact_hashes.yaml.
    """
    state_dir = os.path.dirname(STATE_PATH)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)

    checksum_key = CHECKSUM_KEY
    file_name = os.path.basename(output_path)

    # Load existing state if present
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r") as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {}

    # Update state
    state[checksum_key] = {
        "file": file_name,
        "checksum": checksum,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Write state
    with open(STATE_PATH, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

    logger.info(f"Saved checksum to {STATE_PATH}")

def run_ingestion_pipeline() -> str:
    """
    Execute the full ingestion pipeline.
    Returns the path to the output CSV.
    """
    logger.info("Starting ingestion pipeline...")

    # Step 1: Load and filter
    rows = load_and_filter_dataset()

    # Step 2: Validate schema
    validated_rows = validate_schema(rows)

    # Step 3: Save to CSV
    save_to_csv(validated_rows, OUTPUT_PATH)

    # Step 4: Compute and save checksum
    checksum = compute_sha256(OUTPUT_PATH)
    save_checksum_to_state(checksum, OUTPUT_PATH)

    logger.info("Ingestion pipeline completed successfully.")
    return OUTPUT_PATH

def main():
    """
    Entry point for ingestion script.
    """
    try:
        output_path = run_ingestion_pipeline()
        logger.info(f"Output written to: {output_path}")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()