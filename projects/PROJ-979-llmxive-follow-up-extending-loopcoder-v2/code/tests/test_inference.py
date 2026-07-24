import os
import sys
import json
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from inference import write_convergence_results, run_refinement_loop, detect_convergence
from models import ConvergenceStatus, ConvergenceTrajectory, InputProblem

@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    import shutil
    shutil.rmtree(tmp)

class TestConvergenceLogger:
    def test_write_convergence_results_creates_csv(self, temp_dir):
        """Test that write_convergence_results creates the CSV with correct columns."""
        output_path = os.path.join(temp_dir, "convergence_results.csv")
        
        # Create mock trajectories
        traj1 = ConvergenceTrajectory(
            task_id="task_1",
            steps=[{"k": 1, "code": "print(1)", "status": ConvergenceStatus.FAILED}],
            k_correct=None,
            status=ConvergenceStatus.FAILED
        )
        traj2 = ConvergenceTrajectory(
            task_id="task_2",
            steps=[{"k": 1, "code": "print(2)", "status": ConvergenceStatus.CONVERGED}],
            k_correct=1,
            status=ConvergenceStatus.CONVERGED
        )
        
        write_convergence_results([traj1, traj2], output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Check header
        assert rows[0] == ['task_id', 'k_correct', 'trajectory_status']
        
        # Check data
        assert len(rows) == 3 # Header + 2 rows
        assert rows[1][0] == 'task_1'
        assert rows[1][1] == 'None'
        assert rows[1][2] == 'FAILED'
        
        assert rows[2][0] == 'task_2'
        assert rows[2][1] == '1'
        assert rows[2][2] == 'CONVERGED'

    def test_write_convergence_results_empty_list(self, temp_dir):
        """Test handling of empty trajectory list."""
        output_path = os.path.join(temp_dir, "empty_results.csv")
        write_convergence_results([], output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert rows[0] == ['task_id', 'k_correct', 'trajectory_status']
        assert len(rows) == 1

    def test_write_convergence_results_directory_creation(self, temp_dir):
        """Test that the function creates parent directories if they don't exist."""
        nested_path = os.path.join(temp_dir, "subdir", "nested", "results.csv")
        
        traj = ConvergenceTrajectory(
            task_id="task_1",
            steps=[],
            k_correct=None,
            status=ConvergenceStatus.FAILED
        )
        
        write_convergence_results([traj], nested_path)
        
        assert os.path.exists(nested_path)

class TestRefinementLoop:
    @patch('inference.generate_solution')
    @patch('inference.execute_code_in_sandbox')
    def test_run_refinement_loop_converges_early(self, mock_exec, mock_gen, temp_dir):
        """Test that the loop stops as soon as a solution is found."""
        mock_gen.side_effect = ["bad_code_1", "good_code_2"]
        mock_exec.side_effect = [(False, "error1"), (True, None)]
        
        traj = run_refinement_loop("prompt", "test", None, None, max_k=3)
        
        assert traj.status == ConvergenceStatus.CONVERGED
        assert traj.k_correct == 2
        assert len(traj.steps) == 2 # Should stop after k=2

    @patch('inference.generate_solution')
    @patch('inference.execute_code_in_sandbox')
    def test_run_refinement_loop_fails_all(self, mock_exec, mock_gen, temp_dir):
        """Test behavior when no solution is found within max_k."""
        mock_gen.side_effect = ["bad_1", "bad_2", "bad_3"]
        mock_exec.side_effect = [(False, "e1"), (False, "e2"), (False, "e3")]
        
        traj = run_refinement_loop("prompt", "test", None, None, max_k=3)
        
        assert traj.status == ConvergenceStatus.FAILED
        assert traj.k_correct is None
        assert len(traj.steps) == 3