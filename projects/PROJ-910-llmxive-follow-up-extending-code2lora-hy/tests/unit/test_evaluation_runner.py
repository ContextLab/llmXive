"""
Contract test for runner.py scoring logic on a mock assertion task.

This test validates the core scoring mechanism of the evaluation runner
by mocking the assertion task data and verifying the exact-match calculation.
"""
import pytest
import torch
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.runner import calculate_exact_match, evaluate_task, EvaluationRunner
from utils.config import Config


class MockTask:
    """Mock assertion task for testing."""
    def __init__(self, task_id: str, prompt: str, expected_output: str):
        self.task_id = task_id
        self.prompt = prompt
        self.expected_output = expected_output
        self.timeout = 30
        self.category = "syntax"


class MockModel:
    """Mock model that returns deterministic outputs for testing."""
    def __init__(self):
        self.device = torch.device("cpu")
    
    def generate(self, input_ids, max_length, **kwargs):
        # Return a simple tensor of tokens for testing
        # In a real scenario, this would be the model's output
        return torch.tensor([[101, 202, 303]])  # Mock token IDs


class MockTokenizer:
    """Mock tokenizer for testing."""
    def __init__(self):
        self.pad_token_id = 0
        self.eos_token_id = 2
    
    def __call__(self, text, return_tensors="pt", **kwargs):
        # Return a mock tensor with token IDs
        return {
            "input_ids": torch.tensor([[101, 202, 303]]),
            "attention_mask": torch.tensor([[1, 1, 1]])
        }
    
    def decode(self, token_ids, skip_special_tokens=True):
        # Return a mock decoded string
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()
        # Flatten if needed
        if isinstance(token_ids[0], list):
            token_ids = token_ids[0]
        return "mock generated output"


def test_calculate_exact_match():
    """Test the exact match calculation logic."""
    # Test case 1: Exact match
    predicted = "def hello():\n    print('world')"
    expected = "def hello():\n    print('world')"
    assert calculate_exact_match(predicted, expected) == 1.0
    
    # Test case 2: No match
    predicted = "def hello():\n    print('universe')"
    expected = "def hello():\n    print('world')"
    assert calculate_exact_match(predicted, expected) == 0.0
    
    # Test case 3: Partial match (should be 0.0 for exact match)
    predicted = "def hello():\n    print('world')"
    expected = "def hello():\n    print('world')\nprint('extra')"
    assert calculate_exact_match(predicted, expected) == 0.0
    
    # Test case 4: Case sensitivity
    predicted = "Hello"
    expected = "hello"
    assert calculate_exact_match(predicted, expected) == 0.0


def test_evaluate_task_with_mock():
    """Test evaluate_task function with mocked model and tokenizer."""
    task = MockTask(
        task_id="test_001",
        prompt="Write a hello world function",
        expected_output="def hello():\n    print('world')"
    )
    
    mock_model = MockModel()
    mock_tokenizer = MockTokenizer()
    
    # Mock the model's forward pass to return deterministic output
    with patch.object(mock_model, 'generate', return_value=torch.tensor([[101, 202, 303]])):
        # Mock tokenizer.decode to return the expected output for exact match test
        with patch.object(mock_tokenizer, 'decode', return_value="def hello():\n    print('world')"):
            score, prediction = evaluate_task(task, mock_model, mock_tokenizer)
            
            assert score == 1.0, f"Expected exact match score of 1.0, got {score}"
            assert prediction == "def hello():\n    print('world')"


def test_evaluation_runner_initialization():
    """Test EvaluationRunner initialization with mock config."""
    mock_config = Mock(spec=Config)
    mock_config.base_model_path = "mock_model"
    mock_config.adapter_path = "mock_adapter"
    mock_config.device = "cpu"
    
    runner = EvaluationRunner(mock_config)
    
    assert runner.config == mock_config
    assert runner.device == torch.device("cpu")


def test_evaluation_runner_run_single_task():
    """Test EvaluationRunner.run_single_task with mocked dependencies."""
    mock_config = Mock(spec=Config)
    mock_config.base_model_path = "mock_model"
    mock_config.adapter_path = "mock_adapter"
    mock_config.device = "cpu"
    
    runner = EvaluationRunner(mock_config)
    
    task = MockTask(
        task_id="test_001",
        prompt="Write a hello world function",
        expected_output="def hello():\n    print('world')"
    )
    
    # Mock the model and tokenizer loading
    with patch.object(runner, '_load_model', return_value=MockModel()):
        with patch.object(runner, '_load_tokenizer', return_value=MockTokenizer()):
            # Mock the evaluate_task function
            with patch('evaluation.runner.evaluate_task', return_value=(1.0, "def hello():\n    print('world')")):
                result = runner.run_single_task(task)
                
                assert result['task_id'] == "test_001"
                assert result['score'] == 1.0
                assert result['prediction'] == "def hello():\n    print('world')"
                assert result['status'] == "success"


def test_evaluation_runner_batch_evaluation():
    """Test EvaluationRunner.batch_evaluation with multiple mock tasks."""
    mock_config = Mock(spec=Config)
    mock_config.base_model_path = "mock_model"
    mock_config.adapter_path = "mock_adapter"
    mock_config.device = "cpu"
    
    runner = EvaluationRunner(mock_config)
    
    tasks = [
        MockTask("test_001", "prompt1", "output1"),
        MockTask("test_002", "prompt2", "output2"),
        MockTask("test_003", "prompt3", "output3"),
    ]
    
    # Mock run_single_task to return deterministic results
    with patch.object(runner, 'run_single_task', side_effect=[
        {'task_id': 'test_001', 'score': 1.0, 'prediction': 'output1', 'status': 'success'},
        {'task_id': 'test_002', 'score': 0.0, 'prediction': 'wrong_output', 'status': 'success'},
        {'task_id': 'test_003', 'score': 1.0, 'prediction': 'output3', 'status': 'success'},
    ]):
        results = runner.batch_evaluation(tasks)
        
        assert len(results) == 3
        assert results[0]['score'] == 1.0
        assert results[1]['score'] == 0.0
        assert results[2]['score'] == 1.0
        
        # Calculate average score
        avg_score = sum(r['score'] for r in results) / len(results)
        assert avg_score == (1.0 + 0.0 + 1.0) / 3.0


def test_exact_match_edge_cases():
    """Test exact match with edge cases."""
    # Empty strings
    assert calculate_exact_match("", "") == 1.0
    assert calculate_exact_match("", "non-empty") == 0.0
    assert calculate_exact_match("non-empty", "") == 0.0
    
    # Whitespace differences
    assert calculate_exact_match("hello", "hello ") == 0.0
    assert calculate_exact_match("hello ", "hello") == 0.0
    
    # Newline differences
    assert calculate_exact_match("hello\n", "hello") == 0.0
    assert calculate_exact_match("hello", "hello\n") == 0.0
    
    # Unicode normalization (should be exact match)
    assert calculate_exact_match("café", "café") == 1.0
    
    # Very long strings
    long_string = "a" * 10000
    assert calculate_exact_match(long_string, long_string) == 1.0
    assert calculate_exact_match(long_string, long_string[:-1]) == 0.0