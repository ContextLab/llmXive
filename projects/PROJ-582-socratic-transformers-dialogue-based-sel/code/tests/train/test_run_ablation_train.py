"""
Tests for the Ablation Training Run (T047b).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
import torch
from datasets import Dataset

# Add code root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.train.run_ablation_train import load_ablation_data, prepare_dataset, main

@pytest.fixture
def sample_ablation_data():
    return [
        {
            "question": "What is 2+2?",
            "initial_answer": "It is 5.",
            "critique": "[NEUTRAL PLACEHOLDER]",
            "revised_answer": "It is 4."
        },
        {
            "question": "Solve for x: 2x = 10",
            "initial_answer": "x is 3.",
            "critique": "[NEUTRAL PLACEHOLDER]",
            "revised_answer": "x is 5."
        }
    ]

@pytest.fixture
def temp_jsonl_file(sample_ablation_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in sample_ablation_data:
            f.write(json.dumps(item) + '\n')
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_ablation_data_valid(temp_jsonl_file, sample_ablation_data):
    """Test loading valid ablation data."""
    data = load_ablation_data(Path(temp_jsonl_file))
    assert len(data) == len(sample_ablation_data)
    assert data[0]['question'] == sample_ablation_data[0]['question']
    assert 'revised_answer' in data[0]

def test_load_ablation_data_missing_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_ablation_data(Path("/nonexistent/path/file.jsonl"))

def test_load_ablation_data_invalid_json(temp_jsonl_file):
    """Test handling of invalid JSON lines."""
    with open(temp_jsonl_file, 'a') as f:
        f.write("not valid json\n")
    
    # Should load the valid lines and skip the invalid one (based on implementation)
    data = load_ablation_data(Path(temp_jsonl_file))
    # The implementation logs a warning but continues
    assert len(data) == 2 

def test_prepare_dataset(sample_ablation_data):
    """Test dataset preparation and tokenization logic."""
    # Mock tokenizer
    mock_tokenizer = MagicMock()
    # Mock return values for tokenizer calls
    mock_tokenizer.return_value = {
        'input_ids': [101, 102, 103],
        'attention_mask': [1, 1, 1]
    }
    mock_tokenizer.get_vocab.return_value = {'<pad>': 0, 'test': 1}

    ds = prepare_dataset(sample_ablation_data, mock_tokenizer)
    
    assert isinstance(ds, Dataset)
    assert len(ds) == len(sample_ablation_data)
    assert 'input_ids' in ds.column_names
    assert 'labels' in ds.column_names

@patch('src.train.run_ablation_train.get_config')
@patch('src.train.run_ablation_train.load_model_and_tokenizer')
@patch('src.train.run_ablation_train.prepare_model_for_lora')
@patch('src.train.run_ablation_train.Trainer')
@patch('src.train.run_ablation_train.setup_timeout')
@patch('src.train.run_ablation_train.time')
@patch('src.train.run_ablation_train.torch')
def test_main_execution_flow(
    mock_torch, mock_time, mock_setup_timeout, mock_trainer, mock_prepare, mock_load_model, mock_get_config, temp_jsonl_file
):
    """Test the main execution flow without actual training."""
    # Setup mocks
    mock_config = MagicMock()
    mock_config.BASE_MODEL_ID = "test-model"
    mock_config.CRITIC_MODEL_ID = "test-critic"
    mock_get_config.return_value = mock_config

    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_load_model.return_value = (mock_model, mock_tokenizer)
    
    mock_prepare_model = MagicMock()
    mock_prepare.return_value = mock_prepare_model

    mock_trainer_instance = MagicMock()
    mock_trainer.return_value = mock_trainer_instance

    mock_time.time.side_effect = [0, 100] # start, end
    
    mock_torch.save = MagicMock()

    # Run main
    # We need to patch the file path resolution in main to use our temp file
    # Since main() constructs the path internally, we might need to patch the specific path logic
    # or pass the data via environment. For now, we assume the temp file is at the expected location
    # or we patch the load_ablation_data function directly to return sample data.
    
    with patch('src.train.run_ablation_train.load_ablation_data', return_value=[{"question": "q", "initial_answer": "a", "critique": "c", "revised_answer": "r"}]):
        with patch('src.train.run_ablation_train.PROJECT_ROOT', Path(temp_jsonl_file).parent):
            try:
                main()
            except SystemExit:
                pass # Expected if timeout or other logic triggers, but we mocked most things.

    # Verify calls
    mock_load_model.assert_called_once()
    mock_prepare.assert_called_once()
    mock_trainer.assert_called_once()
    mock_trainer_instance.train.assert_called_once()
    # Verify save was called
    assert mock_torch.save.called