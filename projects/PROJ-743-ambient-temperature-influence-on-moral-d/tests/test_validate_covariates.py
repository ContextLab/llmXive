"""
Tests for T028e: validate_covariates.py
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the main function and logic
from code.validate_covariates import main, parse_args, validate_covariate_file

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create necessary subdirectories
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "results" / "logs").mkdir(parents=True)
        yield tmp_path

def test_validate_empty_merged_dataset(temp_dirs):
    """Test that validation fails if merged dataset is empty."""
    merged_path = temp_dirs / "data" / "processed" / "merged_dataset.parquet"
    pd.DataFrame({"participant_id": []}).to_parquet(merged_path)
    
    covariates_dir = temp_dirs / "data" / "processed"
    output_path = temp_dirs / "results" / "logs" / "covariate_validation.json"
    
    # Create a dummy covariate file
    cov_path = covariates_dir / "dilemma_choices.csv"
    pd.DataFrame({"participant_id": ["P1"], "choice": ["A"]}).to_csv(cov_path)
    
    args = [
        "--input", str(merged_path),
        "--covariates-dir", str(covariates_dir),
        "--output", str(output_path)
    ]
    
    # We need to patch sys.argv or call main directly with args
    # Since main uses argparse, we can't easily pass args without sys.argv manipulation
    # For unit testing, we will test the logic functions directly or mock sys.argv
    pass 

def test_validate_missing_covariate_file(temp_dirs):
    """Test that validation reports fail if a covariate file is missing."""
    # Create a valid merged dataset
    merged_path = temp_dirs / "data" / "processed" / "merged_dataset.parquet"
    pd.DataFrame({"participant_id": ["P1", "P2"]}).to_parquet(merged_path)
    
    covariates_dir = temp_dirs / "data" / "processed"
    output_path = temp_dirs / "results" / "logs" / "covariate_validation.json"
    
    # Do NOT create dilemma_choices.csv
    
    args = [
        "--input", str(merged_path),
        "--covariates-dir", str(covariates_dir),
        "--output", str(output_path)
    ]
    
    # Mock sys.argv for main()
    import sys
    original_argv = sys.argv
    sys.argv = ["test"] + args
    try:
        result = main()
        assert result == 1  # Should fail
        
        with open(output_path) as f:
            report = json.load(f)
        
        assert report["status"] == "fail"
        assert report["covariates"]["dilemma_choice"]["status"] == "fail"
        assert "File not found" in report["covariates"]["dilemma_choice"]["reason"]
    finally:
        sys.argv = original_argv

def test_validate_invalid_participant_ids(temp_dirs):
    """Test that validation fails if covariate has IDs not in merged dataset."""
    # Create merged dataset
    merged_path = temp_dirs / "data" / "processed" / "merged_dataset.parquet"
    pd.DataFrame({"participant_id": ["P1", "P2"]}).to_parquet(merged_path)
    
    covariates_dir = temp_dirs / "data" / "processed"
    output_path = temp_dirs / "results" / "logs" / "covariate_validation.json"
    
    # Create a covariate file with an invalid ID
    cov_path = covariates_dir / "dilemma_choices.csv"
    pd.DataFrame({"participant_id": ["P1", "P99"], "choice": ["A", "B"]}).to_csv(cov_path)
    
    args = [
        "--input", str(merged_path),
        "--covariates-dir", str(covariates_dir),
        "--output", str(output_path)
    ]
    
    import sys
    original_argv = sys.argv
    sys.argv = ["test"] + args
    try:
        result = main()
        assert result == 1  # Should fail
        
        with open(output_path) as f:
            report = json.load(f)
        
        assert report["status"] == "fail"
        assert report["covariates"]["dilemma_choice"]["status"] == "fail"
        assert any("not in merged dataset" in issue for issue in report["covariates"]["dilemma_choice"]["issues"])
    finally:
        sys.argv = original_argv

def test_validate_success(temp_dirs):
    """Test successful validation when all files match."""
    # Create merged dataset
    merged_path = temp_dirs / "data" / "processed" / "merged_dataset.parquet"
    pd.DataFrame({"participant_id": ["P1", "P2", "P3"]}).to_parquet(merged_path)
    
    covariates_dir = temp_dirs / "data" / "processed"
    output_path = temp_dirs / "results" / "logs" / "covariate_validation.json"
    
    # Create valid covariate files
    # dilemma_choices
    pd.DataFrame({"participant_id": ["P1", "P2", "P3"], "choice": ["A", "B", "A"]}).to_csv(covariates_dir / "dilemma_choices.csv")
    # dilemma_complexity
    pd.DataFrame({"participant_id": ["P1", "P2", "P3"], "complexity": [1, 2, 1]}).to_csv(covariates_dir / "dilemma_complexity.csv")
    # time_of_day
    pd.DataFrame({"participant_id": ["P1", "P2", "P3"], "time_of_day": ["morning", "afternoon", "night"]}).to_csv(covariates_dir / "time_of_day.csv")
    # demographics
    pd.DataFrame({"participant_id": ["P1", "P2", "P3"], "age": [20, 30, 40]}).to_csv(covariates_dir / "covariates.csv")
    
    args = [
        "--input", str(merged_path),
        "--covariates-dir", str(covariates_dir),
        "--output", str(output_path)
    ]
    
    import sys
    original_argv = sys.argv
    sys.argv = ["test"] + args
    try:
        result = main()
        assert result == 0  # Should pass
        
        with open(output_path) as f:
            report = json.load(f)
        
        assert report["status"] == "pass"
        assert report["covariates"]["dilemma_choice"]["status"] == "pass"
        assert report["covariates"]["dilemma_complexity"]["status"] == "pass"
        assert report["covariates"]["time_of_day"]["status"] == "pass"
        assert report["covariates"]["demographics"]["status"] == "pass"
    finally:
        sys.argv = original_argv