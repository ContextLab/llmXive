"""Unit tests for the synthetic query generation (T004)."""

import json
from pathlib import Path
import yaml
from jsonschema import Draft7Validator
from llmxive_toolkit import paths

def test_schema_file_exists():
    """The query instance schema must be present."""
    # Using the path identified in the project's current state
    schema_path = Path("specs/001-llmxive-follow-up-extending-omniretrieva/contracts/query_instance.schema.yaml")
    assert schema_path.is_file(), f"Schema file missing: {schema_path}"

def test_generation_log_exists_and_valid():
    """generation_log.json must exist, contain >=500 records, >=100 high-complexity graph queries, and validate against the schema."""
    genlog_path = paths.data("processed", "generation_log.json")
    assert genlog_path.is_file(), f"generation_log.json not found at {genlog_path}"

    with genlog_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Record count
    assert len(data) >= 500, f"Expected at least 500 queries, found {len(data)}"

    # High-complexity graph queries (depth >= 3)
    high_complex_graph = [
        q for q in data
        if q.get("source_type") == "graph" and q.get("complexity_level", 0) >= 3
    ]
    assert len(high_complex_graph) >= 100, (
        f"Expected at least 100 high-complexity graph queries, found {len(high_complex_graph)}"
    )

    # Load and validate schema
    schema_path = Path("specs/001-llmxive-follow-up-extending-omniretrieva/contracts/query_instance.schema.yaml")
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)

    for idx, instance in enumerate(data):
        # Check that ground_truth_plan is explicitly null (None in Python)
        assert instance.get("ground_truth_plan") is None, f"Record {idx} ground_truth_plan must be null"
        
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
        assert not errors, f"Schema validation errors in record {idx}: {errors}"