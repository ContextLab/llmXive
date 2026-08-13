"""
Integration tests for quantized inference service.

Tests error handling, model loading, and partial completion.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
import os

from src.services.quantized_inference import (
    InferenceResult,
    load_quantized_model,
    process_sample,
    run_quantized_inference_batch
)
from src.config.env_config import get_model_path

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_sample():
    return {
        'input_id': 'test-123',
        'prompt': 'What is 2+2?',
        'answer': '4'
    }

@pytest.fixture
def mock_config():
    return {
        'MODEL_PATH': '/fake/path/model.gguf',
        'DATASET_ID': 'gsm8k'
    }

def test_load_quantized_model_invalid_level():
    """Test that invalid quantization level raises ValueError."""
    with pytest.raises(ValueError):
        load_quantized_model('/fake/path', 'invalid_level')

def test_process_sample_empty_prompt(mock_sample):
    """Test that empty prompt results in failure."""
    mock_sample['prompt'] = ''
    result = process_sample(mock_sample, 'int4', {})
    
    assert result.success is False
    assert result.error == "Empty prompt"
    assert result.logits == []

@patch('src.services.quantized_inference.load_quantized_model')
def test_process_sample_model_load_failure(mock_load_model, mock_sample):
    """Test that model loading failure is handled gracefully."""
    mock_load_model.return_value = None
    
    result = process_sample(mock_sample, 'int4', {})
    
    assert result.success is False
    assert "Failed to load model" in result.error
    assert result.logits == []

@patch('src.services.quantized_inference.llama_cpp.Llama')
@patch('src.services.quantized_inference.load_quantized_model')
def test_process_sample_success(mock_load_model, mock_llama_class, mock_sample):
    """Test successful inference path."""
    mock_model_instance = MagicMock()
    mock_load_model.return_value = mock_model_instance
    
    # Mock the create_completion to return valid logprobs
    mock_output = {
        'choices': [{
            'logprobs': {
                'token_logprobs': [-0.1, -0.2, -0.3]
            }
        }]
    }
    mock_model_instance.create_completion.return_value = mock_output
    
    result = process_sample(mock_sample, 'int4', {'int4': mock_model_instance})
    
    assert result.success is True
    assert result.input_id == 'test-123'
    assert result.quantization_level == 'int4'
    assert len(result.logits) == 3
    assert result.error is None

@patch('src.services.quantized_inference.llama_cpp.Llama')
@patch('src.services.quantized_inference.load_quantized_model')
def test_process_sample_inference_error(mock_load_model, mock_llama_class, mock_sample):
    """Test that inference errors are caught and logged."""
    mock_model_instance = MagicMock()
    mock_load_model.return_value = mock_model_instance
    
    # Mock the create_completion to raise an error
    mock_model_instance.create_completion.side_effect = Exception("Inference crash")
    
    result = process_sample(mock_sample, 'int4', {'int4': mock_model_instance})
    
    assert result.success is False
    assert result.error == "Inference crash"
    assert result.logits == []

@patch('src.services.quantized_inference.load_dataset_streaming')
@patch('src.services.quantized_inference.process_sample')
def test_run_quantized_inference_batch_partial_success(mock_process, mock_load_stream, mock_sample):
    """Test batch processing with partial success."""
    # Mock dataset stream
    mock_dataset = [mock_sample, mock_sample, mock_sample]
    mock_load_stream.return_value = iter(mock_dataset)
    
    # Mock process_sample to return mixed results
    results = [
        InferenceResult('1', 'int4', [0.1], success=True),
        InferenceResult('2', 'int4', [], success=False, error="Failed"),
        InferenceResult('3', 'int4', [0.2], success=True)
    ]
    mock_process.side_effect = results
    
    batch_results = run_quantized_inference_batch('gsm8k', max_samples=3)
    
    assert len(batch_results) == 3
    successful = [r for r in batch_results if r.success]
    assert len(successful) == 2
    # Verify that the function didn't crash despite failures

@patch('src.services.quantized_inference.load_dataset_streaming')
@patch('src.services.quantized_inference.process_sample')
def test_run_quantized_inference_batch_all_failures(mock_process, mock_load_stream, mock_sample):
    """Test that batch processing raises error if all samples fail."""
    mock_dataset = [mock_sample]
    mock_load_stream.return_value = iter(mock_dataset)
    
    # All failures
    mock_process.return_value = InferenceResult('1', 'int4', [], success=False, error="All failed")
    
    with pytest.raises(RuntimeError, match="Quantized inference failed for all samples"):
        run_quantized_inference_batch('gsm8k', max_samples=1)
