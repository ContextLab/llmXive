"""
Unit tests for the Verified Source Enforcer module.
"""

import os
import json
import pytest
from pathlib import Path
import tempfile

from data.verified_source_enforcer import (
    ScientificValidityError,
    detect_data_source_type,
    verify_source_is_valid,
    enforce_verified_source,
    load_verified_sources
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def synthetic_csv(temp_dir):
    """Create a synthetic CSV file for testing."""
    csv_path = temp_dir / "data" / "synthetic" / "synthetic_data.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("id,value\n1,2\n3,4")
    return csv_path

@pytest.fixture
def external_csv(temp_dir):
    """Create an external CSV file for testing."""
    csv_path = temp_dir / "data" / "external" / "external_data.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("id,value\n1,2\n3,4")
    return csv_path

@pytest.fixture
def unknown_csv(temp_dir):
    """Create a CSV file with an unknown path for testing."""
    csv_path = temp_dir / "data" / "processed" / "processed_data.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("id,value\n1,2\n3,4")
    return csv_path

@pytest.fixture
def verified_sources_file(temp_dir):
    """Create a verified_sources.json file for testing."""
    json_path = temp_dir / "state" / "verified_sources.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps({
        "sources": [
          str(temp_dir / "data" / "external" / "external_data.csv")
        ]
    }))
    return json_path

def test_detect_data_source_type_synthetic(synthetic_csv):
    """Test that synthetic data is correctly identified."""
    assert detect_data_source_type(synthetic_csv) == 'synthetic'

def test_detect_data_source_type_real(external_csv):
    """Test that external data is correctly identified as real."""
    assert detect_data_source_type(external_csv) == 'real'

def test_detect_data_source_type_unknown(unknown_csv):
    """Test that unknown data path returns 'unknown'."""
    assert detect_data_source_type(unknown_csv) == 'unknown'

def test_verify_source_scientific_validation_synthetic(synthetic_csv):
    """Test that synthetic data raises an error in Scientific Validation mode."""
    with pytest.raises(ScientificValidityError) as exc_info:
        verify_source_is_valid(synthetic_csv, phase='phase3')
    assert "SCIENTIFIC VALIDITY ERROR" in str(exc_info.value)

def test_verify_source_scientific_validation_real(external_csv, verified_sources_file):
    """Test that real data in external dir is valid in Scientific Validation mode."""
    result = verify_source_is_valid(
        external_csv,
        phase='phase3',
        verified_sources_path=verified_sources_file
    )
    assert result["is_valid"] is True
    assert result["verified"] is True

def test_verify_source_scientific_validation_unknown(unknown_csv, verified_sources_file):
    """Test that unknown data path is handled correctly in Scientific Validation mode."""
    # This should not raise an error but log a warning
    result = verify_source_is_valid(
        unknown_csv,
        phase='phase3',
        verified_sources_path=verified_sources_file
    )
    # It should not be verified since it's not in the whitelist
    assert result["is_valid"] is True  # We allow it but warn
    assert result["verified"] is False

def test_verify_source_synthetic_mode_synthetic(synthetic_csv):
    """Test that synthetic data is allowed in synthetic mode."""
    result = verify_source_is_valid(synthetic_csv, phase='synthetic')
    assert result["is_valid"] is True
    assert "Synthetic data is acceptable" in result["message"]

def test_enforce_verified_source_scientific_validation_synthetic(synthetic_csv):
    """Test that enforce_verified_source raises an error for synthetic data in phase3."""
    with pytest.raises(ScientificValidityError):
        enforce_verified_source(synthetic_csv, phase='phase3')

def test_enforce_verified_source_scientific_validation_real(external_csv, verified_sources_file):
    """Test that enforce_verified_source does not raise for real data in phase3."""
    # This should not raise
    enforce_verified_source(
        external_csv,
        phase='phase3',
        verified_sources_path=verified_sources_file
    )

def test_load_verified_sources(verified_sources_file):
    """Test loading verified sources from JSON file."""
    sources = load_verified_sources(verified_sources_file)
    assert len(sources) == 1
    assert "external_data.csv" in sources[0]

def test_load_verified_sources_missing_file(temp_dir):
    """Test loading verified sources from a missing file."""
    missing_path = temp_dir / "nonexistent" / "verified_sources.json"
    sources = load_verified_sources(missing_path)
    assert sources == []