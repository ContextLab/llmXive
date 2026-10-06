"""
Annotation extractor for SWE-bench Lite.
Identifies ground truth fields and extracts annotations to CSV.
"""
import csv
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import config and data_loader from sibling modules
from config import get_path, ensure_directories
from data_loader import download_dataset


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_ground_truth_annotations():
    """
    Step 1: Schema Discovery - Inspect first 100 records to find ground truth field.
    Step 2: Extraction - Extract ground truth data to CSV.
    Step 3: Data Hygiene - Record derivation logic and checksums.
    """
    # Ensure directories exist
    ensure_directories()

    raw_data_path = get_path("data", "raw", "swe-bench-lite.jsonl")
    output_csv_path = get_path("data", "raw", "ground_truth_annotations.csv")
    schema_output_path = get_path("data", "raw", "schema_discovery.json")

    # Download dataset if not present
    if not raw_data_path.exists():
        print("Downloading SWE-bench Lite dataset...")
        download_dataset()

    # Load dataset
    from datasets import load_dataset

    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

    # Step 1: Schema Discovery
    print("Inspecting first 100 records for ground truth field...")
    possible_fields = ["ground_truth_files", "ground_truth", "hints", "solution"]
    detected_field = None
    sample_records = []

    for i, record in enumerate(dataset):
        if i >= 100:
            break
        sample_records.append(record)
        for field in possible_fields:
            if field in record and record[field] is not None:
                detected_field = field
                break
        if detected_field:
            break

    if not detected_field:
        # Fallback to checking any field containing 'ground'
        for record in sample_records:
            for key, value in record.items():
                if "ground" in key.lower() and value is not None:
                    detected_field = key
                    break
            if detected_field:
                break

    if not detected_field:
        raise ValueError(
            "Could not detect ground truth field in SWE-bench Lite dataset. "
            f"Checked fields: {possible_fields}. Available keys in first record: {list(sample_records[0].keys())}"
        )

    print(f"Detected ground truth field: {detected_field}")

    # Save schema discovery result
    schema_result = {
        "detected_field": detected_field,
        "checked_fields": possible_fields,
        "sample_size": len(sample_records),
    }
    with open(schema_output_path, "w") as f:
        json.dump(schema_result, f, indent=2)
    print(f"Schema discovery result saved to: {schema_output_path}")

    # Step 2: Extraction
    print(f"Extracting ground truth annotations from '{detected_field}'...")
    extracted_data = []

    for record in dataset:
        ground_truth_value = record.get(detected_field)

        if ground_truth_value is None:
            raise ValueError(
                f"Record {record.get('instance_id', 'unknown')} has null ground truth for field '{detected_field}'. "
                "Cannot proceed with silent fallback."
            )

        # Handle different types of ground truth values
        if isinstance(ground_truth_value, str):
            # Try to parse as JSON if it looks like a list
            try:
                if ground_truth_value.strip().startswith("["):
                  files_list = json.loads(ground_truth_value)
                else:
                  files_list = [ground_truth_value]
            except json.JSONDecodeError:
                files_list = [ground_truth_value]
        elif isinstance(ground_truth_value, list):
            files_list = ground_truth_value
        else:
            files_list = [str(ground_truth_value)]

        extracted_data.append({
            "repo_id": record.get("repo", ""),
            "issue_id": record.get("instance_id", ""),
            "ground_truth_file_paths": json.dumps(files_list)
        })

    # Write to CSV
    with open(output_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["repo_id", "issue_id", "ground_truth_file_paths"])
        writer.writeheader()
        writer.writerows(extracted_data)

    print(f"Extracted {len(extracted_data)} annotations to: {output_csv_path}")

    # Step 3: Data Hygiene - Record derivation logic and checksum
    checksum = compute_file_sha256(output_csv_path)
    print(f"SHA256 checksum of {output_csv_path}: {checksum}")

    # Update state file with derivation info
    state_path = get_path("state", "projects", "PROJ-905-llmxive-follow-up-extending-fastcontext.yaml")
    if state_path.exists():
        import yaml
        with open(state_path, "r") as f:
            state_data = yaml.safe_load(f) or {}

        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}

        state_data["artifact_hashes"]["ground_truth_annotations.csv"] = checksum
        state_data["artifact_hashes"]["annotation_extractor.py"] = compute_file_sha256(Path(__file__))

        with open(state_path, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False)

        print(f"Updated state file: {state_path}")
    else:
        print(f"Warning: State file not found at {state_path}. Skipping update.")

    return {
        "detected_field": detected_field,
        "total_records": len(extracted_data),
        "output_file": str(output_csv_path),
        "checksum": checksum
    }


def main():
    """Main entry point."""
    try:
        result = extract_ground_truth_annotations()
        print("\nExtraction Summary:")
        print(f"  Detected Field: {result['detected_field']}")
        print(f"  Total Records: {result['total_records']}")
        print(f"  Output File: {result['output_file']}")
        print(f"  Checksum: {result['checksum']}")
    except Exception as e:
        print(f"Error during extraction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
