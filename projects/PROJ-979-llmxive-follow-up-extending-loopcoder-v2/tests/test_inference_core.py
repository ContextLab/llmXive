"""
Tests for core convergence inference (T013a)
"""
import os
import sys
import json
import tempfile
import csv
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.inference import (
    detect_convergence,
    SandboxResult
)


class TestConvergenceDetection:
    """Test convergence detection logic"""

    def test_first_correct_detection(self):
        """Test that first correct step is detected"""
        converged, step = detect_convergence(k=1, is_correct=True, first_correct_step=None)
        assert converged is True
        assert step == 1

    def test_subsequent_correct_ignored(self):
        """Test that subsequent correct steps don't change first_correct_step"""
        converged, step = detect_convergence(k=2, is_correct=True, first_correct_step=1)
        assert converged is False
        assert step == 1

    def test_incorrect_step(self):
        """Test that incorrect steps don't trigger convergence"""
        converged, step = detect_convergence(k=1, is_correct=False, first_correct_step=None)
        assert converged is False
        assert step is None

    def test_later_convergence(self):
        """Test convergence at later step"""
        # First step incorrect
        _, step = detect_convergence(k=1, is_correct=False, first_correct_step=None)
        assert step is None
        
        # Second step correct
        converged, step = detect_convergence(k=2, is_correct=True, first_correct_step=None)
        assert converged is True
        assert step == 2


class TestSandboxResult:
    """Test SandboxResult dataclass"""

    def test_result_creation(self):
        """Test creating a SandboxResult"""
        result = SandboxResult(
            task_id="test_1",
            k=1,
            output="def add(a, b): return a + b",
            is_correct=True,
            converged=True,
            first_correct_step=1,
            censored=False
        )
        
        assert result.task_id == "test_1"
        assert result.k == 1
        assert result.is_correct is True
        assert result.converged is True
        assert result.first_correct_step == 1
        assert result.censored is False

    def test_censored_result(self):
        """Test censored result (never converged)"""
        result = SandboxResult(
            task_id="test_2",
            k=3,
            output="def multiply(a, b): return a * b",
            is_correct=False,
            converged=False,
            first_correct_step=None,
            censored=True
        )
        
        assert result.censored is True
        assert result.first_correct_step is None


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_filtered_splits(temp_dir):
    """Create sample filtered_splits.json"""
    splits = {
        "train": [
            {
                "task_id": "train_1",
                "prompt": "def add(a, b):\n    return a + b",
                "test": "assert add(1, 2) == 3",
                "difficulty": "easy"
            }
        ],
        "test": [
            {
                "task_id": "test_1",
                "prompt": "def subtract(a, b):\n    return a - b",
                "test": "assert subtract(5, 2) == 3",
                "difficulty": "easy"
            },
            {
                "task_id": "test_2",
                "prompt": "def multiply(a, b):\n    return a * b",
                "test": "assert multiply(2, 3) == 6",
                "difficulty": "medium"
            }
        ]
    }
    
    path = os.path.join(temp_dir, "filtered_splits.json")
    with open(path, "w") as f:
        json.dump(splits, f)
    
    return path

@patch("src.inference.load_model")
@patch("src.inference.execute_code")
def test_run_iterative_inference_structure(mock_execute, mock_load_model, sample_filtered_splits, temp_dir):
    """Test the structure of run_iterative_inference without actual model"""
    from src.inference import run_iterative_inference, load_input_problems
    
    # Mock model loading
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_load_model.return_value = (mock_model, mock_tokenizer)
    
    # Mock execution to return correct results
    mock_execute.return_value = {"passed": True, "output": "success"}
    
    output_path = os.path.join(temp_dir, "convergence_results_core.csv")
    
    # Run with k=1,2,3
    run_iterative_inference(
        input_path=sample_filtered_splits,
        output_path=output_path,
        k_range=[1, 2, 3],
        model_path="mock_path",
        seed=42
    )
    
    # Verify output file was created
    assert os.path.exists(output_path)
    
    # Verify CSV structure
    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Should have 2 tasks * 3 k values = 6 rows
    assert len(rows) == 6
    
    # Check required columns
    required_columns = ["task_id", "k", "output", "is_correct", "converged", "first_correct_step", "censored"]
    for col in required_columns:
        assert col in rows[0]
    
    # Verify k values
    k_values = [int(row["k"]) for row in rows]
    assert sorted(k_values) == [1, 1, 2, 2, 3, 3]
    
    # Verify task_ids
    task_ids = [row["task_id"] for row in rows]
    assert task_ids.count("test_1") == 3
    assert task_ids.count("test_2") == 3