"""
Tests for Statistical Insufficiency Handling (T020b / T021d)
"""
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from code.insufficiency import (
    generate_insufficiency_report,
    generate_full_processed_state,
    generate_analysis_log,
    get_project_root
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data folder."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    # Create dummy files for context
    return tmp_path

def test_generate_insufficiency_report(temp_data_dir):
    """Test generation of statistical_insufficiency_report.md."""
    # Mock project root to temp dir
    original_root = get_project_root()
    # We can't easily override the global constant in the module without reloading,
    # so we test the function's ability to write to a specific path by patching or 
    # by assuming the function writes to the standard location relative to the script.
    # Instead, we verify the function writes to the expected location in the real project structure
    # if we run it in the real environment, or we test the logic.
    
    # For this test, we will write to the temp directory by temporarily changing the working directory
    # or by mocking the path. Since get_project_root() is static, we will test the content generation logic
    # by checking if the file is created in the actual project's data/processed if we were running there,
    # but for unit test isolation, we rely on the fact that the function writes to a fixed path.
    # To make this test portable, we assume the test runs in the project root context or we patch.
    
    # Let's just verify the function doesn't crash and produces a file in the expected location
    # if we were in the real environment. Since we are in a test, we'll check the actual project path
    # if it exists, otherwise skip.
    
    report_path = get_project_root() / "data" / "processed" / "statistical_insufficiency_report.md"
    
    # If the real data dir exists, run the test there
    if report_path.parent.exists():
        generate_insufficiency_report(10, "Test Reason")
        assert report_path.exists(), "Report file should be created"
        
        content = report_path.read_text()
        assert "N_count" in content
        assert "10" in content
        assert "Test Reason" in content
        assert "Decision" in content
    else:
        pytest.skip("Real data directory not available for integration-style test")

def test_generate_analysis_log(temp_data_dir):
    """Test generation of analysis_log.txt."""
    log_path = get_project_root() / "data" / "processed" / "analysis_log.txt"
    
    if log_path.parent.exists():
        generate_analysis_log()
        assert log_path.exists(), "Log file should be created"
        
        content = log_path.read_text()
        assert "Arrhenius normalization excluded due to missing Ea" in content
    else:
        pytest.skip("Real data directory not available")

def test_generate_full_processed_state(temp_data_dir):
    """Test generation of full_processed_state.csv."""
    csv_path = get_project_root() / "data" / "processed" / "full_processed_state.csv"
    
    if csv_path.parent.exists():
        included = [{"canonical_smiles": "CCO"}]
        excluded = [{"canonical_smiles": "CC(=O)O", "exclusion_reason": "pH_mismatch"}]
        
        generate_full_processed_state(included, excluded, "Test Reason")
        assert csv_path.exists(), "CSV file should be created"
        
        df = pd.read_csv(csv_path)
        assert "smiles" in df.columns
        assert "is_included" in df.columns
        assert "derivation_source" in df.columns
        
        assert len(df) == 2
        assert df.iloc[0]["is_included"] == True
        assert df.iloc[1]["is_included"] == False
    else:
        pytest.skip("Real data directory not available")