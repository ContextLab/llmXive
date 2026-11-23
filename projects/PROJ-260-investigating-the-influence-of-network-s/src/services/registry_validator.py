import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from llmxive_toolkit import paths, get_logger

# Initialize logger using the toolkit
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Registry handling
# ----------------------------------------------------------------------
def load_registry(registry_path: Path) -> Dict[str, Any]:
    """Load the dataset registry JSON."""
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def validate_dataset_id(dataset_id: str) -> bool:
    """
    Validate a dataset ID by checking its reachability.
    Supports Zenodo numeric IDs and HuggingFace dataset identifiers.
    """
    # Heuristic: numeric IDs are Zenodo, otherwise assume HuggingFace
    is_zenodo = dataset_id.isdigit() or "zenodo" in dataset_id.lower()

    if is_zenodo:
        return validate_zenodo_id(dataset_id)
    else:
        return validate_hf_id(dataset_id)

def validate_zenodo_id(dataset_id: str) -> bool:
    """Validate a Zenodo dataset ID via the public Zenodo API."""
    url = f"https://zenodo.org/api/records/{dataset_id}"
    try:
        log.debug(f"Checking Zenodo ID {dataset_id} at {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data:
                log.info(f"Zenodo ID {dataset_id} is valid.")
                return True
            log.warning(f"Zenodo ID {dataset_id} returned 200 but lacks metadata.")
        else:
            log.warning(f"Zenodo ID {dataset_id} returned status {response.status_code}")
        return False
    except requests.RequestException as e:
        log.error(f"Network error checking Zenodo ID {dataset_id}: {e}")
        return False

def validate_hf_id(dataset_id: str) -> bool:
    """
    Validate a HuggingFace dataset ID using the HF Hub API.
    Handles shorthand IDs by attempting a known project prefix.
    """
    # List of potential prefixes for this project's datasets
    prefixes = ["THZERAOFC/"]
    
    # Try the ID as provided
    if _check_hf_api(dataset_id):
        log.info(f"HuggingFace dataset {dataset_id} is valid.")
        return True
    
    # If it's a short name (no slash), try the project prefixes
    if "/" not in dataset_id:
        for prefix in prefixes:
            full_id = f"{prefix}{dataset_id}"
            if _check_hf_api(full_id):
                log.info(f"HuggingFace dataset {dataset_id} is valid (resolved to {full_id}).")
                return True
    
    log.warning(f"HuggingFace dataset {dataset_id} could not be validated.")
    return False

def _check_hf_api(dataset_id: str) -> bool:
    """Helper to check HF Hub API for dataset existence."""
    url = f"https://huggingface.co/api/datasets/{dataset_id}"
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def validate_registry(registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all dataset IDs in the supplied registry.
    Returns a dict with lists of valid and invalid IDs and an overall status flag.
    """
    valid_ids: List[str] = []
    invalid_ids: List[str] = []

    for size, entries in registry.items():
        log.info(f"Validating entries for system size {size}")

        # Normalise the entry format to a flat list of IDs
        if isinstance(entries, list):
            ids_to_check = entries
        elif isinstance(entries, dict):
            if "ids" in entries:
                ids_to_check = entries["ids"]
            elif "id" in entries:
                ids_to_check = [entries["id"]]
            else:
                ids_to_check = [v for v in entries.values() if isinstance(v, str)]
        else:
            log.warning(f"Unexpected registry format for size {size}: {type(entries)}")
            continue

        for dataset_id in ids_to_check:
            if not isinstance(dataset_id, str):
                continue

            if validate_dataset_id(dataset_id):
                valid_ids.append(dataset_id)
            else:
                invalid_ids.append(dataset_id)

    return {
        "valid_ids": valid_ids,
        "invalid_ids": invalid_ids,
        "all_valid": len(invalid_ids) == 0,
    }

# ----------------------------------------------------------------------
# Output writers
# ----------------------------------------------------------------------
def write_validation_log(log_path: Path, results: Dict[str, Any], registry_path: Path):
    """Write a human‑readable validation log."""
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Registry Validation Log\n")
        f.write("=======================\n")
        f.write(f"Registry file: {registry_path}\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write(f"Valid IDs ({len(results['valid_ids'])}):\n")
        for vid in results["valid_ids"]:
            f.write(f"  - {vid}\n")

        f.write(f"\nInvalid IDs ({len(results['invalid_ids'])}):\n")
        for iid in results["invalid_ids"]:
            f.write(f"  - {iid}\n")

        overall = "PASS" if results["all_valid"] else "FAIL"
        f.write(f"\nOverall Status: {overall}\n")

        if results["all_valid"]:
            f.write("\nVALIDATION SUCCESS\n")
        else:
            f.write("\nVALIDATION FAILED\n")

def write_valid_sources(valid_ids: List[str], output_path: Path):
    """Write the list of validated source IDs to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid_ids, f, indent=2)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Execute the registry validation workflow."""
    registry_path = paths.data("metadata", "dataset_registry.json")
    log_path = paths.data("metadata", "registry_validation.log")
    valid_sources_path = paths.data("metadata", "valid_sources.json")

    log.info("Starting registry validation...")

    try:
        # Load the registry JSON
        log.info(f"Loading registry from {registry_path}")
        registry = load_registry(registry_path)

        # Perform validation
        log.info("Validating dataset IDs...")
        results = validate_registry(registry)

        # Persist outputs
        write_validation_log(log_path, results, registry_path)
        write_valid_sources(results["valid_ids"], valid_sources_path)

        if results["all_valid"]:
            log.info("All dataset IDs are valid.")
            log.info("VALIDATION SUCCESS")
            return 0
        else:
            log.error(f"Validation failed. {len(results['invalid_ids'])} invalid IDs found.")
            log.error("HALTING: Please fix the registry or update VERIFIED_DATASET_IDS in config.")
            return 1

    except FileNotFoundError as e:
        log.error(f"FATAL: {e}")
        return 1
    except Exception as e:
        log.error(f"FATAL: Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
