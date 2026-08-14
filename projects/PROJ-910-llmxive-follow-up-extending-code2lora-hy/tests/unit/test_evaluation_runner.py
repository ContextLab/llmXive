"""
Unit tests for evaluation runner.

Tests the core functionality of code/evaluation/runner.py
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch

from evaluation.runner import (
    load_repopeftbench_data,
    load_ast_adapter,
    run_inference,
    compute_exact_match,
    run_evaluation,
    save_results
)

class TestComputeExactMatch:
    """Tests for exact match computation"""
    
    def test_exact_match_identical(self):
        """Test that identical strings match"""
        result = compute_exact_match("hello world", "hello world")
        assert result is True
    
    def test_exact_match_different(self):
        """Test that different strings don't match"""
        result = compute_exact_match("hello world", "goodbye world")
        assert result is False
    
    def test_exact_match_whitespace_normalization(self):
        """Test that whitespace differences are normalized"""
        result = compute_exact_match("hello  world", "hello world")
        assert result is True
    
    def test_exact_match_newlines(self):
        """Test that newlines are normalized"""
        result = compute_exact_match("hello\nworld", "hello world")
        assert result is True
    
    def test_exact_match_case_sensitive(self):
        """Test that matching is case sensitive"""
        result = compute_exact_match("Hello World", "hello world")
        assert result is False

class TestRunInference:
    """Tests for inference execution"""
    
    @patch('evaluation.runner.AutoModelForCausalLM')
    @patch('evaluation.runner.AutoTokenizer')
    def test_run_inference_mock_model(self, mock_tokenizer, mock_model):
        """Test inference with mocked model"""
        # Setup mocks
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = '<pad>'
        mock_tokenizer.return_value = mock_tokenizer_instance
        
        mock_model_instance = Mock()
        mock_model.return_value = mock_model_instance
        
        # Mock generate to return specific output
        mock_input_ids = torch.tensor([[1, 2, 3]])
        mock_tokenizer_instance.__call__.return_value = {'input_ids': mock_input_ids}
        
        mock_output_ids = torch.tensor([[1, 2, 3, 4, 5]])
        mock_model_instance.generate.return_value = mock_output_ids
        
        mock_tokenizer_instance.decode.return_value = "test output"
        
        # Run inference
        result = run_inference(mock_model_instance, mock_tokenizer_instance, "test prompt")
        
        # Verify
        assert result == "test output"
        mock_model_instance.generate.assert_called_once()

class TestSaveResults:
    """Tests for result saving"""
    
    def test_save_results_creates_file(self):
        """Test that save_results creates the output file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.csv"
            
            results = [
                {
                    'task_id': 'test_1',
                    'generated': 'hello',
                    'expected': 'hello',
                    'exact_match': True,
                    'error': None
                }
            ]
            
            save_results(results, str(output_path))
            
            assert output_path.exists()
            
            # Verify file content
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'task_id' in content
                assert 'test_1' in content
                assert 'hello' in content
                assert 'True' in content
    
    def test_save_results_multiple_tasks(self):
        """Test saving multiple results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.csv"
            
            results = [
                {
                    'task_id': 'test_1',
                    'generated': 'hello',
                    'expected': 'hello',
                    'exact_match': True,
                    'error': None
                },
                {
                    'task_id': 'test_2',
                    'generated': 'world',
                    'expected': 'universe',
                    'exact_match': False,
                    'error': None
                }
            ]
            
            save_results(results, str(output_path))
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
                # Header + 2 data rows
                assert len(lines) == 3

class TestRunEvaluation:
    """Tests for evaluation pipeline"""
    
    @patch('evaluation.runner.run_inference')
    def test_run_evaluation_success(self, mock_inference):
        """Test evaluation with successful inference"""
        mock_inference.return_value = "expected output"
        
        tasks = [
            {
                'task_id': 'task_1',
                'prompt': 'test prompt',
                'expected_output': 'expected output'
            }
        ]
        
        model = Mock()
        tokenizer = Mock()
        
        results = run_evaluation(tasks, model, tokenizer)
        
        assert len(results) == 1
        assert results[0]['task_id'] == 'task_1'
        assert results[0]['exact_match'] is True
        assert results[0]['error'] is None
    
    @patch('evaluation.runner.run_inference')
    def test_run_evaluation_with_error(self, mock_inference):
        """Test evaluation when inference fails"""
        mock_inference.side_effect = Exception("Test error")
        
        tasks = [
            {
                'task_id': 'task_1',
                'prompt': 'test prompt',
                'expected_output': 'expected output'
            }
        ]
        
        model = Mock()
        tokenizer = Mock()
        
        results = run_evaluation(tasks, model, tokenizer)
        
        assert len(results) == 1
        assert results[0]['task_id'] == 'task_1'
        assert results[0]['exact_match'] is False
        assert 'Test error' in results[0]['error']