"""
Unit tests for T012e: Real Ground Truth Fixture Generation.

These tests verify that the generated fixture:
1. Exists and is valid JSON.
2. Contains the required schema (log_id, text, label).
3. Contains both 'novel' and 'benign' labels.
4. Uses real UUIDs.
"""
import json
import os
import sys
import uuid
from pathlib import Path
import pytest

# Add code directory to path if running from tests
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_path

@pytest.fixture
def fixture_path():
    return get_path("project_root") / "data" / "test" / "real_ground_truth_fixture.json"

def test_fixture_exists(fixture_path):
    """Test that the ground truth fixture file exists."""
    assert fixture_path.exists(), f"Fixture file not found at {fixture_path}"

def test_fixture_is_valid_json(fixture_path):
    """Test that the fixture contains valid JSON."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            assert isinstance(data, list), "Fixture must be a JSON list"
        except json.JSONDecodeError as e:
            pytest.fail(f"Fixture is not valid JSON: {e}")

def test_fixture_schema(fixture_path):
    """Test that each record has the required keys: log_id, text, label."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) > 0, "Fixture must contain at least one record"

    for i, record in enumerate(data):
        assert "log_id" in record, f"Record {i} missing 'log_id'"
        assert "text" in record, f"Record {i} missing 'text'"
        assert "label" in record, f"Record {i} missing 'label'"
        assert isinstance(record["text"], str), f"Record {i} 'text' must be string"
        assert record["label"] in ["novel", "benign"], f"Record {i} label must be 'novel' or 'benign'"

def test_fixture_labels_present(fixture_path):
    """Test that both 'novel' and 'benign' labels are present."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    labels = [r["label"] for r in data]
    assert "novel" in labels, "Fixture must contain 'novel' (AdvBench) records"
    assert "benign" in labels, "Fixture must contain 'benign' (HF4) records"

def test_fixture_log_ids_are_uuids(fixture_path):
    """Test that all log_ids are valid UUIDs."""
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, record in enumerate(data):
        try:
            uuid.UUID(record["log_id"])
        except ValueError:
            pytest.fail(f"Record {i} has invalid UUID: {record['log_id']}")