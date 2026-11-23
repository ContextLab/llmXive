"""
Unit tests for code/evaluation/benchmark.py.

These tests verify the correctness of the BenchmarkRunner class and its
methods, including error handling, trace loading, and metric calculation.
"""
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add the project root to the path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.benchmark import (
    BenchmarkError,
    BenchmarkRunner,
    main,
)
from config import get_config, reset_config


class TestBenchmarkError:
    """Tests for the BenchmarkError exception class."""

    def test_benchmark_error_instantiation(self):
        """Test that BenchmarkError can be instantiated with a message."""
        error = BenchmarkError("Test error message")
        assert str(error) == "Test error message"

    def test_benchmark_error_inherits_from_exception(self):
        """Test that BenchmarkError inherits from Exception."""
        assert issubclass(BenchmarkError, Exception)


class TestBenchmarkRunnerInit:
    """Tests for the BenchmarkRunner __init__ method."""

    def test_init_sets_attributes(self, tmp_path):
        """Test that __init__ correctly sets instance attributes."""
        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        assert runner.held_out_dir == str(tmp_path / "held_out")
        assert runner.rules_path == str(tmp_path / "rules.json")
        assert runner.output_dir == str(tmp_path / "output")
        assert runner.config == config

    def test_init_creates_output_directory(self, tmp_path):
        """Test that __init__ creates the output directory if it doesn't exist."""
        output_dir = tmp_path / "new_output_dir"
        assert not output_dir.exists()

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(output_dir),
            config=config,
        )

        assert output_dir.exists()
        assert output_dir.is_dir()


class TestBenchmarkRunnerLoadHeldOutTraces:
    """Tests for the BenchmarkRunner load_held_out_traces method."""

    def test_load_held_out_traces_success(self, tmp_path):
        """Test successful loading of held-out traces."""
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()

        # Create a valid trace file
        trace_data = {
            "trace_id": "test_trace_1",
            "tool_sequence": [{"tool": "edit", "args": {"x": 1}}],
            "final_state": {"slide": "A"},
        }
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        traces = runner.load_held_out_traces()

        assert len(traces) == 1
        assert traces[0]["trace_id"] == "test_trace_1"

    def test_load_held_out_traces_empty_directory(self, tmp_path):
        """Test that an empty held-out directory raises BenchmarkError."""
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.load_held_out_traces()

        assert "No trace files found" in str(exc_info.value)

    def test_load_held_out_traces_invalid_json(self, tmp_path):
        """Test that invalid JSON in a trace file raises BenchmarkError."""
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()

        # Create an invalid trace file
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            f.write("{ invalid json }")

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.load_held_out_traces()

        assert "Failed to parse trace file" in str(exc_info.value)

    def test_load_held_out_traces_missing_required_fields(self, tmp_path):
        """Test that missing required fields in a trace file raises BenchmarkError."""
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()

        # Create a trace file missing required fields
        trace_data = {"trace_id": "test_trace_1"}  # Missing tool_sequence and final_state
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.load_held_out_traces()

        assert "Missing required field" in str(exc_info.value)


