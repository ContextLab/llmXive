"""
Integration test for batch processing loop (T017).

This test verifies that:
1. Exactly 100 tasks are processed
2. Output file is created at data/processed/static_scores.json
3. Output structure matches the expected schema
4. Timeout and exclusion logic works correctly
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from static_score.batch_processor import (
    load_sampled_tasks,
    process_single_task,
    run_batch_processing,
    save_results,
    main,
    TARGET_TASK_COUNT,
    MAX_EXCLUSION_RATE
)
from static_score.compute import StaticScorer
from utils.config import Config, get_config, reset_config


@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary config for testing."""
    config = Config(
        data_dir=str(tmp_path),
        model_path="microsoft/phi-2",
        device="cpu",
        epsilon_smoothing=1e-9,
        seed=42
    )
    with patch('utils.config.get_config', return_value=config):
        with patch('utils.config.reset_config'):
            yield config


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    return [
        {
            "task_id": f"task_{i:04d}",
            "question": f"Sample question {i}",
            "trace": f"Sample trace {i}",
            "original_id": f"orig_{i}"
        }
        for i in range(TARGET_TASK_COUNT)
    ]


@pytest.fixture
def mock_scorer():
    """Create a mock StaticScorer for testing."""
    scorer = MagicMock(spec=StaticScorer)
    scorer.compute_score.return_value = {
        "task_id": "test",
        "scores": [0.1, 0.2, 0.3],
        "type": "static"
    }
    return scorer


def test_load_sampled_tasks_returns_exact_count(mock_config, sample_tasks):
    """Test that load_sampled_tasks returns exactly TARGET_TASK_COUNT tasks."""
    # Mock the dataset loading
    with patch('static_score.batch_processor.load_dataset') as mock_load:
        mock_load.return_value.to_pandas.return_value.to_dict.return_value = sample_tasks
        
        tasks = load_sampled_tasks(Path(mock_config.data_dir), TARGET_TASK_COUNT)
        
        assert len(tasks) == TARGET_TASK_COUNT
        assert all("task_id" in t for t in tasks)
        assert all("question" in t for t in tasks)
        assert all("trace" in t for t in tasks)


def test_process_single_task_returns_result(mock_scorer):
    """Test that process_single_task returns a valid result."""
    task = {
        "task_id": "test_task",
        "question": "Test question",
        "trace": "Test trace"
    }
    
    # Mock process_task_with_timeout to return a result
    with patch('static_score.batch_processor.process_task_with_timeout') as mock_timeout:
        mock_timeout.return_value = {
            "task_id": "test_task",
            "scores": [0.1, 0.2, 0.3],
            "type": "static"
        }
        
        result = process_single_task(task, mock_scorer)
        
        assert result is not None
        assert result["task_id"] == "test_task"
        assert "scores" in result


def test_process_single_task_handles_timeout(mock_scorer):
    """Test that process_single_task returns None on timeout."""
    task = {
        "task_id": "test_task",
        "question": "Test question",
        "trace": "Test trace"
    }
    
    # Mock process_task_with_timeout to return None (timeout)
    with patch('static_score.batch_processor.process_task_with_timeout') as mock_timeout:
        mock_timeout.return_value = None
        
        result = process_single_task(task, mock_scorer)
        
        assert result is None


def test_run_batch_processing_processes_correct_count(mock_config, sample_tasks, mock_scorer):
    """Test that run_batch_processing processes the correct number of tasks."""
    # Mock process_single_task to return a result for all tasks
    with patch('static_score.batch_processor.process_single_task') as mock_process:
        mock_process.return_value = {
            "task_id": "test",
            "scores": [0.1, 0.2, 0.3],
            "type": "static"
        }
        
        results = run_batch_processing(sample_tasks, mock_scorer)
        
        assert len(results) == TARGET_TASK_COUNT
        assert mock_process.call_count == TARGET_TASK_COUNT


def test_run_batch_processing_handles_exclusions(mock_config, sample_tasks, mock_scorer):
    """Test that run_batch_processing handles task exclusions correctly."""
    # Mock process_single_task to return None for 10% of tasks
    call_count = [0]
    
    def mock_process(task, scorer, timeout):
        call_count[0] += 1
        # Exclude 10% of tasks (below MAX_EXCLUSION_RATE)
        if call_count[0] % 10 == 0:
            return None
        return {
            "task_id": task["task_id"],
            "scores": [0.1, 0.2, 0.3],
            "type": "static"
        }
    
    with patch('static_score.batch_processor.process_single_task', side_effect=mock_process):
        results = run_batch_processing(sample_tasks, mock_scorer)
        
        # Should have 90% success rate (10% excluded, which is < MAX_EXCLUSION_RATE)
        assert len(results) == int(TARGET_TASK_COUNT * 0.9)


def test_save_results_creates_file(mock_config, sample_tasks):
    """Test that save_results creates the output file."""
    output_path = Path(mock_config.data_dir) / "test_output.json"
    results = sample_tasks[:10]
    
    save_results(results, output_path)
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == len(results)


def test_main_creates_output_file(mock_config, sample_tasks):
    """Test that main() creates the expected output file."""
    # Mock all dependencies
    with patch('static_score.batch_processor.load_sampled_tasks', return_value=sample_tasks):
        with patch('static_score.batch_processor.StaticScorer') as MockScorer:
            mock_scorer = MagicMock()
            MockScorer.return_value = mock_scorer
            
            with patch('static_score.batch_processor.run_batch_processing') as mock_run:
                mock_run.return_value = sample_tasks[:50]
                
                with patch('static_score.batch_processor.save_results') as mock_save:
                    main()
                    
                    # Verify save_results was called
                    assert mock_save.called
                    
                    # Verify output file path
                    call_args = mock_save.call_args
                    output_path = call_args[0][1]
                    
                    assert "static_scores.json" in str(output_path)

def test_high_exclusion_rate_triggers_exit(mock_config, sample_tasks, mock_scorer):
    """Test that high exclusion rate triggers RESOURCE_LIMIT_EXCEEDED."""
    # Mock process_single_task to return None for 50% of tasks
    def mock_process(task, scorer, timeout):
        # Exclude 50% of tasks (above MAX_EXCLUSION_RATE)
        if int(task["task_id"].split("_")[1]) % 2 == 0:
            return None
        return {
            "task_id": task["task_id"],
            "scores": [0.1, 0.2, 0.3],
            "type": "static"
        }
    
    with patch('static_score.batch_processor.process_single_task', side_effect=mock_process):
        with pytest.raises(SystemExit) as exc_info:
            run_batch_processing(sample_tasks, mock_scorer)
        
        assert exc_info.value.code == 1