"""
Validates entries in data/dataset_registry.yaml and produces validation_log.txt in JSON-lines format.

This script performs the following checks for each dataset in the registry:
1. Verifies the file exists at the specified path.
2. Validates the SHA256 checksum matches the registered value.
3. Checks that required metadata fields (name, description, source_type, source_id, file_path) are present.
4. Validates that the 'verified' flag is a boolean.

Output:
- Writes a JSON-lines log to data/validation_log.txt with one entry per dataset.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Import existing functions from sibling module
from data.dataset_registry import compute_sha256, verify_checksum

REGISTRY_PATH = Path("data/dataset_registry.yaml")
OUTPUT_PATH = Path("data/validation_log.txt")


def validate_dataset_entry(entry: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    """
    Validate a single dataset entry from the registry.

    Returns a log entry dict with validation results.
    """
    log_entry = {
        "name": entry.get("name", "UNKNOWN"),
        "status": "valid",
        "checks": {},
        "errors": []
    }

    # Check 1: Required fields present
    required_fields = ["name", "description", "source_type", "source_id", "file_path"]
    missing_fields = [f for f in required_fields if not entry.get(f)]
    if missing_fields:
        log_entry["status"] = "invalid"
        log_entry["errors"].append(f"Missing required fields: {missing_fields}")
        log_entry["checks"]["required_fields"] = False
    else:
        log_entry["checks"]["required_fields"] = True

    # Check 2: File existence
    file_path = entry.get("file_path")
    if file_path:
        full_path = base_dir / file_path
        if full_path.exists():
            log_entry["checks"]["file_exists"] = True
            log_entry["checks"]["file_path"] = str(full_path)
        else:
            log_entry["checks"]["file_exists"] = False
            log_entry["status"] = "invalid"
            log_entry["errors"].append(f"File not found: {full_path}")
    else:
        log_entry["checks"]["file_exists"] = False
        log_entry["status"] = "invalid"
        log_entry["errors"].append("No file_path specified")

    # Check 3: Checksum validation (only if file exists)
    if log_entry["checks"].get("file_exists"):
        registered_checksum = entry.get("checksum")
        if registered_checksum:
            try:
                # Compute actual checksum
                actual_checksum = compute_sha256(base_dir / file_path)
                
                # Validate using the imported function
                is_valid = verify_checksum(actual_checksum, registered_checksum)
                
                log_entry["checks"]["checksum_valid"] = is_valid
                log_entry["checks"]["registered_checksum"] = registered_checksum
                log_entry["checks"]["actual_checksum"] = actual_checksum
                
                if not is_valid:
                    log_entry["status"] = "invalid"
                    log_entry["errors"].append(f"Checksum mismatch: expected {registered_checksum}, got {actual_checksum}")
            except Exception as e:
                log_entry["checks"]["checksum_valid"] = False
                log_entry["status"] = "invalid"
                log_entry["errors"].append(f"Checksum computation failed: {str(e)}")
        else:
            log_entry["checks"]["checksum_valid"] = None
            log_entry["errors"].append("No checksum registered for validation")
    else:
        log_entry["checks"]["checksum_valid"] = None

    # Check 4: Verified flag type
    verified = entry.get("verified")
    if verified is not None and not isinstance(verified, bool):
        log_entry["checks"]["verified_type"] = False
        log_entry["status"] = "invalid"
        log_entry["errors"].append(f"Invalid 'verified' type: {type(verified).__name__}, expected bool")
    else:
        log_entry["checks"]["verified_type"] = True

    return log_entry


def validate_registry(registry_path: Path, output_path: Path) -> List[Dict[str, Any]]:
    """
    Validate all entries in the dataset registry.

    Args:
        registry_path: Path to the dataset_registry.yaml file
        output_path: Path where the validation_log.txt will be written

    Returns:
        List of validation log entries
    """
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")

    # Load registry
    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)

    datasets = registry.get("datasets", [])
    if not datasets:
        raise ValueError("No datasets found in registry")

    base_dir = registry_path.parent.parent  # Go up from data/ to project root
    
    log_entries = []
    
    for entry in datasets:
        log_entry = validate_dataset_entry(entry, base_dir)
        log_entries.append(log_entry)

    # Write output in JSON-lines format
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for entry in log_entries:
            f.write(json.dumps(entry) + '\n')

    return log_entries


def main():
    """Main entry point for registry validation."""
    print(f"Validating dataset registry: {REGISTRY_PATH}")
    
    try:
        log_entries = validate_registry(REGISTRY_PATH, OUTPUT_PATH)
        
        valid_count = sum(1 for e in log_entries if e["status"] == "valid")
        invalid_count = len(log_entries) - valid_count
        
        print(f"Validation complete:")
        print(f"  Total datasets: {len(log_entries)}")
        print(f"  Valid: {valid_count}")
        print(f"  Invalid: {invalid_count}")
        print(f"  Log written to: {OUTPUT_PATH}")
        
        if invalid_count > 0:
            print("\nInvalid datasets:")
            for entry in log_entries:
                if entry["status"] != "valid":
                    print(f"  - {entry['name']}: {', '.join(entry['errors'])}")
            
    except Exception as e:
        print(f"Validation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()