class TestBenchmarkRunnerLoadRules:
    """Tests for the BenchmarkRunner load_rules method."""

    def test_load_rules_success(self, tmp_path):
        """Test successful loading of rules."""
        rules_path = tmp_path / "rules.json"
        rules_data = {
            "rules": [
                {"condition": "x > 0", "action": "edit"},
                {"condition": "x <= 0", "action": "delete"},
            ]
        }
        with open(rules_path, "w") as f:
            json.dump(rules_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(rules_path),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        rules = runner.load_rules()

        assert len(rules) == 2
        assert rules[0]["condition"] == "x > 0"

    def test_load_rules_file_not_found(self, tmp_path):
        """Test that missing rules file raises BenchmarkError."""
        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "nonexistent_rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.load_rules()

        assert "Rules file not found" in str(exc_info.value)

    def test_load_rules_invalid_json(self, tmp_path):
        """Test that invalid JSON in rules file raises BenchmarkError."""
        rules_path = tmp_path / "rules.json"
        with open(rules_path, "w") as f:
            f.write("{ invalid json }")

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(rules_path),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.load_rules()

        assert "Failed to parse rules file" in str(exc_info.value)

    def test_load_rules_empty_rules(self, tmp_path):
        """Test that empty rules list raises BenchmarkError."""
        rules_path = tmp_path / "rules.json"
        rules_data = {"rules": []}
        with open(rules_path, "w") as f:
            json.dump(rules_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(rules_path),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.load_rules()

        assert "No rules loaded" in str(exc_info.value)


class TestBenchmarkRunnerRunBaselineAgent:
    """Tests for the BenchmarkRunner run_baseline_agent method."""

    @patch("agents.baseline.BaselineAgent")
    def test_run_baseline_agent_success(self, mock_baseline_agent_class, tmp_path):
        """Test successful execution of the baseline agent."""
        # Setup mock
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = {
            "success": True,
            "edit_accuracy": 0.95,
            "latency": 0.123,
        }
        mock_baseline_agent_class.return_value = mock_agent_instance

        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        trace_data = {
            "trace_id": "test_trace_1",
            "tool_sequence": [{"tool": "edit", "args": {"x": 1}}],
            "final_state": {"slide": "A"},
        }
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        result = runner.run_baseline_agent(trace_data)

        assert result["success"] is True
        assert result["edit_accuracy"] == 0.95
        assert result["latency"] == 0.123
        mock_agent_instance.run.assert_called_once_with(trace_data)

    @patch("agents.baseline.BaselineAgent")
    def test_run_baseline_agent_failure(self, mock_baseline_agent_class, tmp_path):
        """Test that agent failure is handled correctly."""
        # Setup mock to raise an exception
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.side_effect = Exception("Agent failed")
        mock_baseline_agent_class.return_value = mock_agent_instance

        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        trace_data = {
            "trace_id": "test_trace_1",
            "tool_sequence": [{"tool": "edit", "args": {"x": 1}}],
            "final_state": {"slide": "A"},
        }
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        result = runner.run_baseline_agent(trace_data)

        assert result["success"] is False
        assert "Agent failed" in result["error"]


class TestBenchmarkRunnerRunCompressedAgent:
    """Tests for the BenchmarkRunner run_compressed_agent method."""

    @patch("agents.compressed.CompressedAgent")
    def test_run_compressed_agent_success(self, mock_compressed_agent_class, tmp_path):
        """Test successful execution of the compressed agent."""
        # Setup mock
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = {
            "success": True,
            "edit_accuracy": 0.92,
            "latency": 0.085,
        }
        mock_compressed_agent_class.return_value = mock_agent_instance

        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        trace_data = {
            "trace_id": "test_trace_1",
            "tool_sequence": [{"tool": "edit", "args": {"x": 1}}],
            "final_state": {"slide": "A"},
        }
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        rules_data = {"rules": [{"condition": "x > 0", "action": "edit"}]}
        rules_path = tmp_path / "rules.json"
        with open(rules_path, "w") as f:
            json.dump(rules_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(rules_path),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        result = runner.run_compressed_agent(trace_data)

        assert result["success"] is True
        assert result["edit_accuracy"] == 0.92
        assert result["latency"] == 0.085
        mock_agent_instance.run.assert_called_once_with(trace_data)

    @patch("agents.compressed.CompressedAgent")
    def test_run_compressed_agent_failure(self, mock_compressed_agent_class, tmp_path):
        """Test that agent failure is handled correctly."""
        # Setup mock to raise an exception
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.side_effect = Exception("Compressed agent failed")
        mock_compressed_agent_class.return_value = mock_agent_instance

        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        trace_data = {
            "trace_id": "test_trace_1",
            "tool_sequence": [{"tool": "edit", "args": {"x": 1}}],
            "final_state": {"slide": "A"},
        }
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        rules_data = {"rules": [{"condition": "x > 0", "action": "edit"}]}
        rules_path = tmp_path / "rules.json"
        with open(rules_path, "w") as f:
            json.dump(rules_data, f)

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(held_out_dir),
            rules_path=str(rules_path),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        result = runner.run_compressed_agent(trace_data)

        assert result["success"] is False
        assert "Compressed agent failed" in result["error"]


class TestBenchmarkRunnerSaveResults:
    """Tests for the BenchmarkRunner save_results method."""

    def test_save_results_creates_file(self, tmp_path):
        """Test that save_results correctly writes results to a file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        results = [
            {
                "trace_id": "test_trace_1",
                "baseline": {"success": True, "edit_accuracy": 0.95, "latency": 0.123},
                "compressed": {"success": True, "edit_accuracy": 0.92, "latency": 0.085},
            }
        ]

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(output_dir),
            config=config,
        )

        output_file = runner.save_results(results)

        assert output_file.exists()
        with open(output_file, "r") as f:
            saved_results = json.load(f)

        assert len(saved_results) == 1
        assert saved_results[0]["trace_id"] == "test_trace_1"
        assert saved_results[0]["baseline"]["edit_accuracy"] == 0.95

    def test_save_results_creates_directory_if_needed(self, tmp_path):
        """Test that save_results creates the output directory if it doesn't exist."""
        output_dir = tmp_path / "output" / "nested"
        assert not output_dir.exists()

        results = [{"trace_id": "test_trace_1", "baseline": {}, "compressed": {}}]

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(output_dir),
            config=config,
        )

        output_file = runner.save_results(results)

        assert output_dir.exists()
        assert output_file.exists()


class TestBenchmarkRunnerRunBenchmark:
    """Tests for the BenchmarkRunner run_benchmark method."""

    @patch.object(BenchmarkRunner, "load_held_out_traces")
    @patch.object(BenchmarkRunner, "load_rules")
    @patch.object(BenchmarkRunner, "run_baseline_agent")
    @patch.object(BenchmarkRunner, "run_compressed_agent")
    @patch.object(BenchmarkRunner, "save_results")
    def test_run_benchmark_success(
        self,
        mock_save_results,
        mock_run_compressed,
        mock_run_baseline,
        mock_load_rules,
        mock_load_traces,
        tmp_path,
    ):
        """Test successful execution of the full benchmark pipeline."""
        # Setup mocks
        mock_load_traces.return_value = [
            {
                "trace_id": "trace_1",
                "tool_sequence": [{"tool": "edit", "args": {"x": 1}}],
                "final_state": {"slide": "A"},
            }
        ]
        mock_load_rules.return_value = [{"condition": "x > 0", "action": "edit"}]
        mock_run_baseline.return_value = {
            "success": True,
            "edit_accuracy": 0.95,
            "latency": 0.123,
        }
        mock_run_compressed.return_value = {
            "success": True,
            "edit_accuracy": 0.92,
            "latency": 0.085,
        }
        mock_save_results.return_value = tmp_path / "output" / "results.json"

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        results = runner.run_benchmark()

        assert len(results) == 1
        assert results[0]["trace_id"] == "trace_1"
        assert results[0]["baseline"]["edit_accuracy"] == 0.95
        assert results[0]["compressed"]["edit_accuracy"] == 0.92

        mock_load_traces.assert_called_once()
        mock_load_rules.assert_called_once()
        assert mock_run_baseline.call_count == 1
        assert mock_run_compressed.call_count == 1
        mock_save_results.assert_called_once()

    @patch.object(BenchmarkRunner, "load_held_out_traces")
    @patch.object(BenchmarkRunner, "load_rules")
    def test_run_benchmark_load_traces_failure(
        self, mock_load_rules, mock_load_traces, tmp_path
    ):
        """Test that load_traces failure raises BenchmarkError."""
        mock_load_traces.side_effect = BenchmarkError("Failed to load traces")

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.run_benchmark()

        assert "Failed to load traces" in str(exc_info.value)

    @patch.object(BenchmarkRunner, "load_held_out_traces")
    @patch.object(BenchmarkRunner, "load_rules")
    def test_run_benchmark_load_rules_failure(
        self, mock_load_rules, mock_load_traces, tmp_path
    ):
        """Test that load_rules failure raises BenchmarkError."""
        mock_load_traces.return_value = [{"trace_id": "test"}]
        mock_load_rules.side_effect = BenchmarkError("Failed to load rules")

        config = get_config()
        runner = BenchmarkRunner(
            held_out_dir=str(tmp_path / "held_out"),
            rules_path=str(tmp_path / "rules.json"),
            output_dir=str(tmp_path / "output"),
            config=config,
        )

        with pytest.raises(BenchmarkError) as exc_info:
            runner.run_benchmark()

        assert "Failed to load rules" in str(exc_info.value)


class TestMain:
    """Tests for the main function."""

    @patch("evaluation.benchmark.BenchmarkRunner")
    @patch("evaluation.benchmark.get_config")
    def test_main_success(self, mock_get_config, mock_benchmark_runner_class, tmp_path):
        """Test successful execution of the main function."""
        # Setup mocks
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_benchmark.return_value = [
            {"trace_id": "test", "baseline": {}, "compressed": {}}
        ]
        mock_runner_instance.save_results.return_value = tmp_path / "results.json"
        mock_benchmark_runner_class.return_value = mock_runner_instance

        # Create necessary directories
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create dummy files
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump({"trace_id": "test"}, f)

        rules_file = rules_dir / "rules.json"
        with open(rules_file, "w") as f:
            json.dump({"rules": []}, f)

        # Run main
        main(str(held_out_dir), str(rules_file), str(output_dir))

        # Verify calls
        mock_get_config.assert_called_once()
        mock_benchmark_runner_class.assert_called_once()
        mock_runner_instance.run_benchmark.assert_called_once()
        mock_runner_instance.save_results.assert_called_once()

    @patch("evaluation.benchmark.BenchmarkRunner")
    @patch("evaluation.benchmark.get_config")
    def test_main_benchmark_error(self, mock_get_config, mock_benchmark_runner_class, tmp_path):
        """Test that BenchmarkError in main is handled correctly."""
        # Setup mocks
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_benchmark.side_effect = BenchmarkError("Benchmark failed")
        mock_benchmark_runner_class.return_value = mock_runner_instance

        # Create necessary directories
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create dummy files
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump({"trace_id": "test"}, f)

        rules_file = rules_dir / "rules.json"
        with open(rules_file, "w") as f:
            json.dump({"rules": []}, f)

        # Run main and expect exit
        with pytest.raises(SystemExit) as exc_info:
            main(str(held_out_dir), str(rules_file), str(output_dir))

        assert exc_info.value.code == 1

    @patch("evaluation.benchmark.BenchmarkRunner")
    @patch("evaluation.benchmark.get_config")
    def test_main_general_exception(self, mock_get_config, mock_benchmark_runner_class, tmp_path):
        """Test that general exceptions in main are handled correctly."""
        # Setup mocks
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_benchmark.side_effect = RuntimeError("Unexpected error")
        mock_benchmark_runner_class.return_value = mock_runner_instance

        # Create necessary directories
        held_out_dir = tmp_path / "held_out"
        held_out_dir.mkdir()
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create dummy files
        trace_file = held_out_dir / "trace_1.json"
        with open(trace_file, "w") as f:
            json.dump({"trace_id": "test"}, f)

        rules_file = rules_dir / "rules.json"
        with open(rules_file, "w") as f:
            json.dump({"rules": []}, f)

        # Run main and expect exit
        with pytest.raises(SystemExit) as exc_info:
            main(str(held_out_dir), str(rules_file), str(output_dir))

        assert exc_info.value.code == 1