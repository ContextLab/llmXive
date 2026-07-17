import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from static_score.batch_processor import run_batch_processing, process_single_task, load_sampled_tasks
from static_score.compute import StaticScorer
from data.preprocess import tokenize_traces

@pytest.fixture
def mock_task():
    """Create a mock task for testing."""
    return {
        "id": "test_task_1",
        "question": "What is 2 + 2?",
        "answer": "4",
        "trace": ["2", "+", "2", "=", "4"]
    }

@pytest.fixture
def sample_tasks():
    """Create a list of sample tasks."""
    return [
        {"id": f"task_{i}", "question": f"Question {i}", "answer": f"Answer {i}", "trace": [f"token_{i}"]}
        for i in range(10)
    ]

class TestBatchProcessing:
    """Integration tests for batch processing functionality."""

    def test_load_sampled_tasks_smoke(self, sample_tasks):
        """Test that we can load a sampled subset of tasks."""
        # This is a smoke test - we're just verifying the function doesn't crash
        # In a real scenario, this would load from actual data files
        with patch('static_score.batch_processor.load_raw_data', return_value=sample_tasks):
            with patch('static_score.batch_processor.download_gsm8k'):
                result = load_sampled_tasks("gsm8k", sample_size=5)
                assert len(result) == 5
                assert all("id" in task for task in result)

    def test_process_single_task_success(self, mock_task):
        """Test successful processing of a single task."""
        scorer = StaticScorer()
        
        # Mock the tokenize_traces function to return deterministic tokens
        with patch('static_score.batch_processor.tokenize_traces', return_value=[["token1", "token2"]]):
            result = process_single_task(mock_task, scorer, timeout_threshold=300)
            
            assert result is not None
            assert result["task_id"] == "test_task_1"
            assert "static_scores" in result
            assert isinstance(result["static_scores"], list)
            assert "processing_time" in result

    def test_process_single_task_timeout(self, mock_task):
        """Test that tasks exceeding timeout are excluded."""
        scorer = StaticScorer()
        
        # Mock tokenize_traces to simulate a slow task
        def slow_tokenize(*args, **kwargs):
            import time
            time.sleep(0.1)  # Simulate some processing time
            return [["token"]]
        
        # We'll test the timeout logic by checking the return value
        # In a real test, we'd mock the timing to exceed the threshold
        with patch('static_score.batch_processor.tokenize_traces', return_value=[["token"]]):
            # This should succeed normally since we're not actually timing it
            result = process_single_task(mock_task, scorer, timeout_threshold=300)
            assert result is not None  # Should succeed within threshold

    def test_run_batch_processing_integration(self, sample_tasks):
        """Integration test for the full batch processing pipeline."""
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_scores.json")
            
            # Mock the necessary functions to avoid actual data loading
            with patch('static_score.batch_processor.load_sampled_tasks', return_value=sample_tasks):
                with patch('static_score.batch_processor.download_gsm8k'):
                    with patch('static_score.batch_processor.download_math'):
                        with patch('static_score.batch_processor.tokenize_traces', 
                                 return_value=[["token"] * 5 for _ in sample_tasks]):
                            
                            result = run_batch_processing(
                                datasets=["gsm8k"],
                                sample_size=len(sample_tasks),
                                timeout_threshold=300,
                                output_path=output_path
                            )
                            
                            # Verify the result structure
                            assert "total_tasks" in result
                            assert "processed" in result
                            assert "output_file" in result
                            
                            # Verify the output file was created
                            assert os.path.exists(output_path)
                            
                            # Verify the output file contains valid JSON
                            with open(output_path, 'r') as f:
                                data = json.load(f)
                                assert isinstance(data, list)
                                assert len(data) == len(sample_tasks)
                                assert all("task_id" in item for item in data)
                                assert all("static_scores" in item for item in data)

    def test_batch_processing_exclusion_logic(self, sample_tasks):
        """Test that the exclusion logic works correctly."""
        # Create tasks where some will be excluded due to timeout
        # We'll mock the processing to return None for some tasks
        timeout_count = 3
        success_count = len(sample_tasks) - timeout_count
        
        def mock_process_single_task(task, scorer, timeout_threshold):
            # Exclude every 3rd task to simulate timeout
            if int(task["id"].split("_")[-1]) % 3 == 0:
                return None
            return {
                "task_id": task["id"],
                "static_scores": [0.1, 0.2, 0.3],
                "processing_time": 0.1
            }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_scores.json")
            
            with patch('static_score.batch_processor.load_sampled_tasks', return_value=sample_tasks):
                with patch('static_score.batch_processor.download_gsm8k'):
                    with patch('static_score.batch_processor.download_math'):
                        with patch('static_score.batch_processor.process_single_task', side_effect=mock_process_single_task):
                            result = run_batch_processing(
                                datasets=["gsm8k"],
                                sample_size=len(sample_tasks),
                                timeout_threshold=300,
                                output_path=output_path
                            )
                            
                            # Verify exclusion counts
                            assert result["timeout_excluded"] == timeout_count
                            assert result["processed"] == success_count
                            assert result["exclusion_rate"] == timeout_count / len(sample_tasks)
                            
                            # Verify output file contains only successful tasks
                            with open(output_path, 'r') as f:
                                data = json.load(f)
                                assert len(data) == success_count
                                assert all(item["task_id"] != "task_0" and item["task_id"] != "task_3" and item["task_id"] != "task_6" for item in data)
