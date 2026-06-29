"""
Unit tests for the hyperbolic volume validation module.
"""
import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock
import json

from code.analysis.validation import (
    ValidationEntry,
    ValidationResult,
    HyperbolicVolumeValidator,
    run_validation,
    load_cleaned_knots
)
from code.analysis.validation_reporting import (
    generate_validation_summary,
    write_validation_report_md,
    generate_full_report
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        "knot_id": ["3_1", "4_1", "5_1", "5_2"],
        "crossing_number": [3, 4, 5, 5],
        "hyperbolic_volume": [2.02988, 2.02988, 0.0, 10.0], # 5_1 is torus (0 vol), 5_2 is hyperbolic
        "braid_index": [3, 2, 3, 3]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path

def test_validation_entry_creation():
    """Test that ValidationEntry dataclass works correctly."""
    entry = ValidationEntry(
        knot_id="3_1",
        crossing_number=3,
        atlas_volume=2.0,
        knotinfo_volume=2.0,
        match=True
    )
    assert entry.knot_id == "3_1"
    assert entry.match is True

def test_validator_initialization():
    """Test HyperbolicVolumeValidator initialization."""
    validator = HyperbolicVolumeValidator(tolerance=1e-5)
    assert validator.tolerance == 1e-5
    assert validator.KNOTOINFO_API_BASE is not None

@patch('code.analysis.validation.HyperbolicVolumeValidator._fetch_knotinfo_volume')
def test_validate_single_knot_match(mock_fetch, sample_df):
    """Test validation of a single knot that matches."""
    mock_fetch.return_value = 2.02988
    
    validator = HyperbolicVolumeValidator()
    row = sample_df.iloc[0].to_dict()
    
    entry = validator.validate_single_knot(row)
    
    assert entry.match is True
    assert entry.knotinfo_volume == 2.02988
    assert entry.error_message is None

@patch('code.analysis.validation.HyperbolicVolumeValidator._fetch_knotinfo_volume')
def test_validate_single_knot_mismatch(mock_fetch, sample_df):
    """Test validation of a single knot that does not match."""
    mock_fetch.return_value = 5.0 # Significant difference
    
    validator = HyperbolicVolumeValidator()
    row = sample_df.iloc[0].to_dict()
    
    entry = validator.validate_single_knot(row)
    
    assert entry.match is False
    assert "Mismatch" in entry.error_message

@patch('code.analysis.validation.HyperbolicVolumeValidator._fetch_knotinfo_volume')
def test_validate_single_knot_missing_atlas(mock_fetch, sample_df):
    """Test validation when atlas volume is missing."""
    mock_fetch.return_value = 2.0
    
    validator = HyperbolicVolumeValidator()
    row = sample_df.iloc[2].to_dict() # 5_1 has volume 0.0, but let's test None
    row["hyperbolic_volume"] = None
    
    entry = validator.validate_single_knot(row)
    
    assert entry.error_message == "Atlas volume missing"
    assert entry.match is False

@patch('code.analysis.validation.HyperbolicVolumeValidator._fetch_knotinfo_volume')
def test_validate_dataset(mock_fetch, sample_df, temp_output_dir):
    """Test the full dataset validation flow."""
    # Mock returns: match, match, error, match
    mock_fetch.side_effect = [2.02988, 2.02988, None, 10.0]
    
    validator = HyperbolicVolumeValidator()
    result = validator.validate_dataset(sample_df)
    
    assert result.total_records == 4
    assert result.successful_lookups == 3 # 5_1 failed (0 vol -> error or skipped)
    # Actually 5_1 has 0.0 volume. The logic checks if <= 0.
    # Let's check the logic: if atlas_vol_float <= 0: error_message = "Non-positive volume"
    # So 5_1 should be a failure (error_message set).
    # 3_1: match
    # 4_1: match
    # 5_1: error (0 volume)
    # 5_2: match
    
    # Re-evaluating based on mock:
    # 3_1: fetch 2.02988 -> match
    # 4_1: fetch 2.02988 -> match
    # 5_1: atlas 0.0 -> error "Non-positive volume" (fetch not called)
    # 5_2: fetch 10.0 -> match
    
    # So successful_lookups should be 3 (3_1, 4_1, 5_2)
    # failed_lookups should be 1 (5_1)
    # matches should be 3
    
    assert result.matches_within_tolerance == 3
    assert result.matches_percentage == 100.0

def test_generate_validation_summary():
    """Test summary generation."""
    result = ValidationResult(
        total_records=10,
        successful_lookups=10,
        failed_lookups=0,
        matches_within_tolerance=9,
        matches_percentage=90.0,
        tolerance=1e-6,
        entries=[]
    )
    
    summary = generate_validation_summary(result)
    
    assert summary["total_records"] == 10
    assert summary["matches_percentage"] == 90.0
    assert summary["status"] == "PASS"

def test_write_validation_report_md(temp_output_dir):
    """Test Markdown report generation."""
    result = ValidationResult(
        total_records=5,
        successful_lookups=5,
        failed_lookups=0,
        matches_within_tolerance=4,
        matches_percentage=80.0,
        tolerance=1e-6,
        entries=[]
    )
    
    output_path = temp_output_dir / "test_report.md"
    write_validation_report_md(result, output_path)
    
    assert output_path.exists()
    content = output_path.read_text()
    assert "Hyperbolic Volume Validation Report" in content
    assert "FAIL" in content # Because 80% < 90%