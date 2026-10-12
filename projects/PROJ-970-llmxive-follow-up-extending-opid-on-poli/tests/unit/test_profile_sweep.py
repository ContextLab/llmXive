"""
Unit test for the profiling script.

The test ensures that the ``profile_sweep`` module can be imported and that
calling its ``main`` function completes without raising an exception when
the experiment runner is configured to execute a minimal number of episodes.
To keep the test fast, we monkey‑patch ``verify_feasibility`` to return a
small episode count and mock the heavy ``ExperimentRunner.run_sweep`` method.
"""

import builtins
from unittest import mock

import pytest

# Import the module under test
from profiling import profile_sweep


@mock.patch("config.verify_feasibility")
@mock.patch("experiments.runner.ExperimentRunner")
@mock.patch("llmxive_toolkit.get_logger")
def test_main_runs_fast(mock_logger, mock_runner_cls, mock_feasibility):
    # Arrange: make feasibility return a tiny episode count
    mock_feasibility.return_value = (5, 0.0)

    # Mock the ExperimentRunner instance and its run_sweep method
    mock_runner = mock.Mock()
    mock_runner.run_sweep.return_value = None
    mock_runner_cls.return_value = mock_runner

    # Act: run the profiling main function
    profile_sweep.main()

    # Assert: verify that the runner was instantiated with the mocked episode count
    mock_runner_cls.assert_called_once_with(episodes_per_setting=5)
    assert mock_runner.run_sweep.called, "run_sweep should be invoked"

    # Ensure a profiling file was created (the path is deterministic)
    profile_path = profile_sweep.paths.results("profile.txt")
    assert profile_path.exists(), f"Expected profiling output at {profile_path}"
    # Clean up the generated file
    profile_path.unlink()


def test_profile_file_content():
    """
    Verify that the profiling output file contains the expected keys.
    This test reads the file written by the previous test (if it exists)
    and checks for the presence of ``elapsed_seconds`` and ``estimated_hours``.
    """
    profile_path = profile_sweep.paths.results("profile.txt")
    if not profile_path.exists():
        pytest.skip("Profiling file not generated; previous test may have failed.")

    content = profile_path.read_text()
    assert "elapsed_seconds:" in content
    assert "estimated_hours:" in content