"""
Metadata Validation (Phase 0 Gate) for ds000228.

This script fetches the participant-level metadata for the OpenNeuro dataset
ds000228 (Dream Recall Frequency study), verifies the existence of the
'dream_recall_frequency' field, and halts execution if the field is missing.

It implements FR-001 and Plan Phase 0 requirements.
"""

import json
import sys
import os
from pathlib import Path

import requests

# Add project root to path for imports if running as script
# Note: In a real environment, ensure code/ is in sys.path or use -m
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_config_summary

# Constants
DATASET_ID = "ds000228"
OPENNEURO_API_URL = f"https://api.openneuro.org/datasets/{DATASET_ID}/files"
PARTICIPANT_METADATA_URL = f"https://api.openneuro.org/datasets/{DATASET_ID}/files/participants.tsv"
PARTICIPANT_JSON_URL = f"https://api.openneuro.org/datasets/{DATASET_ID}/files/participants.json"

# Fallback to the standard OpenNeuro BIDS metadata endpoint for the dataset description
# which often contains the schema or we fetch the participants.tsv directly to parse
DATASET_DESC_URL = f"https://api.openneuro.org/datasets/{DATASET_ID}/files/dataset_description.json"

# The most reliable way to get the schema for participants in OpenNeuro is often
# to fetch the participants.json (if available via API) or parse the TSV header.
# However, the task specifically asks to verify the *field* exists.
# OpenNeuro API v2/v3: https://api.openneuro.org/datasets/{id}/files?files.filename=participants.tsv
# Let's fetch the participants.tsv content to inspect headers.
PARTICIPANTS_TSV_RAW = f"https://openneuro.org/datasets/{DATASET_ID}/versions/latest/file-display/participants.tsv"

# Alternative: Fetch the metadata JSON if the dataset provides a schema file
# But standard BIDS datasets usually have participants.tsv.

REQUIRED_FIELD = "dream_recall_frequency"
OUTPUT_DIR = Path("data/raw")
METADATA_FILE = OUTPUT_DIR / "validated_metadata.json"


def fetch_participants_tsv(dataset_id: str) -> str:
    """
    Fetches the raw content of participants.tsv from OpenNeuro.
    Raises an exception if the file is not found or network fails.
    """
    url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/file-display/participants.tsv"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch participants.tsv from OpenNeuro: {e}")


def validate_metadata_field(tsv_content: str, field_name: str) -> bool:
    """
    Checks if the specified field exists in the header of the TSV content.
    """
    if not tsv_content:
        return False
    
    lines = tsv_content.strip().split('\n')
    if not lines:
        return False
    
    header_line = lines[0]
    headers = header_line.split('\t')
    
    # Clean headers (remove BIDS prefix if present, though standard is just column name)
    # BIDS participants.tsv usually has 'participant_id' and then other columns.
    # We look for the exact string match in the header.
    return field_name in headers


def save_validated_metadata(field_found: bool, headers: list):
    """
    Saves the validation result to a JSON file in data/raw/
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "dataset_id": DATASET_ID,
        "required_field": REQUIRED_FIELD,
        "field_found": field_found,
        "available_headers": headers,
        "status": "PASSED" if field_found else "FAILED",
        "message": f"Field '{REQUIRED_FIELD}' {'found' if field_found else 'NOT FOUND'} in metadata."
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    return data


def main():
    """
    Main execution gate for Phase 0.
    """
    print(f"--- Phase 0 Gate: Validating Metadata for {DATASET_ID} ---")
    print(f"Target Field: {REQUIRED_FIELD}")
    
    # 1. Fetch Metadata
    try:
        print(f"Fetching participants.tsv from OpenNeuro...")
        tsv_content = fetch_participants_tsv(DATASET_ID)
    except RuntimeError as e:
        print(f"CRITICAL ERROR: {e}")
        # Fail loudly as per constraints
        sys.exit(1)
    
    # 2. Parse Headers
    headers = []
    if tsv_content:
        lines = tsv_content.strip().split('\n')
        if lines:
            headers = lines[0].split('\t')
    
    print(f"Available columns in metadata: {headers}")
    
    # 3. Validate
    field_found = validate_metadata_field(tsv_content, REQUIRED_FIELD)
    
    # 4. Save Result
    result = save_validated_metadata(field_found, headers)
    
    # 5. Gate Logic
    if not field_found:
        print(f"\n!!! GATE FAILED !!!")
        print(f"The required field '{REQUIRED_FIELD}' is missing from the dataset metadata.")
        print(f"Execution HALTED as per FR-001 and Plan Phase 0.")
        print(f"Result saved to: {METADATA_FILE}")
        sys.exit(1)
    
    print(f"\n--- GATE PASSED ---")
    print(f"Field '{REQUIRED_FIELD}' verified. Proceeding to next stage.")
    print(f"Result saved to: {METADATA_FILE}")
    
    # Optional: Print config summary to verify environment
    config = get_config_summary()
    print(f"Config Check: {config}")


if __name__ == "__main__":
    main()