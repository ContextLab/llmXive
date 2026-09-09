"""
Unit tests for the human_review_consumer module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to mock the project root utilities since we are running in a temp dir
# or ensure the test environment has the correct structure.
# For this test, we will patch the config functions.

@pytest.fixture
def temp_project_root():
    """Creates a temporary directory structure mimicking the project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data" / "synthetic_benchmark"
        data_dir.mkdir(parents=True)
        
        # Create dummy files
        (data_dir / "needs_human_review.json").write_text(json.dumps([
            {"trajectory_id": "traj_001", "reason": "Low semantic score", "timestamp": "2023-01-01T00:00:00"}
        ]))
        
        (data_dir / "trajectories.jsonl").write_text(json.dumps({
            "trajectory_id": "traj_001",
            "steps": ["open app", "click button", "type text"]
        }) + "\n")
        
        yield root

@patch('code.data_generation.human_review_consumer.get_project_root')
@patch('code.data_generation.human_review_consumer.get_data_dir')
def test_load_needs_review_empty(mock_get_data_dir, mock_get_root, temp_project_root):
    """Test loading an empty or missing needs_review file."""
    from code.data_generation.human_review_consumer import load_needs_review
    
    # Setup mocks to point to our temp dir
    mock_get_root.return_value = temp_project_root
    mock_get_data_dir.return_value = temp_project_root / "data" / "synthetic_benchmark"
    
    # Test with missing file
    missing_path = temp_project_root / "data" / "synthetic_benchmark" / "nonexistent.json"
    result = load_needs_review(missing_path)
    assert result == []

@patch('code.data_generation.human_review_consumer.get_project_root')
@patch('code.data_generation.human_review_consumer.get_data_dir')
def test_load_needs_review_valid(mock_get_data_dir, mock_get_root, temp_project_root):
    """Test loading a valid needs_review file."""
    from code.data_generation.human_review_consumer import load_needs_review
    
    mock_get_root.return_value = temp_project_root
    mock_get_data_dir.return_value = temp_project_root / "data" / "synthetic_benchmark"
    
    path = temp_project_root / "data" / "synthetic_benchmark" / "needs_human_review.json"
    result = load_needs_review(path)
    
    assert len(result) == 1
    assert result[0]["trajectory_id"] == "traj_001"
    assert result[0]["reason"] == "Low semantic score"

@patch('code.data_generation.human_review_consumer.get_project_root')
@patch('code.data_generation.human_review_consumer.get_data_dir')
def test_load_trajectories(mock_get_data_dir, mock_get_root, temp_project_root):
    """Test loading trajectories from JSONL."""
    from code.data_generation.human_review_consumer import load_trajectories
    
    mock_get_root.return_value = temp_project_root
    mock_get_data_dir.return_value = temp_project_root / "data" / "synthetic_benchmark"
    
    path = temp_project_root / "data" / "synthetic_benchmark" / "trajectories.jsonl"
    result = load_trajectories(path)
    
    assert "traj_001" in result
    assert result["traj_001"]["steps"][0] == "open app"

@patch('code.data_generation.human_review_consumer.get_project_root')
@patch('code.data_generation.human_review_consumer.get_data_dir')
def test_process_reviews_integration(mock_get_data_dir, mock_get_root, temp_project_root):
    """Test the full review process flow."""
    from code.data_generation.human_review_consumer import process_reviews, save_results, load_existing_results
    
    mock_get_root.return_value = temp_project_root
    mock_get_data_dir.return_value = temp_project_root / "data" / "synthetic_benchmark"
    
    needs_review_path = temp_project_root / "data" / "synthetic_benchmark" / "needs_human_review.json"
    needs_review_items = json.loads(needs_review_path.read_text())
    
    trajectories_path = temp_project_root / "data" / "synthetic_benchmark" / "trajectories.jsonl"
    trajectories = json.loads(trajectories_path.read_text())
    # Convert single line JSONL to dict for test
    trajectories = {t["trajectory_id"]: t for t in trajectories}
    
    results_path = temp_project_root / "data" / "synthetic_benchmark" / "review_results.json"
    existing_results = {"reviews": []}
    
    # Mock the human feedback input to simulate 'Accept'
    with patch('builtins.input', return_value='A'):
        final_results = process_reviews(needs_review_items, trajectories, existing_results)
    
    assert len(final_results["reviews"]) == 1
    assert final_results["reviews"][0]["decision"] == "A"
    assert final_results["reviews"][0]["trajectory_id"] == "traj_001"