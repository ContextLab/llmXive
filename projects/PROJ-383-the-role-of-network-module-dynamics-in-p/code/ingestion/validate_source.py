"""
Dataset ingestion validator for OpenNeuro ds001734.

This module verifies the availability and integrity of the HCP 1200 Subjects
dataset (OpenNeuro ds001734) before ingestion proceeds. It checks:
1. That the expected dataset identifier is 'ds001734'.
2. That the dataset is accessible via the OpenNeuro API.
3. That critical directories (e.g., 'sub-*/func') exist in the remote structure.

If validation fails, the script exits with a non-zero code and a clear error
message, preventing downstream processing of invalid or mismatched data.
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# Expected dataset ID as per plan.md (contradiction with spec.md ds000224 noted)
EXPECTED_DATASET_ID = "ds001734"
EXPECTED_DATASET_VERSION = "1.0.0"
OPENNEURO_API_BASE = "https://api.openneuro.org/datasets"

def check_dataset_availability(dataset_id: str) -> bool:
    """
    Check if a dataset exists on OpenNeuro via their public API.

    Args:
        dataset_id: The OpenNeuro dataset identifier (e.g., 'ds001734').

    Returns:
        True if the dataset exists and is accessible, False otherwise.
    """
    url = f"{OPENNEURO_API_BASE}/{dataset_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "llmXive-Research-Validator/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        # Other errors (e.g., 500) might be transient, but we treat them as failure for validation
        return False
    except Exception:
        return False
    return False

def verify_dataset_structure(dataset_id: str) -> bool:
    """
    Verify that the dataset has the expected directory structure.
    Specifically checks for the presence of subject folders (sub-*) and func directory.

    Args:
        dataset_id: The OpenNeuro dataset identifier.

    Returns:
        True if structure looks valid, False otherwise.
    """
    # OpenNeuro dataset tree API: https://api.openneuro.org/datasets/{id}/tree
    # We check for a specific subject pattern to ensure it's not an empty dataset
    tree_url = f"{OPENNEURO_API_BASE}/{dataset_id}/tree"
    try:
        req = urllib.request.Request(tree_url, headers={"User-Agent": "llmXive-Research-Validator/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                # Look for 'sub-' directories in the root
                # The API returns a list of nodes. We check if any start with 'sub-'
                if 'nodes' in data:
                    sub_dirs = [n for n in data['nodes'] if n.get('name', '').startswith('sub-')]
                    if len(sub_dirs) > 0:
                        # Further check if any of these have a 'func' child
                        # For ds001734, structure is usually: sub-*/func/sub-*_task-*_bold.nii.gz
                        for sub_node in sub_dirs[:5]: # Check first 5 subjects
                            sub_tree_url = f"{OPENNEURO_API_BASE}/{dataset_id}/tree?prefix={sub_node['name']}"
                            try:
                                sub_req = urllib.request.Request(sub_tree_url, headers={"User-Agent": "llmXive-Research-Validator/1.0"})
                                with urllib.request.urlopen(sub_req, timeout=15) as sub_resp:
                                    sub_data = json.loads(sub_resp.read().decode('utf-8'))
                                    if 'nodes' in sub_data:
                                        func_dirs = [n for n in sub_data['nodes'] if n.get('name') == 'func']
                                        if func_dirs:
                                            return True
                            except Exception:
                                continue
                return False
    except Exception:
        return False
    return False

def validate_source(dataset_id: str = EXPECTED_DATASET_ID) -> bool:
    """
    Main validation routine.

    Args:
        dataset_id: The dataset ID to validate. Defaults to ds001734.

    Returns:
        True if validation passes, False otherwise.
    """
    print(f"Validating OpenNeuro dataset: {dataset_id}...")

    # Check 1: Is the requested ID the expected one?
    if dataset_id != EXPECTED_DATASET_ID:
        print(f"ERROR: Dataset ID mismatch. Expected '{EXPECTED_DATASET_ID}', got '{dataset_id}'.")
        print("This project is configured to use ds001734 (HCP 1200).")
        return False

    # Check 2: Is the dataset available?
    if not check_dataset_availability(dataset_id):
        print(f"ERROR: Dataset '{dataset_id}' is not available on OpenNeuro.")
        print("Please check your internet connection or the dataset ID.")
        return False

    # Check 3: Does the structure look correct?
    if not verify_dataset_structure(dataset_id):
        print(f"ERROR: Dataset '{dataset_id}' does not have the expected structure (missing subject/func dirs).")
        return False

    print(f"SUCCESS: Dataset '{dataset_id}' is available and validated.")
    return True

def main():
    """Entry point for the validator script."""
    # Allow override via command line argument, but default to ds001734
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    else:
        target_id = EXPECTED_DATASET_ID

    success = validate_source(target_id)
    
    # ABORT ON MISMATCH: Exit with non-zero code if validation fails
    if not success:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()