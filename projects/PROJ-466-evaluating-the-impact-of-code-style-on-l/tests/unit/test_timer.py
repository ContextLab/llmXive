"""
Unit tests for the timing module (T044a).
"""
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from performance.timer import (
    get_task_subset,
    run_timed_subset_pipeline,
    write_timing_log,
    run_timing_pipeline
)

class TestGetTaskSubset:
    """Tests for task subset selection."""

    def test_subset_smaller_than_total(self):
        """Test that subset is smaller than total when requested."""
        tasks = [{'task_id': f'task_{i}'} for i in range(10)]
        subset = get_task_subset(tasks, 5)
        
        assert len(subset) == 5
        assert subset[0]['task_id'] == 'task_0'
        assert subset[-1]['task_id'] == 'task_4'

    def test_subset_larger_than_total(self):
        """Test that subset returns all tasks when requested size is larger."""
        tasks = [{'task_id': f'task_{i}'} for i in range(3)]
        subset = get_task_subset(tasks, 10)
        
        assert len(subset) == 3

    def test_empty_tasks(self):
        """Test with empty task list."""
        subset = get_task_subset([], 5)
        assert len(subset) == 0

class TestWriteTimingLog:
    """Tests for timing log writing."""

    def test_log_file_created(self, tmp_path):
        """Test that log file is created with correct content."""
        log_path = tmp_path / "test_timing.log"
        results = {
            'total_duration_seconds': 10.5,
            'tasks_processed': 5,
            'start_time': '2024-01-01T00:00:00',
            'end_time': '2024-01-01T00:00:10',
            'status': 'completed'
        }
        
        write_timing_log(results, log_path)
        
        assert log_path.exists()
        
        content = log_path.read_text()
        assert 'Total Duration: 10.50 seconds' in content
        assert 'Tasks Processed: 5' in content
        assert 'Status: completed' in content

    def test_log_creates_directory(self, tmp_path):
        """Test that log creates parent directories if they don't exist."""
        log_path = tmp_path / "deep" / "nested" / "timing.log"
        results = {
            'total_duration_seconds': 1.0,
            'tasks_processed': 1,
            'start_time': '2024-01-01',
            'status': 'completed'
        }
        
        write_timing_log(results, log_path)
        
        assert log_path.exists()
        assert log_path.parent.exists()

class TestRunTimedSubsetPipeline:
    """Tests for the timed pipeline execution."""

    @patch('performance.timer.get_humaneval_tasks')
    def test_pipeline_runs_successfully(self, mock_get_tasks):
        """Test that pipeline runs and returns correct structure."""
        mock_tasks = [{'task_id': 'task_0'}, {'task_id': 'task_1'}]
        mock_get_tasks.return_value = mock_tasks
        
        config = {}
        results = run_timed_subset_pipeline(config, subset_size=2)
        
        assert 'total_duration_seconds' in results
        assert 'tasks_processed' in results
        assert 'status' in results
        assert results['status'] == 'completed'
        assert results['tasks_processed'] == 2
        assert results['total_duration_seconds'] >= 0

    @patch('performance.timer.get_humaneval_tasks')
    def test_pipeline_handles_empty_dataset(self, mock_get_tasks):
        """Test that pipeline fails gracefully with empty dataset."""
        mock_get_tasks.return_value = []
        
        config = {}
        
        with pytest.raises(ValueError, match="No tasks found"):
            run_timed_subset_pipeline(config, subset_size=1)

    @patch('performance.timer.get_humaneval_tasks')
    def test_pipeline_timing_accuracy(self, mock_get_tasks):
        """Test that timing is reasonably accurate."""
        mock_tasks = [{'task_id': 'task_0'}]
        mock_get_tasks.return_value = mock_tasks
        
        config = {}
        
        # Measure actual time
        start = time.time()
        results = run_timed_subset_pipeline(config, subset_size=1)
        end = time.time()
        
        actual_duration = end - start
        reported_duration = results['total_duration_seconds']
        
        # Reported time should be close to actual time (within 1 second for small tasks)
        assert abs(reported_duration - actual_duration) < 1.0

class TestRunTimingPipeline:
    """Tests for the main timing pipeline function."""

    @patch('performance.timer.load_config')
    @patch('performance.timer.run_timed_subset_pipeline')
    @patch('performance.timer.write_timing_log')
    def test_full_pipeline_integration(self, mock_write, mock_run, mock_load):
        """Test full pipeline integration."""
        mock_load.return_value = {}
        mock_run.return_value = {
            'total_duration_seconds': 5.0,
            'tasks_processed': 3,
            'status': 'completed',
            'start_time': '2024-01-01',
            'end_time': '2024-01-01'
        }
        
        results = run_timing_pipeline(subset_size=3, log_path='/tmp/test.log')
        
        assert results['status'] == 'completed'
        assert results['tasks_processed'] == 3
        mock_load.assert_called_once()
        mock_run.assert_called_once()
        mock_write.assert_called_once()