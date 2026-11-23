import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

code_root = Path(__file__).parent.parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from data_generation.expert_system_validator import main as validator_main
from utils.config import get_data_dir

@pytest.fixture
def temp_trajectories_file():
    """Creates a temporary trajectories.jsonl file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Create 10 valid trajectories
        for i in range(10):
            traj = {
                "trajectory_id": f"int-test-{i}",
                "actions": [
                    {"description": "Action A", "step": 1},
                    {"description": "Action B", "step": 2},
                    {"description": "Action C", "step": 3},
                    {"description": "Action D", "step": 4}
                ],
                "state": "success"
            }
            f.write(json.dumps(traj) + "\n")
        return f.name

@pytest.fixture
def temp_trajectories_file_failing():
    """Creates a temporary file with failing trajectories."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Create 10 trajectories with errors
        for i in range(10):
            traj = {
                "trajectory_id": f"int-test-fail-{i}",
                "actions": [
                    {"description": "Action A", "step": 1},
                    {"description": "Error: Failed", "step": 2} # Triggers penalty
                ],
                "state": "failed"
            }
            f.write(json.dumps(traj) + "\n")
        return f.name

def test_validator_passes_good_data(temp_trajectories_file, monkeypatch, tmp_path):
    """Test that validator exits 0 when data is good."""
    # Mock get_data_dir to return tmp_path
    monkeypatch.setattr('utils.config.get_data_dir', lambda: tmp_path)
    monkeypatch.setattr('data_generation.expert_system_validator.get_data_dir', lambda: tmp_path)
    
    # Mock the trajectory loading path
    input_path = Path(temp_trajectories_file)
    output_results = tmp_path / "synthetic_benchmark" / "review_results.json"
    output_human = tmp_path / "synthetic_benchmark" / "needs_human_review.json"
    
    # We need to mock the file path inside the function or set up the directory structure
    # The function uses get_data_dir() / "synthetic_benchmark" / "trajectories.jsonl"
    # So we need to move the temp file there or mock the path resolution
    
    # Simpler approach: Mock the open call and file existence check
    # But the function reads from a specific path. Let's copy the file.
    benchmark_dir = tmp_path / "synthetic_benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    target_file = benchmark_dir / "trajectories.jsonl"
    
    with open(input_path, 'r') as src:
        with open(target_file, 'w') as dst:
            dst.write(src.read())
    
    # Run main
    with patch('sys.exit') as mock_exit:
        with patch('builtins.print'): # Suppress prints
            validator_main()
            mock_exit.assert_called_with(0)
    
    assert output_results.exists()
    assert not output_human.exists()

def test_validator_triggers_human_review(temp_trajectories_file_failing, monkeypatch, tmp_path):
    """Test that validator exits 42 and creates needs_human_review.json when data is bad."""
    benchmark_dir = tmp_path / "synthetic_benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    target_file = benchmark_dir / "trajectories.jsonl"
    
    with open(temp_trajectories_file_failing, 'r') as src:
        with open(target_file, 'w') as dst:
            dst.write(src.read())
    
    output_results = benchmark_dir / "review_results.json"
    output_human = benchmark_dir / "needs_human_review.json"
    
    exit_code = None
    def capture_exit(code):
        nonlocal exit_code
        exit_code = code
        raise SystemExit(code)
    
    try:
        with patch('sys.exit', side_effect=capture_exit):
            with patch('builtins.print'):
                validator_main()
    except SystemExit:
        pass
    
    assert exit_code == 42
    assert output_results.exists()
    assert output_human.exists()
    
    with open(output_human, 'r') as f:
        human_data = json.load(f)
        assert len(human_data) == 10
        for item in human_data:
            assert "trajectory_id" in item
            assert "reason" in item
            assert "timestamp" in item
