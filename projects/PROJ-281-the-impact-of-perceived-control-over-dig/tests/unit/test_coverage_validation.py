"""
Unit tests for coverage validation logic.
"""
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from code.services.coverage_validation import validate_coverage, CoverageError

@pytest.fixture
def temp_files():
    """Create temporary CSV files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create preprocessed file with 100 rows
        preprocessed_path = tmpdir / "preprocessed_text.csv"
        preprocessed_df = pd.DataFrame({
            "text": [f"Sample text {i}" for i in range(100)],
            "user_id": [f"user_{i % 10}" for i in range(100)]
        })
        preprocessed_df.to_csv(preprocessed_path, index=False)
        
        # Create scored file with 95 rows (95% coverage)
        scored_path = tmpdir / "scoring_results.csv"
        scored_df = pd.DataFrame({
            "text": [f"Sample text {i}" for i in range(95)],
            "anxiety_score": [0.5] * 95,
            "confidence_score": [0.8] * 95
        })
        scored_df.to_csv(scored_path, index=False)
        
        yield preprocessed_path, scored_path, tmpdir

def test_validate_coverage_pass(temp_files):
    """Test that validation passes at exactly 95% coverage."""
    preprocessed_path, scored_path, _ = temp_files
    
    report = validate_coverage(preprocessed_path, scored_path)
    
    assert report["preprocessed_count"] == 100
    assert report["scored_count"] == 95
    assert report["coverage_percentage"] == 95.0
    assert report["status"] == "PASS"

def test_validate_coverage_fail(temp_files):
    """Test that validation fails below 95% coverage."""
    preprocessed_path, scored_path, tmpdir = temp_files
    
    # Create scored file with only 90 rows (90% coverage)
    scored_path_fail = tmpdir / "scoring_results_fail.csv"
    scored_df = pd.DataFrame({
        "text": [f"Sample text {i}" for i in range(90)],
        "anxiety_score": [0.5] * 90,
        "confidence_score": [0.8] * 90
    })
    scored_df.to_csv(scored_path_fail, index=False)
    
    with pytest.raises(CoverageError) as excinfo:
        validate_coverage(preprocessed_path, scored_path_fail)
    
    assert "90.00%" in str(excinfo.value)
    assert "95.0%" in str(excinfo.value)

def test_validate_coverage_missing_file(temp_files):
    """Test that FileNotFoundError is raised for missing files."""
    preprocessed_path, scored_path, _ = temp_files
    
    with pytest.raises(FileNotFoundError):
        validate_coverage(Path("nonexistent.csv"), scored_path)
    
    with pytest.raises(FileNotFoundError):
        validate_coverage(preprocessed_path, Path("nonexistent.csv"))

def test_validate_coverage_empty_preprocessed(temp_files):
    """Test handling of empty preprocessed file."""
    preprocessed_path, scored_path, tmpdir = temp_files
    
    # Create empty preprocessed file
    empty_path = tmpdir / "empty_preprocessed.csv"
    pd.DataFrame(columns=["text", "user_id"]).to_csv(empty_path, index=False)
    
    # Create empty scored file
    empty_scored_path = tmpdir / "empty_scored.csv"
    pd.DataFrame(columns=["text", "anxiety_score", "confidence_score"]).to_csv(
        empty_scored_path, index=False
    )
    
    report = validate_coverage(empty_path, empty_scored_path)
    
    assert report["preprocessed_count"] == 0
    assert report["scored_count"] == 0
    assert report["coverage_percentage"] == 0.0
    # Empty data should fail coverage check
    with pytest.raises(CoverageError):
        validate_coverage(empty_path, empty_scored_path)

def test_validate_coverage_100_percent(temp_files):
    """Test that validation passes at 100% coverage."""
    preprocessed_path, scored_path, tmpdir = temp_files
    
    # Create scored file with 100 rows
    scored_path_100 = tmpdir / "scoring_results_100.csv"
    scored_df = pd.DataFrame({
        "text": [f"Sample text {i}" for i in range(100)],
        "anxiety_score": [0.5] * 100,
        "confidence_score": [0.8] * 100
    })
    scored_df.to_csv(scored_path_100, index=False)
    
    report = validate_coverage(preprocessed_path, scored_path_100)
    
    assert report["preprocessed_count"] == 100
    assert report["scored_count"] == 100
    assert report["coverage_percentage"] == 100.0
    assert report["status"] == "PASS"