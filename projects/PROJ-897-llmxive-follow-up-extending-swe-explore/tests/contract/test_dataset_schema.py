"""
Contract test for the dataset schema (T009).

This test verifies that the dataset artifacts in data/curated/ conform
to the schema defined in contracts/dataset_schema.yaml (created in T006).

It uses the validation utilities from code/utils/validation.py to perform
the checks.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path to allow importing code modules
# assuming this test is run from the project root or via pytest with the correct config.
# The project root is the parent of 'code' and 'tests'.
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.validation import load_schema, validate_jsonl_against_schema
from config import get_config_summary


def test_dataset_schema_contract():
    """
    Contract test: Validate curated dataset files against the schema.

    Checks:
    1. The schema file exists and loads correctly.
    2. The expected dataset files (hard_subset.jsonl, synthetic_issues.jsonl)
       exist in data/curated/.
    3. Each file validates against the schema.
    """
    # 1. Load the schema
    schema_path = PROJECT_ROOT / "contracts" / "dataset_schema.yaml"
    assert schema_path.exists(), f"Schema file not found: {schema_path}"

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        raise AssertionError(f"Failed to load schema from {schema_path}: {e}")

    # 2. Define expected curated files based on T014 tasks
    # Note: If these files don't exist yet (e.g., T014 not run), the test should fail
    # to indicate the pipeline is incomplete, or we can skip if they are optional for this specific contract check.
    # However, a contract test usually implies the artifacts should exist to be validated.
    # We will check existence and validate if present.
    curated_dir = PROJECT_ROOT / "data" / "curated"
    expected_files = ["hard_subset.jsonl", "synthetic_issues.jsonl"]

    missing_files = []
    for filename in expected_files:
        filepath = curated_dir / filename
        if not filepath.exists():
            missing_files.append(filename)

    if missing_files:
        # If files are missing, it means the data curation tasks (T014) haven't run yet.
        # For a strict contract test, this is a failure state if we expect the data to be there.
        # We raise an assertion to highlight the missing artifacts.
        raise AssertionError(
            f"Missing expected dataset artifacts for schema validation: {missing_files}. "
            "Ensure T014 (curate.py) has been executed successfully."
        )

    # 3. Validate each file
    for filename in expected_files:
        filepath = curated_dir / filename
        try:
            is_valid, errors = validate_jsonl_against_schema(filepath, schema)
            assert is_valid, (
                f"Validation failed for {filename}:\n"
                + "\n".join([str(e) for e in errors])
            )
        except Exception as e:
            raise AssertionError(
                f"Error during validation of {filename}: {e}"
            )

    # If we reach here, all files exist and validate correctly.
    assert True, "All dataset contracts passed."


if __name__ == "__main__":
    test_dataset_schema_contract()
    print("Contract test for dataset schema passed.")