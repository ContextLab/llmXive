"""
Unit tests for the solver profiler module.

Tests verify that:
1. Synthetic problem generation creates valid structures
2. Single trial execution handles success/failure cases
3. Results are saved correctly to CSV
4. Timeout handling works as expected
"""
import os
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import csv

from code.solver_profiler import (
    generate_synthetic_problem,
    run_single_trial,
    save_results,
    DEFAULT_NUM_TRIALS,
    DEFAULT_OUTPUT_PATH,
    TARGET_MAX_TIME_SECONDS
)
from code.config import SolverConfig
from code.symbolic_solver import TimeoutError

class TestGenerateSyntheticProblem:
    """Tests for synthetic problem generation."""
    
    def test_problem_structure(self):
        """Test that generated problem has correct structure and dimensions."""
        solver_config = SolverConfig()
        rng = np.random.default_rng(42)
        
        problem = generate_synthetic_problem(solver_config, rng)
        
        assert "num_vars" in problem
        assert "num_ineq" in problem
        assert "num_eq" in problem
        assert "G" in problem
        assert "h" in problem
        assert "A" in problem
        assert "b" in problem
        assert "c" in problem
        
        # Verify dimensions match
        assert problem["G"].shape[0] == problem["num_ineq"]
        assert problem["G"].shape[1] == problem["num_vars"]
        assert len(problem["h"]) == problem["num_ineq"]
        
        assert problem["A"].shape[0] == problem["num_eq"]
        assert problem["A"].shape[1] == problem["num_vars"]
        assert len(problem["b"]) == problem["num_eq"]
        
        assert len(problem["c"]) == problem["num_vars"]
    
    def test_variable_ranges(self):
        """Test that variable counts are within expected ranges."""
        solver_config = SolverConfig()
        rng = np.random.default_rng(42)
        
        for _ in range(10):
            problem = generate_synthetic_problem(solver_config, rng)
            
            assert 50 <= problem["num_vars"] <= 150
            assert 100 <= problem["num_ineq"] <= 300
            assert 10 <= problem["num_eq"] <= 50

class TestRunSingleTrial:
    """Tests for single trial execution."""
    
    @patch('code.symbolic_solver.SymbolicSolver.solve')
    def test_successful_trial(self, mock_solve):
        """Test a successful trial execution."""
        solver_config = SolverConfig()
        problem = {
            "num_vars": 100,
            "num_ineq": 200,
            "num_eq": 20,
            "G": np.random.randn(200, 100),
            "h": np.random.randn(200),
            "A": np.random.randn(20, 100),
            "b": np.random.randn(20),
            "c": np.random.randn(100)
        }
        
        mock_solve.return_value = {"status": "optimal", "x": np.zeros(100)}
        
        result = run_single_trial(
            trial_id=1,
            problem=problem,
            solver_config=solver_config,
            timeout_seconds=300.0,
            logger=MagicMock()
        )
        
        assert result["trial_id"] == 1
        assert result["success"] is True
        assert result["timed_out"] is False
        assert result["elapsed_time_seconds"] > 0
        assert result["error_message"] is None
    
    def test_timeout_handling(self):
        """Test that timeout is properly detected."""
        solver_config = SolverConfig()
        problem = {
            "num_vars": 100,
            "num_ineq": 200,
            "num_eq": 20,
            "G": np.random.randn(200, 100),
            "h": np.random.randn(200),
            "A": np.random.randn(20, 100),
            "b": np.random.randn(20),
            "c": np.random.randn(100)
        }
        
        # Simulate a timeout by raising TimeoutError
        with patch('code.symbolic_solver.SymbolicSolver.solve', side_effect=TimeoutError("Test timeout")):
            result = run_single_trial(
                trial_id=1,
                problem=problem,
                solver_config=solver_config,
                timeout_seconds=1.0,  # Very short timeout for test
                logger=MagicMock()
            )
            
            assert result["success"] is False
            assert result["timed_out"] is True
            assert "timeout" in result["error_message"].lower()

class TestSaveResults:
    """Tests for result saving functionality."""
    
    def test_save_results_creates_file(self):
        """Test that results are saved to a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.csv")
            
            results = [
                {
                    "trial_id": 1,
                    "num_vars": 100,
                    "num_constraints": 220,
                    "elapsed_time_seconds": 150.5,
                    "success": True,
                    "timed_out": False,
                    "error_message": None,
                    "timestamp": "2024-01-01 12:00:00"
                },
                {
                    "trial_id": 2,
                    "num_vars": 120,
                    "num_constraints": 250,
                    "elapsed_time_seconds": 180.3,
                    "success": True,
                    "timed_out": False,
                    "error_message": None,
                    "timestamp": "2024-01-01 12:01:00"
                }
            ]
            
            save_results(results, output_path, MagicMock())
            
            assert os.path.exists(output_path)
            
            # Verify CSV structure
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]["trial_id"] == "1"
                assert rows[0]["success"] == "True"
                assert float(rows[0]["elapsed_time_seconds"]) == 150.5

class TestConstants:
    """Tests for module constants."""
    
    def test_target_max_time(self):
        """Verify the target maximum time matches the requirement."""
        assert TARGET_MAX_TIME_SECONDS == 300.0
    
    def test_default_num_trials(self):
        """Verify default number of trials is reasonable."""
        assert DEFAULT_NUM_TRIALS >= 10
        assert DEFAULT_NUM_TRIALS <= 100