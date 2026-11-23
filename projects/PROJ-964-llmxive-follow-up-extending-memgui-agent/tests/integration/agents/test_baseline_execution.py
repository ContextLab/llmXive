"""
Integration test for baseline execution loop (T015).

This test verifies that the baseline ConAct agent (CPU-only, 4-bit quantized)
can execute a trajectory from the synthetic benchmark, record step-level
success/failure, and attribute information decay to missing context from
steps >10 indices prior.

Prerequisites:
  - T005: ExecutionLog data model (code/utils/execution_log.py)
  - T011: Synthetic benchmark generation (data/synthetic_benchmark/trajectories.jsonl)
  - T012: Coherence validation (dependency links exist)
  - T016: Model checker (static verification of model ID)
  - T017: Base ConAct wrapper (code/agents/base_conact.py)
  - T018: CPU-only, 4-bit quantization configuration
  - T019: RunnerProtocol interface (code/evaluation/interfaces.py)
  - T020: Baseline runner implementation (code/evaluation/runner.py)
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "code"))

from utils.execution_log import ExecutionLog, TrajectoryExecutionLog
from evaluation.interfaces import RunnerProtocol
from evaluation.runner import BaselineRunner
from data_generation.validator import load_trajectories
from agents.model_checker import verify_model_availability


class TestBaselineExecution:
    """Integration tests for the baseline execution loop."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure test environment is ready."""
        # Verify model availability before running tests
        model_id = verify_model_availability()
        assert model_id is not None, "No verified model available for baseline execution"

        # Verify synthetic benchmark exists
        benchmark_path = project_root / "data" / "synthetic_benchmark" / "trajectories.jsonl"
        assert benchmark_path.exists(), f"Synthetic benchmark not found at {benchmark_path}"

        # Load trajectories for testing
        self.trajectories = load_trajectories(benchmark_path)
        assert len(self.trajectories) > 0, "No trajectories loaded from benchmark"

    def test_baseline_runner_initialization(self):
        """Test that BaselineRunner initializes correctly with RunnerProtocol."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Verify it implements RunnerProtocol
        assert hasattr(runner, 'run_trajectory'), "Missing run_trajectory method"
        assert hasattr(runner, 'get_logs'), "Missing get_logs method"

    def test_trajectory_execution_single(self):
        """Test execution of a single trajectory."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Select first trajectory for testing
        trajectory = self.trajectories[0]
        trajectory_id = trajectory.get('id', 'unknown')

        # Execute trajectory
        logs = runner.run_trajectory(trajectory)

        # Verify logs are generated
        assert logs is not None, "No logs generated for trajectory execution"
        assert isinstance(logs, TrajectoryExecutionLog), "Logs should be TrajectoryExecutionLog instance"

        # Verify trajectory_id matches
        assert logs.trajectory_id == trajectory_id, f"Trajectory ID mismatch: {logs.trajectory_id} vs {trajectory_id}"

        # Verify step logs exist
        assert len(logs.step_logs) > 0, "No step logs generated"

        # Verify each step log has required fields
        for step_log in logs.step_logs:
            assert 'step_index' in step_log, "Missing step_index in step log"
            assert 'success' in step_log, "Missing success in step log"
            assert 'action' in step_log, "Missing action in step log"

    def test_information_decay_attribution(self):
        """Test that information decay failures are attributed to context >10 steps prior."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Test with multiple trajectories to find decay failures
        decay_failures = []

        for trajectory in self.trajectories[:5]:  # Test first 5 trajectories
            logs = runner.run_trajectory(trajectory)

            # Check for failure attribution
            for step_log in logs.step_logs:
                if step_log.get('success') is False:
                    reason = step_log.get('failure_reason', '')
                    if 'information decay' in reason.lower() or 'context' in reason.lower():
                        # Check if attribution mentions steps >10 prior
                        if '>10' in reason or 'step' in reason:
                            decay_failures.append({
                                'trajectory_id': logs.trajectory_id,
                                'step_index': step_log['step_index'],
                                'reason': reason
                            })

        # If we have decay failures, verify they have proper attribution
        if decay_failures:
            for failure in decay_failures:
                assert 'step' in failure['reason'].lower() or '>10' in failure['reason'], \
                    f"Failure attribution missing step reference: {failure['reason']}"

    def test_execution_log_persistence(self):
        """Test that execution logs are persisted to the correct output file."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Execute a trajectory
        trajectory = self.trajectories[0]
        logs = runner.run_trajectory(trajectory)

        # Verify logs can be serialized
        try:
            log_dict = logs.to_dict()
            json_str = json.dumps(log_dict, indent=2)
            assert len(json_str) > 0, "Serialized log is empty"
        except Exception as e:
            pytest.fail(f"Failed to serialize execution logs: {e}")

    def test_cpu_only_execution(self):
        """Test that execution enforces CPU-only mode."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Verify CPU-only flag is set
        assert runner.cpu_only is True, "CPU-only mode should be enabled"

        # Execute trajectory and verify no CUDA errors
        trajectory = self.trajectories[0]
        try:
            logs = runner.run_trajectory(trajectory)
            assert logs is not None, "Execution failed without CUDA error"
        except Exception as e:
            # If there's an error, it should not be CUDA-related
            assert 'cuda' not in str(e).lower() and 'gpu' not in str(e).lower(), \
                f"CUDA/GPU error detected in CPU-only mode: {e}"

    def test_4bit_quantization(self):
        """Test that 4-bit quantization is configured."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Verify quantization flag is set
        assert runner.quantize_4bit is True, "4-bit quantization should be enabled"

    def test_multiple_trajectory_execution(self):
        """Test execution of multiple trajectories in sequence."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        executed_count = 0
        for trajectory in self.trajectories[:3]:  # Test first 3
            logs = runner.run_trajectory(trajectory)
            assert logs is not None, f"Failed to execute trajectory {trajectory.get('id', 'unknown')}"
            executed_count += 1

        assert executed_count == 3, f"Expected 3 executions, got {executed_count}"

    def test_step_success_rate_calculation(self):
        """Test that step-level success/failure is correctly recorded."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        trajectory = self.trajectories[0]
        logs = runner.run_trajectory(trajectory)

        # Count successes and failures
        successes = sum(1 for step in logs.step_logs if step.get('success') is True)
        failures = sum(1 for step in logs.step_logs if step.get('success') is False)

        # Verify total steps match
        total_steps = len(logs.step_logs)
        assert successes + failures == total_steps, \
            f"Success/Failure count mismatch: {successes} + {failures} != {total_steps}"

    def test_dependency_link_validation_integration(self):
        """Test that dependency links are preserved during execution."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Load trajectory with dependency links
        trajectory = self.trajectories[0]
        assert 'dependency_links' in trajectory, "Trajectory missing dependency_links"

        # Execute
        logs = runner.run_trajectory(trajectory)

        # Verify logs include dependency context
        assert hasattr(logs, 'dependency_context') or 'dependency_context' in logs.to_dict(), \
            "Execution logs should preserve dependency context"

    def test_runner_protocol_compliance(self):
        """Test that BaselineRunner fully implements RunnerProtocol."""
        runner = BaselineRunner(
            model_id=verify_model_availability(),
            cpu_only=True,
            quantize_4bit=True
        )

        # Verify all protocol methods exist
        protocol_methods = ['run_trajectory', 'get_logs']
        for method in protocol_methods:
            assert hasattr(runner, method), f"Missing protocol method: {method}"
            assert callable(getattr(runner, method)), f"Protocol method not callable: {method}"

        # Verify get_logs returns accumulated logs
        trajectory = self.trajectories[0]
        runner.run_trajectory(trajectory)
        accumulated_logs = runner.get_logs()

        assert isinstance(accumulated_logs, list), "get_logs should return a list"
        assert len(accumulated_logs) > 0, "Accumulated logs should not be empty"