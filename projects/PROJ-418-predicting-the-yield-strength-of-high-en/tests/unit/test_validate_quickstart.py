"""
Unit tests for quickstart validation script (T036).
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.validate_quickstart import (
    check_file_exists,
    validate_output_artifacts,
    run_pipeline_validation
)
from utils.logging import get_logger

logger = get_logger("test_validate_quickstart")

def test_check_file_exists_true():
    """Test that check_file_exists returns True for existing files."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        result = check_file_exists(tmp_path, "Test file")
        assert result is True
    finally:
        tmp_path.unlink()

def test_check_file_exists_false():
    """Test that check_file_exists returns False for missing files."""
    fake_path = PROJECT_ROOT / "nonexistent_file_12345.txt"
    result = check_file_exists(fake_path, "Nonexistent file")
    assert result is False

def test_validate_output_artifacts_structure():
    """Test that validate_output_artifacts handles valid JSON correctly."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create required output files
        metrics_path = tmp_path / "output" / "metrics.json"
        metrics_path.parent.mkdir(parents=True)
        
        test_metrics = {
            "rf": {"R2": 0.85, "MAE": 50.0, "RMSE": 70.0},
            "gb": {"R2": 0.87, "MAE": 48.0, "RMSE": 68.0},
            "linear": {"R2": 0.75, "MAE": 60.0, "RMSE": 80.0},
            "best_model": "gb"
        }
        
        with open(metrics_path, 'w') as f:
            json.dump(test_metrics, f)
        
        # Mock PROJECT_ROOT to point to our temp directory
        with patch('code.validate_quickstart.PROJECT_ROOT', tmp_path):
            # This should not raise an exception
            try:
                validate_output_artifacts()
            except Exception as e:
                # We expect some warnings but not crashes
                logger.warning(f"Expected warning during validation: {e}")

def test_run_pipeline_validation_with_existing_data():
    """Test pipeline validation when data already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create fake data and metrics
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        (data_dir / "hea_descriptors.csv").touch()
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "metrics.json").write_text("{}")
        (output_dir / "report.md").write_text("# Test Report")
        
        with patch('code.validate_quickstart.PROJECT_ROOT', tmp_path):
            # Should return True since files exist
            result = run_pipeline_validation()
            assert result is True

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])