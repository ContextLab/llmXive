"""
Unit tests for the evaluation runner module.
"""
import pytest
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from evaluation.runner import (
    load_repopeftbench_data,
    load_ast_adapter,
    compute_exact_match,
    run_inference,
    run_evaluation,
    save_results
)
from utils.config import Config

@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock(spec=Config)
    config.repo_peft_bench_path = "repo-peft-bench"
    config.base_model_path = "TinyLlama-1.1B-Chat-hf"
    config.ast_adapter_path = "data/adapters/ast_adapter"
    config.results_dir = "data/results"
    config.sample_size = 10
    return config

@pytest.fixture
def mock_dataset():
    """Create a mock dataset."""
    return [
        {
            'task_id': 'task_001',
            'input': 'def add(a, b):\n    return a + b',
            'output': 'def add(a, b):\n    return a + b'
        },
        {
            'task_id': 'task_002',
            'input': 'def multiply(a, b):\n    return a * b',
            'output': 'def multiply(a, b):\n    return a * b'
        }
    ]

def test_compute_exact_match_success():
    """Test exact match computation with matching strings."""
    prediction = "def add(a, b):\n    return a + b"
    reference = "def add(a, b):\n    return a + b"
    assert compute_exact_match(prediction, reference) is True

def test_compute_exact_match_failure():
    """Test exact match computation with non-matching strings."""
    prediction = "def add(a, b):\n    return a - b"
    reference = "def add(a, b):\n    return a + b"
    assert compute_exact_match(prediction, reference) is False

def test_compute_exact_match_whitespace():
    """Test exact match computation ignores leading/trailing whitespace."""
    prediction = "  def add(a, b):\n    return a + b  "
    reference = "def add(a, b):\n    return a + b"
    assert compute_exact_match(prediction, reference) is True

@patch('evaluation.runner.datasets.load_dataset')
def test_load_repopeftbench_data(mock_load_dataset, mock_config):
    """Test loading RepoPeftBench dataset."""
    mock_dataset = Mock()
    mock_dataset.__iter__ = Mock(return_value=iter([{'task_id': 'test'}]))
    mock_load_dataset.return_value = mock_dataset
    
    dataset = load_repopeftbench_data(mock_config, sample_size=1)
    
    mock_load_dataset.assert_called_once_with(
        "repo-peft-bench",
        "python",
        split="test",
        streaming=True
    )

@patch('evaluation.runner.AutoTokenizer.from_pretrained')
@patch('evaluation.runner.AutoModelForCausalLM.from_pretrained')
@patch('evaluation.runner.PeftModel.from_pretrained')
def test_load_ast_adapter(
    mock_peft_model, 
    mock_base_model, 
    mock_tokenizer, 
    mock_config,
    tmp_path
):
    """Test loading AST adapter."""
    # Create a fake adapter directory
    adapter_dir = tmp_path / "adapters" / "ast_adapter"
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "adapter_config.json").write_text("{}")
    
    mock_config.ast_adapter_path = str(adapter_dir)
    
    mock_tokenizer.return_value = Mock()
    mock_base_model.return_value = Mock()
    mock_peft_model.return_value = Mock()
    mock_peft_model.return_value.merge_and_unload.return_value = Mock()
    
    model, tokenizer = load_ast_adapter(mock_config)
    
    assert model is not None
    assert tokenizer is not None

@patch('evaluation.runner.time.perf_counter')
@patch('evaluation.runner.AutoModelForCausalLM.generate')
@patch('evaluation.runner.AutoTokenizer')
def test_run_inference(mock_tokenizer, mock_generate, mock_perf_counter):
    """Test inference execution and latency measurement."""
    mock_model = Mock()
    mock_model.device = "cpu"
    
    mock_tokenizer_instance = Mock()
    mock_tokenizer.return_value = mock_tokenizer_instance
    
    mock_inputs = {'input_ids': torch.tensor([[1, 2, 3]])}
    mock_tokenizer_instance.__call__.return_value = mock_inputs
    
    mock_output = Mock()
    mock_output.__getitem__.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    mock_generate.return_value = mock_output
    
    mock_tokenizer_instance.decode.side_effect = [
        "input text",  # Full decode
        "generated text"  # Generated part only
    ]
    
    mock_perf_counter.side_effect = [0.0, 0.1]  # Start and end times
    
    task = {
        'input': 'test input',
        'output': 'test output'
    }
    
    prediction, latency_ms = run_inference(mock_model, mock_tokenizer_instance, task)
    
    assert prediction == "generated text"
    assert latency_ms == 100.0  # 0.1 seconds = 100ms

def test_save_results(tmp_path):
    """Test saving results to CSV."""
    results = [
        {'task_id': 'task_001', 'exact_match': 1, 'latency_ms': 100.5},
        {'task_id': 'task_002', 'exact_match': 0, 'latency_ms': 150.2}
    ]
    
    output_path = tmp_path / "test_scores.csv"
    save_results(results, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2
    assert rows[0]['task_id'] == 'task_001'
    assert rows[0]['exact_match'] == '1'
    assert rows[0]['latency_ms'] == '100.5'
    assert rows[1]['task_id'] == 'task_002'
    assert rows[1]['exact_match'] == '0'
    assert rows[1]['latency_ms'] == '150.2'

def test_save_results_creates_directory(tmp_path):
    """Test that save_results creates parent directories if they don't exist."""
    results = [
        {'task_id': 'task_001', 'exact_match': 1, 'latency_ms': 100.5}
    ]
    
    output_path = tmp_path / "nested" / "dir" / "scores.csv"
    save_results(results, str(output_path))
    
    assert output_path.exists()
    assert output_path.parent.exists()

@patch('evaluation.runner.load_repopeftbench_data')
@patch('evaluation.runner.load_ast_adapter')
@patch('evaluation.runner.run_evaluation')
@patch('evaluation.runner.save_results')
def test_main_execution(
    mock_save_results, 
    mock_run_evaluation, 
    mock_load_adapter, 
    mock_load_data,
    mock_config,
    tmp_path
):
    """Test the main function execution flow."""
    mock_config.results_dir = str(tmp_path)
    mock_config.sample_size = 10
    
    mock_dataset = [
        {'task_id': 'task_001', 'input': 'test', 'output': 'test'}
    ]
    mock_load_data.return_value = mock_dataset
    
    mock_model = Mock()
    mock_tokenizer = Mock()
    mock_load_adapter.return_value = (mock_model, mock_tokenizer)
    
    mock_results = [
        {'task_id': 'task_001', 'exact_match': 1, 'latency_ms': 100.0}
    ]
    mock_run_evaluation.return_value = mock_results
    
    # Patch the main function to use our mock config
    with patch('evaluation.runner.load_config', return_value=mock_config):
        from evaluation.runner import main
        main()
    
    mock_load_data.assert_called_once()
    mock_load_adapter.assert_called_once()
    mock_run_evaluation.assert_called_once()
    mock_save_results.assert_called_once()
    
    # Verify output file was created
    output_path = Path(tmp_path) / "ast_scores.csv"
    assert output_path.exists()
    
    summary_path = Path(tmp_path) / "ast_evaluation_summary.json"
    assert summary_path.exists()
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    assert 'accuracy' in summary
    assert 'avg_latency_ms' in summary
    assert summary['total_tasks'] == 1
