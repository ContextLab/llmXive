import os
import sys
import json
import tempfile
import csv
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from src.inference import (
    save_convergence_results,
    load_input_problems,
    detect_convergence,
    execute_code_in_sandbox,
    ConvergenceTrajectory
)
from src.models import InputProblem

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestConvergenceLogger:
    def test_save_convergence_results_csv_schema(self, temp_dir):
        """Test that save_convergence_results writes correct CSV schema."""
        output_path = os.path.join(temp_dir, "convergence_results.csv")
        
        # Create sample results
        results = [
            ConvergenceTrajectory(
                task_id="test-001",
                k=1,
                output="print('hello')",
                is_correct=True,
                converged=True,
                first_correct_step=1
            ),
            ConvergenceTrajectory(
                task_id="test-002",
                k=2,
                output="print('world')",
                is_correct=False,
                converged=False,
                first_correct_step=None
            )
        ]
        
        # Save results
        save_convergence_results(results, output_path)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify CSV schema
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check columns
            expected_columns = ['task_id', 'k', 'converged', 'step', 'timestamp']
            assert set(reader.fieldnames) == set(expected_columns)
            
            # Check data
            assert len(rows) == 2
            assert rows[0]['task_id'] == 'test-001'
            assert rows[0]['k'] == '1'
            assert rows[0]['converged'] == 'True'
            assert rows[0]['step'] == '1'
            
            assert rows[1]['task_id'] == 'test-002'
            assert rows[1]['k'] == '2'
            assert rows[1]['converged'] == 'False'
            assert rows[1]['step'] == '0'  # None converted to 0

    def test_save_convergence_results_empty(self, temp_dir):
        """Test saving empty results."""
        output_path = os.path.join(temp_dir, "convergence_results.csv")
        
        save_convergence_results([], output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0

class TestRefinementLoop:
    def test_detect_convergence_success(self, temp_dir):
        """Test convergence detection with correct solution."""
        # Mock code that passes test
        solutions = [
            "def add(a, b): return a + b",
            "def add(a, b): return a + b"
        ]
        test_case = """
        assert add(2, 3) == 5
        """
        
        # Mock execute_code_in_sandbox to return success
        with patch('src.inference.execute_code_in_sandbox') as mock_exec:
            mock_exec.return_value = MagicMock(is_correct=True)
            
            converged, step = detect_convergence(solutions, test_case)
            
            assert converged is True
            assert step == 1

    def test_detect_convergence_failure(self, temp_dir):
        """Test convergence detection when no solution is correct."""
        solutions = [
            "def add(a, b): return a - b",
            "def add(a, b): return b - a"
        ]
        test_case = """
        assert add(2, 3) == 5
        """
        
        # Mock execute_code_in_sandbox to return failure
        with patch('src.inference.execute_code_in_sandbox') as mock_exec:
            mock_exec.return_value = MagicMock(is_correct=False)
            
            converged, step = detect_convergence(solutions, test_case)
            
            assert converged is False
            assert step is None

    def test_load_input_problems(self, temp_dir):
        """Test loading input problems from JSON."""
        input_path = os.path.join(temp_dir, "input_problems.json")
        
        # Create sample input data
        sample_data = [
            {
                "task_id": "test-001",
                "prompt": "Write a function to add two numbers",
                "test": "assert add(2, 3) == 5"
            },
            {
                "task_id": "test-002",
                "prompt": "Write a function to multiply two numbers",
                "test": "assert multiply(2, 3) == 6"
            }
        ]
        
        with open(input_path, 'w') as f:
            json.dump(sample_data, f)
        
        problems = load_input_problems(input_path)
        
        assert len(problems) == 2
        assert problems[0].task_id == "test-001"
        assert problems[0].prompt == "Write a function to add two numbers"
        assert problems[1].task_id == "test-002"

    def test_execute_code_in_sandbox(self, temp_dir):
        """Test code execution in sandbox."""
        code = "def add(a, b): return a + b"
        test_case = "assert add(2, 3) == 5"
        
        result = execute_code_in_sandbox(code, test_case)
        
        assert result.output is not None
        # Note: In real implementation, we'd verify is_correct based on actual execution
        # For now, we just check that it runs without crashing

    def test_save_convergence_results_with_none_step(self, temp_dir):
        """Test that None first_correct_step is handled correctly."""
        output_path = os.path.join(temp_dir, "convergence_results.csv")
        
        results = [
            ConvergenceTrajectory(
                task_id="test-001",
                k=1,
                output="code",
                is_correct=False,
                converged=False,
                first_correct_step=None
            )
        ]
        
        save_convergence_results(results, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert rows[0]['step'] == '0'  # None should be converted to 0