"""
Unit tests for T035b: Latency Exclusion Verifier.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock the config module to avoid path issues in tests
@pytest.fixture
def mock_config():
    with patch('analysis.latency_exclusion_verifier.get_path') as mock_get_path:
        with patch('analysis.latency_exclusion_verifier.get_hyperparameter') as mock_get_hp:
            # Setup mock paths
            mock_get_path.side_effect = lambda key: {
                "processed_evaluation_outcomes": "/tmp/test_filtered.json",
                "artifacts_latency_exclusion_verified": "/tmp/test_result.json"
            }.get(key, f"/tmp/{key}.json")
            mock_get_hp.return_value = 150 # Default latency threshold
            yield mock_get_path, mock_get_hp

@pytest.fixture
def temp_filtered_file():
    """Create a temporary filtered outcomes file."""
    data = {
        "outcomes": [
            {"task_id": "1", "success": True, "latency_ms": 100},
            {"task_id": "2", "success": False, "latency_ms": 120, "failure_category": "semantic"},
            {"task_id": "3", "success": True, "latency_ms": 90}
        ],
        "metadata": {
            "total_tasks": 5,
            "latency_failures_excluded": 2
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_original_file():
    """Create a temporary original outcomes file."""
    data = [
        {"task_id": "1", "success": True, "latency_ms": 100},
        {"task_id": "2", "success": False, "latency_ms": 120, "failure_category": "semantic"},
        {"task_id": "3", "success": True, "latency_ms": 90},
        {"task_id": "4", "success": False, "latency_ms": 200, "is_latency_failure": True},
        {"task_id": "5", "success": False, "latency_ms": 180, "failure_category": "latency"}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_filtered_outcomes_success(mock_config, temp_filtered_file):
    """Test successful loading of filtered outcomes."""
    from analysis.latency_exclusion_verifier import load_filtered_outcomes
    
    # Update mock to point to our temp file
    mock_get_path, _ = mock_config
    mock_get_path.side_effect = lambda key: {
        "processed_evaluation_outcomes": temp_filtered_file,
        "artifacts_latency_exclusion_verified": "/tmp/test_result.json"
    }.get(key, f"/tmp/{key}.json")
    
    outcomes = load_filtered_outcomes()
    assert len(outcomes) == 3
    assert outcomes[0]["task_id"] == "1"

def test_load_filtered_outcomes_missing_file(mock_config):
    """Test error handling when file is missing."""
    from analysis.latency_exclusion_verifier import load_filtered_outcomes
    from utils.exceptions import LlmXiveError
    
    mock_get_path, _ = mock_config
    mock_get_path.side_effect = lambda key: "/tmp/nonexistent.json"
    
    with pytest.raises(LlmXiveError, match="not found"):
        load_filtered_outcomes()

def test_count_latency_failures(mock_config, temp_original_file):
    """Test counting latency failures."""
    from analysis.latency_exclusion_verifier import load_all_outcomes, count_latency_failures
    
    mock_get_path, _ = mock_config
    mock_get_path.side_effect = lambda key: {
        "processed_evaluation_outcomes": "/tmp/test_filtered.json",
        "artifacts_latency_exclusion_verified": "/tmp/test_result.json",
        "processed_evaluation_outcomes_raw": temp_original_file # Hack to return this
    }.get(key, temp_original_file)
    
    # We need to patch load_all_outcomes to use our temp file directly
    # Since the function logic is complex, we test the counting logic directly
    outcomes = [
        {"task_id": "1", "is_latency_failure": False},
        {"task_id": "2", "failure_category": "latency"},
        {"task_id": "3", "is_latency_failure": True},
        {"task_id": "4", "failure_category": "semantic"}
    ]
    
    count = count_latency_failures(outcomes)
    assert count == 2

def test_verify_exclusion_logic_valid():
    """Test verification logic with valid data."""
    from analysis.latency_exclusion_verifier import verify_exclusion_logic
    
    result = verify_exclusion_logic(
        total_tasks=100,
        latency_failure_count=10,
        filtered_count=90
    )
    
    assert result["verification_passed"] is True
    assert result["expected_filtered"] == 90
    assert result["total_tasks"] == 100

def test_verify_exclusion_logic_invalid():
    """Test verification logic with invalid data."""
    from analysis.latency_exclusion_verifier import verify_exclusion_logic
    
    result = verify_exclusion_logic(
        total_tasks=100,
        latency_failure_count=10,
        filtered_count=85 # Incorrect
    )
    
    assert result["verification_passed"] is False
    assert result["expected_filtered"] == 90
    assert "FAILED" in result["message"]

def test_write_verification_result(mock_config):
    """Test writing the verification result."""
    from analysis.latency_exclusion_verifier import write_verification_result
    
    result = {
        "total_tasks": 10,
        "latency_failures": 2,
        "filtered_tasks": 8,
        "verification_passed": True,
        "message": "Test message"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_get_path, _ = mock_config
        mock_get_path.side_effect = lambda key: {
            "artifacts_latency_exclusion_verified": os.path.join(tmpdir, "result.json")
        }.get(key, os.path.join(tmpdir, "test.json"))
        
        write_verification_result(result)
        
        # Check file exists
        output_path = os.path.join(tmpdir, "result.json")
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            saved = json.load(f)
        
        assert saved["verification_passed"] is True
        assert "verified_at" in saved
