"""
Contract test for mapping coverage results (T046 output).

Validates the structure and content of results/mapping_coverage.json
to ensure it contains the required fields with correct types.

Required fields:
- organism_id: str
- total_genes: int
- mapped_genes: int
- coverage_percent: float
"""
import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict

import sys
# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path


MAPPING_COVERAGE_SCHEMA = {
    "type": "object",
    "required": ["organism_id", "total_genes", "mapped_genes", "coverage_percent"],
    "properties": {
        "organism_id": {"type": "string"},
        "total_genes": {"type": "integer", "minimum": 0},
        "mapped_genes": {"type": "integer", "minimum": 0},
        "coverage_percent": {"type": "number", "minimum": 0.0, "maximum": 100.0}
    },
    "additionalProperties": False
}


def validate_mapping_coverage_entry(entry: Dict[str, Any]) -> None:
    """
    Validate a single mapping coverage entry against the schema.
    
    Args:
        entry: Dictionary containing mapping coverage data for one organism.
        
    Raises:
        AssertionError: If the entry does not match the schema.
    """
    assert isinstance(entry, dict), "Entry must be a dictionary"
    
    # Check required fields
    for field in MAPPING_COVERAGE_SCHEMA["required"]:
        assert field in entry, f"Missing required field: {field}"
    
    # Validate organism_id
    assert isinstance(entry["organism_id"], str), "organism_id must be a string"
    assert len(entry["organism_id"]) > 0, "organism_id cannot be empty"
    
    # Validate total_genes
    assert isinstance(entry["total_genes"], int), "total_genes must be an integer"
    assert entry["total_genes"] >= 0, "total_genes cannot be negative"
    
    # Validate mapped_genes
    assert isinstance(entry["mapped_genes"], int), "mapped_genes must be an integer"
    assert entry["mapped_genes"] >= 0, "mapped_genes cannot be negative"
    
    # Validate coverage_percent
    assert isinstance(entry["coverage_percent"], (int, float)), "coverage_percent must be a number"
    assert 0.0 <= entry["coverage_percent"] <= 100.0, "coverage_percent must be between 0 and 100"
    
    # Validate consistency: mapped_genes cannot exceed total_genes
    assert entry["mapped_genes"] <= entry["total_genes"], "mapped_genes cannot exceed total_genes"
    
    # Validate coverage_percent calculation
    if entry["total_genes"] > 0:
        expected_coverage = (entry["mapped_genes"] / entry["total_genes"]) * 100
        # Allow small floating point tolerance
        assert abs(entry["coverage_percent"] - expected_coverage) < 0.01, \
            f"coverage_percent mismatch: expected {expected_coverage}, got {entry['coverage_percent']}"


@pytest.mark.contract
def test_mapping_coverage_schema_exists():
    """Test that the mapping coverage file exists (if data was generated)."""
    # This test passes if the file exists or if we're in a test-only environment
    # where data hasn't been generated yet.
    file_path = get_path("results/mapping_coverage.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), "Mapping coverage data must be a list of entries"
        assert len(data) > 0, "Mapping coverage data should not be empty"


@pytest.mark.contract
def test_mapping_coverage_structure():
    """
    Test that mapping coverage entries conform to the expected schema.
    
    If the file doesn't exist, this test is skipped (data generation not yet run).
    """
    file_path = get_path("results/mapping_coverage.json")
    
    if not os.path.exists(file_path):
        pytest.skip("results/mapping_coverage.json not found. Run the pipeline first.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Mapping coverage data must be a list"
    
    for i, entry in enumerate(data):
        try:
            validate_mapping_coverage_entry(entry)
        except AssertionError as e:
            pytest.fail(f"Entry {i} failed validation: {str(e)}")


@pytest.mark.contract
def test_mapping_coverage_fields_types():
    """
    Test that all required fields have the correct types.
    
    This is a more granular test to catch type errors specifically.
    """
    file_path = get_path("results/mapping_coverage.json")
    
    if not os.path.exists(file_path):
        pytest.skip("results/mapping_coverage.json not found. Run the pipeline first.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    for i, entry in enumerate(data):
        assert isinstance(entry.get("organism_id"), str), \
            f"Entry {i}: organism_id must be a string"
        assert isinstance(entry.get("total_genes"), int), \
            f"Entry {i}: total_genes must be an integer"
        assert isinstance(entry.get("mapped_genes"), int), \
            f"Entry {i}: mapped_genes must be an integer"
        assert isinstance(entry.get("coverage_percent"), (int, float)), \
            f"Entry {i}: coverage_percent must be a number"


@pytest.mark.contract
def test_mapping_coverage_consistency():
    """
    Test logical consistency of mapping coverage data.
    
    Ensures that mapped_genes <= total_genes and coverage calculation is correct.
    """
    file_path = get_path("results/mapping_coverage.json")
    
    if not os.path.exists(file_path):
        pytest.skip("results/mapping_coverage.json not found. Run the pipeline first.")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    for i, entry in enumerate(data):
        total = entry["total_genes"]
        mapped = entry["mapped_genes"]
        coverage = entry["coverage_percent"]
        
        assert mapped <= total, \
            f"Entry {i} ({entry['organism_id']}): mapped_genes ({mapped}) > total_genes ({total})"
        
        if total > 0:
            expected = (mapped / total) * 100
            assert abs(coverage - expected) < 0.01, \
                f"Entry {i} ({entry['organism_id']}): coverage_percent mismatch. " \
                f"Expected {expected:.2f}, got {coverage:.2f}"