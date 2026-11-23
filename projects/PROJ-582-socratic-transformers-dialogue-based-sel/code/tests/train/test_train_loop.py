"""
Tests for the CPU-safe training loop with timeout handling.
"""
import os
import signal
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.train.train_loop import (
    TimeoutError,
    timeout_handler,
    setup_timeout,
    cancel_timeout,
    run_training_loop,
    main,
)
from src.utils.config import get_config

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "BASE_MODEL_ID": "test-model",
        "RESULTS_DIR": "/tmp/test_results",
        "PROCESSED_DIR": "/tmp/test_data",
    }

@pytest.fixture
def mock_dataset():
    """Mock dataset for testing."""
    return {
        "question": "What is 2+2?",
        "initial_answer": "4",
        "critique": "The answer is correct but lacks explanation.",
        "revised_answer": "2+2 equals 4 because adding two to two results in four.",
    }

def test_timeout_handler():
    """Test that timeout handler sets the flag and raises TimeoutError."""
    with pytest.raises(TimeoutError):
        timeout_handler(signal.SIGALRM, None)

@patch('os.name', 'posix')
def test_setup_timeout():
    """Test that setup_timeout configures SIGALRM."""
    with patch('signal.signal') as mock_signal, \
         patch('signal.alarm') as mock_alarm:
        setup_timeout(100)
        mock_signal.assert_called_once_with(signal.SIGALRM, timeout_handler)
        mock_alarm.assert_called_once_with(100)

@patch('os.name', 'posix')
def test_cancel_timeout():
    """Test that cancel_timeout resets the alarm."""
    with patch('signal.alarm') as mock_alarm:
        cancel_timeout()
        mock_alarm.assert_called_once_with(0)

@patch('os.name', 'posix')
@patch('src.train.train_loop.load_model_and_tokenizer')
@patch('src.train.train_loop.load_training_data')
@patch('src.train.train_loop.create_lora_config_from_env')
@patch('src.train.train_loop.Trainer')
@patch('src.train.train_loop.get_memory_usage')
@patch('src.train.train_setup_timeout')
@patch('src.train.train_loop.cancel_timeout')
def test_run_training_loop_success(
    mock_cancel_timeout,
    mock_setup_timeout,
    mock_memory_usage,
    mock_trainer,
    mock_lora_config,
    mock_load_data,
    mock_load_model,
):
    """Test successful training loop execution."""
    mock_memory_usage.return_value = 2.0
    mock_load_model.return_value = (MagicMock(), MagicMock())
    mock_load_data.return_value = MagicMock()
    mock_lora_config.return_value = MagicMock()
    mock_trainer.return_value = MagicMock()
    
    result = run_training_loop(
        model_id="test-model",
        dataset_path="/tmp/test.jsonl",
        output_dir="/tmp/output",
        timeout_seconds=100,
    )
    
    assert result is True
    mock_setup_timeout.assert_called_once_with(100)
    mock_cancel_timeout.assert_called_once()

@patch('os.name', 'posix')
@patch('src.train.train_loop.load_model_and_tokenizer')
@patch('src.train.train_loop.load_training_data')
@patch('src.train.train_loop.create_lora_config_from_env')
@patch('src.train.train_loop.Trainer')
@patch('src.train.train_loop.get_memory_usage')
@patch('src.train.train_setup_timeout')
@patch('src.train.train_loop.cancel_timeout')
def test_run_training_loop_timeout(
    mock_cancel_timeout,
    mock_setup_timeout,
    mock_memory_usage,
    mock_trainer,
    mock_lora_config,
    mock_load_data,
    mock_load_model,
):
    """Test training loop with simulated timeout."""
    mock_memory_usage.return_value = 2.0
    mock_load_model.return_value = (MagicMock(), MagicMock())
    mock_load_data.return_value = MagicMock()
    mock_lora_config.return_value = MagicMock()
    
    # Simulate timeout by raising TimeoutError
    with patch('src.train.train_loop.trainer.train', side_effect=TimeoutError("Test timeout")):
        with pytest.raises(SystemExit) as exc_info:
            run_training_loop(
                model_id="test-model",
                dataset_path="/tmp/test.jsonl",
                output_dir="/tmp/output",
                timeout_seconds=100,
            )
        assert exc_info.value.code == 1
    
    mock_cancel_timeout.assert_called_once()

@patch('os.name', 'posix')
@patch('src.train.train_loop.load_model_and_tokenizer')
@patch('src.train.train_loop.load_training_data')
@patch('src.train.train_loop.create_lora_config_from_env')
@patch('src.train.train_loop.Trainer')
@patch('src.train.train_loop.get_memory_usage')
@patch('src.train.train_setup_timeout')
@patch('src.train.train_loop.cancel_timeout')
def test_run_training_loop_memory_warning(
    mock_cancel_timeout,
    mock_setup_timeout,
    mock_memory_usage,
    mock_trainer,
    mock_lora_config,
    mock_load_data,
    mock_load_model,
):
    """Test training loop with high memory usage warning."""
    mock_memory_usage.return_value = 7.0  # Above 6.5GB threshold
    mock_load_model.return_value = (MagicMock(), MagicMock())
    mock_load_data.return_value = MagicMock()
    mock_lora_config.return_value = MagicMock()
    mock_trainer.return_value = MagicMock()
    
    # This should log a warning but continue
    result = run_training_loop(
        model_id="test-model",
        dataset_path="/tmp/test.jsonl",
        output_dir="/tmp/output",
        timeout_seconds=100,
    )
    
    assert result is True

@patch('os.name', 'nt')
def test_setup_timeout_windows():
    """Test that setup_timeout warns on Windows."""
    with patch('logging.Logger.warning') as mock_warning:
        setup_timeout(100)
        mock_warning.assert_called_once_with(
            "SIGALRM not supported on Windows, timeout disabled"
        )

@patch('src.train.train_loop.run_training_loop')
@patch('src.train.train_loop.get_config')
def test_main_success(mock_get_config, mock_run_training):
    """Test main function with successful training."""
    mock_get_config.return_value = MagicMock(
        BASE_MODEL_ID="test-model",
        RESULTS_DIR="/tmp/results",
        PROCESSED_DIR="/tmp/data",
    )
    mock_run_training.return_value = True
    
    with patch('sys.exit') as mock_exit:
        main()
        mock_exit.assert_called_once_with(0)

@patch('src.train.train_loop.run_training_loop')
@patch('src.train.train_loop.get_config')
def test_main_failure(mock_get_config, mock_run_training):
    """Test main function with failed training."""
    mock_get_config.return_value = MagicMock(
        BASE_MODEL_ID="test-model",
        RESULTS_DIR="/tmp/results",
        PROCESSED_DIR="/tmp/data",
    )
    mock_run_training.return_value = False
    
    with patch('sys.exit') as mock_exit:
        main()
        mock_exit.assert_called_once_with(1)
