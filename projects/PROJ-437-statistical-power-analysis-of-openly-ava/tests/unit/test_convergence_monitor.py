"""
Unit tests for the Convergence Monitor.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from utils.convergence_monitor import ConvergenceMonitor


def test_convergence_monitor_no_issues():
    """Test that no issues are flagged when data is good."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "convergence_log.json"
        output_path = Path(tmpdir) / "report.md"

        # Create good data
        data = [
            {"iteration_id": 1, "converged": True, "max_iterations": 50, "tolerance": 1e-3},
            {"iteration_id": 2, "converged": True, "max_iterations": 80, "tolerance": 1e-3}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        monitor = ConvergenceMonitor(
            input_path=input_path,
            output_path=output_path,
            max_iterations_threshold=100,
            min_tolerance_threshold=1e-4
        )
        
        log_data = monitor.load_log()
        issues = monitor.analyze(log_data)

        assert len(issues) == 0


def test_convergence_monitor_excessive_iterations():
    """Test that excessive iterations are flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "convergence_log.json"
        output_path = Path(tmpdir) / "report.md"

        # Create data with high iteration count
        data = [
            {"iteration_id": 1, "converged": True, "max_iterations": 150, "tolerance": 1e-3}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        monitor = ConvergenceMonitor(
            input_path=input_path,
            output_path=output_path,
            max_iterations_threshold=100,
            min_tolerance_threshold=1e-4
        )
        
        log_data = monitor.load_log()
        issues = monitor.analyze(log_data)

        assert len(issues) == 1
        assert "Exceeded max iterations" in issues[0]["reason"]


def test_convergence_monitor_low_tolerance():
    """Test that low tolerance is flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "convergence_log.json"
        output_path = Path(tmpdir) / "report.md"

        # Create data with very low tolerance
        data = [
            {"iteration_id": 1, "converged": True, "max_iterations": 50, "tolerance": 1e-5}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        monitor = ConvergenceMonitor(
            input_path=input_path,
            output_path=output_path,
            max_iterations_threshold=100,
            min_tolerance_threshold=1e-4
        )
        
        log_data = monitor.load_log()
        issues = monitor.analyze(log_data)

        assert len(issues) == 1
        assert "Tolerance too tight/low" in issues[0]["reason"]


def test_convergence_monitor_file_not_found():
    """Test that FileNotFoundError is raised if log is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "nonexistent.json"
        output_path = Path(tmpdir) / "report.md"

        monitor = ConvergenceMonitor(
            input_path=input_path,
            output_path=output_path
        )

        with pytest.raises(FileNotFoundError):
            monitor.load_log()


def test_convergence_monitor_report_generation():
    """Test that the report file is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "convergence_log.json"
        output_path = Path(tmpdir) / "report.md"

        data = [
            {"iteration_id": 1, "converged": True, "max_iterations": 150, "tolerance": 1e-3}
        ]
        with open(input_path, 'w') as f:
            json.dump(data, f)

        monitor = ConvergenceMonitor(
            input_path=input_path,
            output_path=output_path
        )
        
        monitor.run()

        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
            assert "Convergence Monitor Report" in content
            assert "Exceeded max iterations" in content