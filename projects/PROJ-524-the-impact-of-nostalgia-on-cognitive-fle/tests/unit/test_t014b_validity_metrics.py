"""
Unit tests for T014b validity metrics calculation.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock config and utils for testing
@pytest.fixture
def mock_config():
    return {
        "data": {
            "raw": "/tmp/test_raw",
            "processed": "/tmp/test_processed"
        }
    }

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Create a fake metadata file
        metadata = {"total_records": 150}
        with open(raw_dir / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Create a fake exclusion log
        exclusion = {
            "total_excluded": 30,
            "counts": {
                "ERR_MISSING_AGE_FIELD": 10,
                "ERR_MISSING_BIRTH_YEAR": 5,
                "ERR_MISSING_SCORE": 15
            }
        }
        with open(processed_dir / "exclusion_log.json", "w") as f:
            json.dump(exclusion, f)
        
        yield {
            "raw": str(raw_dir),
            "processed": str(processed_dir)
        }

@patch('code.task_t014b_validity_metrics.get_config')
@patch('code.task_t014b_validity_metrics.ensure_dirs')
def test_calculate_validity_metrics(mock_ensure, mock_get_config, temp_dirs, mock_config):
    # Update mock config to point to temp dirs
    mock_config["data"]["raw"] = temp_dirs["raw"]
    mock_config["data"]["processed"] = temp_dirs["processed"]
    mock_get_config.return_value = mock_config

    from code.task_t014b_validity_metrics import calculate_validity_metrics

    metrics = calculate_validity_metrics()

    assert metrics["status"] == "success"
    assert metrics["total_raw_records"] == 150
    assert metrics["excluded_records_count"] == 30
    assert metrics["valid_records_count"] == 120
    assert metrics["validity_percentage"] == 80.0
    assert "ERR_MISSING_AGE_FIELD" in metrics["exclusion_breakdown"]

@patch('code.task_t014b_validity_metrics.get_config')
@patch('code.task_t014b_validity_metrics.ensure_dirs')
def test_calculate_validity_metrics_missing_metadata(mock_ensure, mock_get_config, temp_dirs, mock_config):
    # Remove metadata file to test fallback
    os.remove(Path(temp_dirs["raw"]) / "metadata.json")
    
    # Create a fake CSV to test fallback counting
    with open(Path(temp_dirs["raw"]) / "dataset.csv", "w") as f:
        f.write("id,value\n1,10\n2,20\n3,30\n4,40\n5,50\n") # 5 rows
    
    mock_config["data"]["raw"] = temp_dirs["raw"]
    mock_config["data"]["processed"] = temp_dirs["processed"]
    mock_get_config.return_value = mock_config

    from code.task_t014b_validity_metrics import calculate_validity_metrics

    metrics = calculate_validity_metrics()

    # Should fall back to CSV count (5 rows)
    assert metrics["total_raw_records"] == 5
    # Excluded count remains 30 from exclusion log
    # But valid = 5 - 30 = -25 -> clamped to 0 in logic
    assert metrics["valid_records_count"] == 0
    assert metrics["validity_percentage"] == 0.0

@patch('code.task_t014b_validity_metrics.get_config')
@patch('code.task_t014b_validity_metrics.ensure_dirs')
def test_calculate_validity_metrics_unknown_total(mock_ensure, mock_get_config, temp_dirs, mock_config):
    # Remove all sources of total count
    os.remove(Path(temp_dirs["raw"]) / "metadata.json")
    os.remove(Path(temp_dirs["raw"]) / "dataset.csv")
    
    mock_config["data"]["raw"] = temp_dirs["raw"]
    mock_config["data"]["processed"] = temp_dirs["processed"]
    mock_get_config.return_value = mock_config

    from code.task_t014b_validity_metrics import calculate_validity_metrics

    metrics = calculate_validity_metrics()

    assert metrics["status"] == "unknown"
    assert metrics["total_raw_records"] == 0
    assert "Could not determine" in metrics["message"]
