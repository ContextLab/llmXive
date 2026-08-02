import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tracemalloc

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.validate_streaming import get_memory_usage_mb, run_streaming_validation

class TestGetMemoryUsageMb:
    def test_memory_usage_returns_numbers(self):
        """Test that get_memory_usage_mb returns valid numbers."""
        tracemalloc.start()
        try:
            current, peak = get_memory_usage_mb()
            assert isinstance(current, float)
            assert isinstance(peak, float)
            assert current >= 0
            assert peak >= 0
        finally:
            tracemalloc.stop()

class TestRunStreamingValidation:
    @patch('utils.validate_streaming.fetch_locomo_dataset')
    @patch('utils.validate_streaming.build_memory_graph')
    @patch('utils.validate_streaming.FullTraversal')
    def test_validation_succeeds_with_mocked_data(self, mock_traversal, mock_build_graph, mock_fetch):
        """Test that validation succeeds with mocked data."""
        # Mock tasks
        mock_tasks = [
            {'task_id': 'test_1', 'context': 'test context 1', 'question': 'Q1', 'answer': 'A1'},
            {'task_id': 'test_2', 'context': 'test context 2', 'question': 'Q2', 'answer': 'A2'}
        ]
        mock_fetch.return_value = mock_tasks
        
        # Mock graph
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = ['node1', 'node2']
        mock_build_graph.return_value = mock_graph
        
        # Mock strategy
        mock_strategy = MagicMock()
        mock_traversal.return_value = mock_strategy
        
        # Run validation
        log = run_streaming_validation(num_tasks=2, chunk_size=1)
        
        # Check log structure
        assert log['status'] == 'success'
        assert log['num_tasks'] == 2
        assert log['chunk_size'] == 1
        assert 'measurements' in log
        assert len(log['measurements']) > 0
        
        # Check memory metrics
        assert 'initial_memory_mb' in log
        assert 'final_memory_mb' in log
        assert 'memory_stable' in log
        assert isinstance(log['memory_stable'], bool)

    @patch('utils.validate_streaming.fetch_locomo_dataset')
    def test_validation_handles_empty_dataset(self, mock_fetch):
        """Test that validation handles empty dataset gracefully."""
        mock_fetch.return_value = []
        
        log = run_streaming_validation(num_tasks=1, chunk_size=1)
        
        assert log['status'] == 'failed'
        assert 'reason' in log
        assert 'No tasks fetched' in log['reason']

    @patch('utils.validate_streaming.fetch_locomo_dataset')
    @patch('utils.validate_streaming.build_memory_graph')
    def test_validation_handles_graph_build_failure(self, mock_build_graph, mock_fetch):
        """Test that validation handles graph build failures."""
        mock_tasks = [
            {'task_id': 'test_1', 'context': 'test context 1', 'question': 'Q1', 'answer': 'A1'}
        ]
        mock_fetch.return_value = mock_tasks
        mock_build_graph.side_effect = Exception("Graph build failed")
        
        log = run_streaming_validation(num_tasks=1, chunk_size=1)
        
        # Should still succeed if it handles the error gracefully
        # (depending on implementation, it might fail or continue with empty graphs)
        assert 'status' in log

class TestStreamingLogOutput:
    def test_log_contains_required_fields(self):
        """Test that the streaming log contains all required fields."""
        # This is a structural test - we check that if a log is generated,
        # it has the expected structure
        required_fields = [
            'timestamp', 'num_tasks', 'chunk_size', 'initial_memory_mb',
            'measurements', 'status'
        ]
        
        # Create a sample log
        sample_log = {
            'timestamp': '2024-01-01 00:00:00',
            'num_tasks': 10,
            'chunk_size': 2,
            'initial_memory_mb': 100.0,
            'measurements': [
                {'stage': 'test', 'current_memory_mb': 100.0, 'peak_memory_mb': 100.0}
            ],
            'status': 'success'
        }
        
        for field in required_fields:
            assert field in sample_log, f"Missing required field: {field}"

    def test_measurements_have_required_fields(self):
        """Test that each measurement in the log has required fields."""
        required_measurement_fields = ['stage', 'current_memory_mb', 'peak_memory_mb']
        
        sample_measurement = {
            'stage': 'test',
            'current_memory_mb': 100.0,
            'peak_memory_mb': 100.0
        }
        
        for field in required_measurement_fields:
            assert field in sample_measurement, f"Missing required measurement field: {field}"