import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd

from code.validate_covariates import main, validate_covariate_file, ensure_directories

def test_validate_covariate_file_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file_path = base / "missing.csv"
        expected_ids = {1, 2, 3}
        
        result = validate_covariate_file(file_path, expected_ids, "test_covariate")
        
        assert result["exists"] is False
        assert result["valid"] is False
        assert "File does not exist" in result["issues"]

def test_validate_covariate_file_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file_path = base / "empty.csv"
        file_path.touch()
        expected_ids = {1, 2, 3}
        
        result = validate_covariate_file(file_path, expected_ids, "test_covariate")
        
        assert result["exists"] is True
        assert result["valid"] is False
        assert any("Empty" in issue or "no columns" in issue for issue in result["issues"])

def test_validate_covariate_file_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file_path = base / "valid.csv"
        
        # Create a valid CSV
        df = pd.DataFrame({
            "participant_id": [1, 2, 3],
            "value": [10, 20, 30]
        })
        df.to_csv(file_path, index=False)
        
        expected_ids = {1, 2, 3}
        result = validate_covariate_file(file_path, expected_ids, "test_covariate")
        
        assert result["exists"] is True
        assert result["valid"] is True
        assert len(result["issues"]) == 0

def test_validate_covariate_file_missing_participants():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file_path = base / "partial.csv"
        
        # Create a CSV with missing participants
        df = pd.DataFrame({
            "participant_id": [1, 2], # 3 is missing
            "value": [10, 20]
        })
        df.to_csv(file_path, index=False)
        
        expected_ids = {1, 2, 3}
        result = validate_covariate_file(file_path, expected_ids, "test_covariate")
        
        assert result["valid"] is False
        assert any("Missing" in issue for issue in result["issues"])

def test_validate_covariate_file_extra_participants():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file_path = base / "extra.csv"
        
        # Create a CSV with extra participants
        df = pd.DataFrame({
            "participant_id": [1, 2, 3, 4], # 4 is extra
            "value": [10, 20, 30, 40]
        })
        df.to_csv(file_path, index=False)
        
        expected_ids = {1, 2, 3}
        result = validate_covariate_file(file_path, expected_ids, "test_covariate")
        
        assert result["valid"] is False
        assert any("extra" in issue.lower() for issue in result["issues"])

def test_validate_covariate_file_null_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file_path = base / "nulls.csv"
        
        # Create a CSV with null participant_ids
        df = pd.DataFrame({
            "participant_id": [1, None, 3],
            "value": [10, 20, 30]
        })
        df.to_csv(file_path, index=False)
        
        expected_ids = {1, 3} # None is dropped from expected set logic usually, but here we check the file
        # The function checks for nulls in the file
        result = validate_covariate_file(file_path, expected_ids, "test_covariate")
        
        assert result["valid"] is False
        assert any("missing participant_id" in issue for issue in result["issues"])
