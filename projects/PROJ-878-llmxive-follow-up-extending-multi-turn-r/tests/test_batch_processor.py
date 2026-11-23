"""
Tests for batch processing logic in batch_processor.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import gc

from code.batch_processor import (
    stream_puzzles,
    process_batch,
    write_results,
    run_batched_execution,
    BatchConfig
)


class TestStreamPuzzles:
    """Tests for the stream_puzzles generator function."""
    
    def test_stream_valid_jsonl(self, tmp_path):
        """Test streaming from a valid JSONL file."""
        input_file = tmp_path / "test.jsonl"
        test_data = [
            {"instance_id": "1", "text": "test1"},
            {"instance_id": "2", "text": "test2"},
            {"instance_id": "3", "text": "test3"}
        ]
        
        with open(input_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        results = list(stream_puzzles(str(input_file)))
        
        assert len(results) == 3
        assert results[0]['instance_id'] == '1'
        assert results[1]['instance_id'] == '2'
        assert results[2]['instance_id'] == '3'
    
    def test_stream_handles_empty_lines(self, tmp_path):
        """Test that empty lines are skipped."""
        input_file = tmp_path / "test.jsonl"
        test_data = [
            {"instance_id": "1", "text": "test1"},
            "",
            {"instance_id": "2", "text": "test2"}
        ]
        
        with open(input_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        results = list(stream_puzzles(str(input_file)))
        
        assert len(results) == 2
    
    def test_stream_handles_invalid_json(self, tmp_path, caplog):
        """Test that invalid JSON lines are logged and skipped."""
        input_file = tmp_path / "test.jsonl"
        test_data = [
            {"instance_id": "1", "text": "test1"},
            "not valid json",
            {"instance_id": "2", "text": "test2"}
        ]
        
        with open(input_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        results = list(stream_puzzles(str(input_file)))
        
        assert len(results) == 2
        assert "Failed to parse" in caplog.text


class TestProcessBatch:
    """Tests for the process_batch function."""
    
    def test_process_batch_success(self):
        """Test successful batch processing."""
        batch = [
            {"instance_id": "1", "text": "test1"},
            {"instance_id": "2", "text": "test2"}
        ]
        
        mock_executor = Mock()
        mock_executor.execute.return_value = {
            "turns_to_converge": 5,
            "convergence_status": "success",
            "path_coverage": 0.95,
            "divergence_from_ground_truth": 0.1
        }
        
        config = BatchConfig()
        results = process_batch(batch, mock_executor, config)
        
        assert len(results) == 2
        assert results[0]['instance_id'] == '1'
        assert results[0]['turns_to_converge'] == 5
        assert results[1]['instance_id'] == '2'
        assert mock_executor.execute.call_count == 2
    
    def test_process_batch_handles_errors(self):
        """Test that errors during execution are handled gracefully."""
        batch = [
            {"instance_id": "1", "text": "test1"},
            {"instance_id": "2", "text": "test2"}
        ]
        
        def mock_execute(puzzle):
            if puzzle['instance_id'] == '1':
                return {
                    "turns_to_converge": 5,
                    "convergence_status": "success"
                }
            raise ValueError("Simulated error")
        
        mock_executor = Mock()
        mock_executor.execute.side_effect = mock_execute
        
        config = BatchConfig()
        results = process_batch(batch, mock_executor, config)
        
        assert len(results) == 2
        assert results[0]['convergence_status'] == 'success'
        assert results[1]['convergence_status'] == 'error'
        assert 'error_message' in results[1]


class TestWriteResults:
    """Tests for the write_results function."""
    
    def test_write_results_creates_file(self, tmp_path):
        """Test that write_results creates the output file."""
        output_file = tmp_path / "results.csv"
        results = [
            {"instance_id": "1", "value": 10},
            {"instance_id": "2", "value": 20}
        ]
        
        write_results(results, str(output_file))
        
        assert output_file.exists()
    
    def test_write_results_with_header(self, tmp_path):
        """Test that write_results writes headers on first write."""
        output_file = tmp_path / "results.csv"
        results = [
            {"instance_id": "1", "value": 10}
        ]
        
        write_results(results, str(output_file))
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert "instance_id" in content
        assert "value" in content
    
    def test_write_results_append_mode(self, tmp_path):
        """Test that append mode adds to existing file."""
        output_file = tmp_path / "results.csv"
        
        # First write
        results1 = [{"instance_id": "1", "value": 10}]
        write_results(results1, str(output_file))
        
        # Append
        results2 = [{"instance_id": "2", "value": 20}]
        write_results(results2, str(output_file), append=True)
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3  # header + 2 data rows


class TestRunBatchedExecution:
    """Tests for the run_batched_execution function."""
    
    @patch('code.batch_processor.ReflectiveMaskingExecutor')
    def test_run_batched_execution_end_to_end(self, mock_executor_class, tmp_path):
        """Test end-to-end batched execution."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.csv"
        
        # Create input data
        test_data = [
            {"instance_id": "1", "text": "test1"},
            {"instance_id": "2", "text": "test2"},
            {"instance_id": "3", "text": "test3"},
            {"instance_id": "4", "text": "test4"}
        ]
        with open(input_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        # Mock executor
        mock_executor_instance = Mock()
        mock_executor_instance.execute.return_value = {
            "turns_to_converge": 5,
            "convergence_status": "success",
            "path_coverage": 0.95,
            "divergence_from_ground_truth": 0.1
        }
        mock_executor_class.return_value = mock_executor_instance
        
        config = BatchConfig(batch_size=2, stream_input=True)
        
        def executor_factory():
            return Mock()
        
        summary = run_batched_execution(
            input_path=str(input_file),
            output_path=str(output_file),
            executor_factory=executor_factory,
            config=config
        )
        
        assert summary['total_puzzles'] == 4
        assert summary['processed_puzzles'] == 4
        assert summary['batch_size'] == 2
        assert output_file.exists()
    
    def test_run_batched_execution_handles_missing_input(self, tmp_path, caplog):
        """Test that missing input file is handled."""
        with pytest.raises(FileNotFoundError):
            run_batched_execution(
                input_path=str(tmp_path / "nonexistent.jsonl"),
                output_path=str(tmp_path / "output.csv"),
                executor_factory=lambda: Mock()
            )


class TestBatchConfig:
    """Tests for BatchConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = BatchConfig()
        
        assert config.batch_size == 10
        assert config.max_memory_mb is None
        assert config.stream_input is True
        assert config.output_path == "data/processed/execution_log.csv"
        assert config.checkpoint_interval == 50
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = BatchConfig(
            batch_size=20,
            max_memory_mb=4096,
            stream_input=False,
            output_path="custom/output.csv",
            checkpoint_interval=100
        )
        
        assert config.batch_size == 20
        assert config.max_memory_mb == 4096
        assert config.stream_input is False
        assert config.output_path == "custom/output.csv"
        assert config.checkpoint_interval == 100
