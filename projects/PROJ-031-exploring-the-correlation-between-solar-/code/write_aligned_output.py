"""
Task T017: Write aligned_events.csv and update source_manifest.yaml with checksums.

This script performs the final output stage for User Story 1:
1. Validates the aligned events using code/validate.py (blocks if invalid).
2. Writes the validated data to data/processed/aligned_events.csv.
3. Computes the SHA-256 checksum of the output file.
4. Updates data/source_manifest.yaml with the new file path, checksum, record count, and status.
"""
import os
import sys
import csv
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.validate import load_schema, validate_aligned_events, block_write_if_invalid
from code.versioning import compute_sha256, update_artifact_state
from code.ingest import load_manifest, save_manifest, update_manifest_entry
from code.align import align_events

ALIGNED_EVENTS_PATH = project_root / "data" / "processed" / "aligned_events.csv"
MANIFEST_PATH = project_root / "data" / "source_manifest.yaml"
SCHEMA_PATH = project_root / "contracts" / "aligned_event.schema.yaml"

def ensure_directories():
    """Ensure output directories exist."""
    ALIGNED_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)

def write_aligned_events(df_data: List[Dict[str, Any]], output_path: Path):
    """
    Write the aligned events list to a CSV file.
    
    Args:
        df_data: List of dictionaries representing rows.
        output_path: Path to the output CSV file.
    """
    if not df_data:
        print("Warning: No data to write to aligned_events.csv")
        return

    fieldnames = list(df_data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(df_data)

def update_manifest_with_checksum(manifest_path: Path, output_path: Path, record_count: int):
    """
    Update the source_manifest.yaml with the new file's checksum and metadata.
    
    Args:
        manifest_path: Path to the source_manifest.yaml.
        output_path: Path to the generated aligned_events.csv.
        record_count: Number of records in the file.
    """
    manifest = load_manifest(str(manifest_path))
    
    if "processed_outputs" not in manifest or "aligned_events" not in manifest["processed_outputs"]:
        raise ValueError("aligned_events entry not found in processed_outputs of manifest.")
    
    checksum = compute_sha256(str(output_path))
    
    # Update the manifest entry
    update_manifest_entry(
        manifest, 
        "processed_outputs", 
        "aligned_events", 
        {
            "status": "Verified",
            "last_generated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checksum_sha256": checksum,
            "record_count": record_count,
            "file_path": str(output_path.relative_to(project_root))
        }
    )
    
    save_manifest(str(manifest_path), manifest)
    print(f"Updated manifest: {manifest_path}")
    print(f"  Status: Verified")
    print(f"  Checksum: {checksum}")
    print(f"  Record Count: {record_count}")

def main():
    """Main entry point for T017."""
    print(f"Starting T017: Writing {ALIGNED_EVENTS_PATH}...")
    
    ensure_directories()
    
    # 1. Generate/Load Data
    # We assume the previous steps (T014-T016) prepared the data.
    # If the final file does not exist, we run the alignment logic to produce it.
    # This ensures T017 is self-contained for the final write step.
    temp_path = project_root / "data" / "processed" / "aligned_events_temp.csv"
    
    if not ALIGNED_EVENTS_PATH.exists():
        print("Aligned events file not found. Running alignment logic...")
        aligned_data = align_events()
        
        if aligned_data is None or len(aligned_data) == 0:
            print("Error: Alignment produced no data. Check raw data sources.")
            sys.exit(1)
        
        write_aligned_events(aligned_data, temp_path)
    else:
        print("Aligned events file exists. Using existing file for validation.")
        temp_path = ALIGNED_EVENTS_PATH

    # 2. Validate the data (T018 requirement)
    print("Validating data against schema...")
    is_valid, errors = validate_aligned_events(str(temp_path), str(SCHEMA_PATH))
    
    if not is_valid:
        print("Validation FAILED. Blocking write.")
        print(f"Errors: {errors}")
        if temp_path != ALIGNED_EVENTS_PATH and temp_path.exists():
            temp_path.unlink()
        sys.exit(1)
    
    print("Validation PASSED.")
    
    # 3. Write the final file
    if temp_path != ALIGNED_EVENTS_PATH:
        print(f"Moving validated file to {ALIGNED_EVENTS_PATH}")
        with open(temp_path, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            rows = list(reader)
        
        write_aligned_events(rows, ALIGNED_EVENTS_PATH)
        temp_path.unlink()
    else:
        print(f"Final file already at {ALIGNED_EVENTS_PATH}")
    
    # 4. Update Manifest
    record_count = 0
    with open(ALIGNED_EVENTS_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        record_count = sum(1 for _ in reader)
    
    update_manifest_with_checksum(MANIFEST_PATH, ALIGNED_EVENTS_PATH, record_count)
    
    print(f"T017 Complete. Wrote {ALIGNED_EVENTS_PATH} with {record_count} records.")

if __name__ == "__main__":
    main()