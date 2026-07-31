"""
Unit tests for coverage validation logic.
"""
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from code.services.coverage_validation import validate_coverage, run_coverage_validation
from code.config import CONFIG

def test_validate_coverage_pass():
    """Test that validation passes when coverage is >= 95%."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        preprocessed_df = pd.DataFrame({"text": ["a"] * 100})
        scoring_df = pd.DataFrame({"text": ["a"] * 96, "score": [0.5] * 96})
        
        preprocessed_path = tmp_path / "preprocessed.csv"
        scoring_path = tmp_path / "scoring.csv"
        
        preprocessed_df.to_csv(preprocessed_path, index=False)
        scoring_df.to_csv(scoring_path, index=False)
        
        result = validate_coverage(preprocessed_path, scoring_path, threshold=0.95)
        
        assert result["preprocessed_count"] == 100
        assert result["scoring_count"] == 96
        assert result["coverage_ratio"] == 0.96
        assert result["is_valid"] is True

def test_validate_coverage_fail():
    """Test that validation fails when coverage is < 95%."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        preprocessed_df = pd.DataFrame({"text": ["a"] * 100})
        scoring_df = pd.DataFrame({"text": ["a"] * 90, "score": [0.5] * 90})
        
        preprocessed_path = tmp_path / "preprocessed.csv"
        scoring_path = tmp_path / "scoring.csv"
        
        preprocessed_df.to_csv(preprocessed_path, index=False)
        scoring_df.to_csv(scoring_path, index=False)
        
        result = validate_coverage(preprocessed_path, scoring_path, threshold=0.95)
        
        assert result["preprocessed_count"] == 100
        assert result["scoring_count"] == 90
        assert result["coverage_ratio"] == 0.90
        assert result["is_valid"] is False

def test_validate_coverage_empty_preprocessed():
    """Test behavior when preprocessed file is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        preprocessed_df = pd.DataFrame({"text": []})
        scoring_df = pd.DataFrame({"text": [], "score": []})
        
        preprocessed_path = tmp_path / "preprocessed.csv"
        scoring_path = tmp_path / "scoring.csv"
        
        preprocessed_df.to_csv(preprocessed_path, index=False)
        scoring_df.to_csv(scoring_path, index=False)
        
        result = validate_coverage(preprocessed_path, scoring_path, threshold=0.95)
        
        assert result["preprocessed_count"] == 0
        assert result["coverage_ratio"] == 0.0
        assert result["is_valid"] is False

def test_validate_coverage_missing_file():
    """Test that FileNotFoundError is raised when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        preprocessed_path = tmp_path / "nonexistent.csv"
        scoring_path = tmp_path / "scoring.csv"
        
        scoring_df = pd.DataFrame({"text": ["a"], "score": [0.5]})
        scoring_path = tmp_path / "scoring.csv"
        scoring_df.to_csv(scoring_path, index=False)
        
        with pytest.raises(FileNotFoundError):
            validate_coverage(preprocessed_path, scoring_path)
