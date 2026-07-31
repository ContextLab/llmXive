"""
Integration test for the full coverage validation pipeline.

Verifies that run_coverage_validation() successfully generates
data/processed/coverage_report.json with valid structure.
"""
import json
import tempfile
import os
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import patch
from code.services.coverage_validation import run_coverage_validation
from code.config import CONFIG

@pytest.fixture
def mock_config_and_files():
    """Create temporary files and mock CONFIG paths for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create mock data files
        preprocessed_df = pd.DataFrame({
            "text": ["test post " + str(i) for i in range(100)],
            "user_id": ["user1"] * 100
        })
        scoring_df = pd.DataFrame({
            "text": ["test post " + str(i) for i in range(98)],
            "anxiety_score": [0.5] * 98,
            "confidence_score": [0.8] * 98
        })
        
        preprocessed_path = tmp_path / "preprocessed_text.csv"
        scoring_path = tmp_path / "scoring_results.csv"
        output_path = tmp_path / "coverage_report.json"
        
        preprocessed_df.to_csv(preprocessed_path, index=False)
        scoring_df.to_csv(scoring_path, index=False)
        
        # Mock CONFIG to point to temp directory
        with patch.object(CONFIG, 'DATA_PROCESSED_DIR', tmp_path):
            yield {
                "preprocessed": preprocessed_path,
                "scoring": scoring_path,
                "output": output_path
            }

def test_run_coverage_validation_integration(mock_config_and_files):
    """Test that the pipeline generates a valid coverage report."""
    output_path = mock_config_and_files["output"]
    
    # Run the pipeline
    result_path = run_coverage_validation()
    
    # Verify file was created
    assert result_path.exists()
    assert result_path == output_path
    
    # Verify content structure
    with open(result_path, 'r') as f:
        report = json.load(f)
    
    assert "preprocessed_count" in report
    assert "scoring_count" in report
    assert "coverage_ratio" in report
    assert "threshold" in report
    assert "is_valid" in report
    assert "message" in report
    
    # Verify values
    assert report["preprocessed_count"] == 100
    assert report["scoring_count"] == 98
    assert report["is_valid"] is True
    assert report["coverage_ratio"] == 0.98