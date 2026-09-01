"""
Contract test for T036: Enforce JSON schema compliance for LLM outputs.

This test validates that the file `data/processed/semantic_results.json`
adheres to the expected schema defined in the project specifications.
It ensures that every entry contains the required fields and that the
`llm_smell_labels` field is a valid list of strings.

Dependencies:
- pandas (for CSV loading if needed, though JSON is primary here)
- json (standard library)
"""

import json
import os
import pytest
from pathlib import Path

# Import project configuration paths to ensure consistency
from config import get_processed_path


REQUIRED_KEYS = {
    "function_id",
    "code",
    "loc",
    "cyclomatic_complexity",
    "nesting_depth",
    "static_smell_labels",
    "embedding_vector",
    "llm_smell_labels",
    "inference_time_ms",
    "status"
}

EXPECTED_STATUS_VALUES = {"success", "unparseable", "context_truncated", "error"}


def get_semantic_results_path():
    """Resolve the path to semantic_results.json."""
    processed_dir = get_processed_path()
    return os.path.join(processed_dir, "semantic_results.json")


@pytest.fixture
def semantic_results_data():
    """
    Load the semantic results JSON file.
    Raises FileNotFoundError if the file does not exist.
    """
    path = get_semantic_results_path()
    if not os.path.exists(path):
        pytest.fail(f"Data file not found: {path}. Run US2 pipeline first.")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {path}: {e}")
    
    if not isinstance(data, list):
        # Handle case where the root might be a dict with a 'results' key
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        pytest.fail(f"Expected a list of results in {path}, got {type(data)}")
    
    return data


def test_file_exists():
    """Verify the output file exists at the expected location."""
    path = get_semantic_results_path()
    assert os.path.exists(path), f"File {path} does not exist. US2 pipeline must run first."


def test_schema_compliance(semantic_results_data):
    """
    Validate that every record in the dataset conforms to the expected schema.
    Specifically checks:
    1. All required keys are present.
    2. `llm_smell_labels` is a list.
    3. `status` is a known valid value.
    """
    assert len(semantic_results_data) > 0, "The semantic results file is empty."

    failed_count = 0
    errors = []

    for idx, record in enumerate(semantic_results_data):
        if not isinstance(record, dict):
            errors.append(f"Record {idx} is not a dictionary: {type(record)}")
            failed_count += 1
            continue

        # Check required keys
        missing_keys = REQUIRED_KEYS - set(record.keys())
        if missing_keys:
            errors.append(f"Record {idx} missing keys: {missing_keys}")
            failed_count += 1
            continue

        # Validate specific field types
        if not isinstance(record.get("llm_smell_labels"), list):
            errors.append(f"Record {idx}: 'llm_smell_labels' is not a list (got {type(record.get('llm_smell_labels'))})")
            failed_count += 1

        if not isinstance(record.get("embedding_vector"), list):
            # Embedding vectors should be lists of floats
            errors.append(f"Record {idx}: 'embedding_vector' is not a list")
            failed_count += 1

        status = record.get("status")
        if status not in EXPECTED_STATUS_VALUES:
            errors.append(f"Record {idx}: Invalid status '{status}'. Expected one of {EXPECTED_STATUS_VALUES}")
            failed_count += 1

    if failed_count > 0:
        pytest.fail(f"Schema validation failed for {failed_count} records:\n" + "\n".join(errors[:10]))


def test_llm_labels_content(semantic_results_data):
    """
    Ensure that 'llm_smell_labels' contains only strings or is an empty list.
    """
    for idx, record in enumerate(semantic_results_data):
        labels = record.get("llm_smell_labels", [])
        if not isinstance(labels, list):
            continue # Caught in schema_compliance, but safe to skip here
        
        for label in labels:
            if not isinstance(label, str):
                pytest.fail(f"Record {idx}: 'llm_smell_labels' contains non-string value: {label} (type: {type(label)})")


def test_no_duplicate_function_ids(semantic_results_data):
    """
    Ensure that each function_id appears only once in the results.
    """
    ids = [record.get("function_id") for record in semantic_results_data if record.get("function_id")]
    if len(ids) != len(set(ids)):
        duplicates = [x for x in ids if ids.count(x) > 1]
        pytest.fail(f"Duplicate function_ids found: {set(duplicates)}")