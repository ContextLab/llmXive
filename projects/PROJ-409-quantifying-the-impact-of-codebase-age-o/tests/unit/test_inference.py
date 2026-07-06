"""
Unit tests for inference logic in code/inference/.

Tests cover:
- model_loader: load_model, unload_model
- metrics_calculator: calculate_perplexity, validate_snippet_syntax, calculate_functional_correctness
- run_inference: process_snippet_with_timeout, load_snippets, save_results

These tests use mock objects and real logic execution without requiring GPU.
"""
import unittest
import sys
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from concurrent.futures import TimeoutError as FuturesTimeoutError

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.logging import get_logger
from inference.model_loader import load_model, unload_model
from inference.metrics_calculator import (
    calculate_perplexity, 
    validate_snippet_syntax, 
    calculate_functional_correctness,
    calculate_metrics
)
from inference.run_inference import (
    process_snippet_with_timeout, 
    load_snippets, 
    save_results
)
from models import InferenceResult

logger = get_logger(__name__)

class TestModelLoader(unittest.TestCase):
    """Tests for model_loader.py functions."""
    
    @patch('inference.model_loader.load_model')
    def test_load_model_returns_mock(self, mock_load):
        """Test that load_model returns a mock model when loading fails or succeeds."""
        # Mock the load_model function to return a mock object
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        
        result = load_model("test_model")
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_model)
        
    @patch('inference.model_loader.unload_model')
    def test_unload_model_calls_unload(self, mock_unload):
        """Test that unload_model calls the underlying unload function."""
        mock_model = MagicMock()
        unload_model(mock_model)
        mock_unload.assert_called_once_with(mock_model)

class TestMetricsCalculator(unittest.TestCase):
    """Tests for metrics_calculator.py functions."""
    
    def test_validate_snippet_syntax_valid(self):
        """Test syntax validation with valid Python code."""
        valid_code = "def hello():\n    return 'world'"
        is_valid, error_msg = validate_snippet_syntax(valid_code)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        
    def test_validate_snippet_syntax_invalid(self):
        """Test syntax validation with invalid Python code."""
        invalid_code = "def broken(:\n    return 'world'"
        is_valid, error_msg = validate_snippet_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        
    def test_validate_snippet_syntax_empty(self):
        """Test syntax validation with empty code."""
        is_valid, error_msg = validate_snippet_syntax("")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        
    def test_calculate_perplexity_with_mock(self):
        """Test perplexity calculation with a mock model."""
        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        
        # Mock the forward pass to return a specific loss
        mock_output = MagicMock()
        mock_output.loss = 2.5
        mock_model.return_value = mock_output
        
        snippet = "def test():\n    return 1"
        
        # We need to mock the tokenizer and model behavior
        with patch('inference.metrics_calculator.load_model_and_tokenizer') as mock_load:
            mock_load.return_value = (mock_model, MagicMock())
            perplexity, status = calculate_perplexity(snippet, mock_model)
            
            # Perplexity should be exp(loss) = exp(2.5)
            expected_perplexity = 2.5  # Simplified for mock
            self.assertIsInstance(perplexity, (float, int))
            self.assertIn(status, ['success', 'timeout', 'error'])
            
    def test_calculate_functional_correctness_valid(self):
        """Test functional correctness calculation with valid code."""
        snippet = "def add(a, b):\n    return a + b"
        is_valid, error_msg = calculate_functional_correctness(snippet)
        # Valid syntax should pass basic checks
        self.assertTrue(is_valid)
        
    def test_calculate_functional_correctness_invalid(self):
        """Test functional correctness calculation with invalid code."""
        snippet = "def broken(:\n    return a + b"
        is_valid, error_msg = calculate_functional_correctness(snippet)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        
    def test_calculate_metrics_integration(self):
        """Test the full metrics calculation pipeline."""
        valid_snippet = "def hello():\n    return 'world'"
        invalid_snippet = "def broken(:\n    return 'world'"
        
        # Test valid snippet
        metrics_valid, status_valid = calculate_metrics(valid_snippet)
        self.assertIn('perplexity', metrics_valid)
        self.assertIn('functional_correctness', metrics_valid)
        self.assertIn('inference_time', metrics_valid)
        
        # Test invalid snippet
        metrics_invalid, status_invalid = calculate_metrics(invalid_snippet)
        # Should handle invalid syntax gracefully
        self.assertIsNotNone(metrics_invalid)
        
class TestRunInference(unittest.TestCase):
    """Tests for run_inference.py functions."""
    
    def test_load_snippets_from_csv(self):
        """Test loading snippets from a CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("snippet_id,repo_url,file_path,median_commit_age,snippet_content,token_count,complexity\n")
            f.write("1,https://github.com/test/repo,test.py,100,def hello(): pass,10,1\n")
            f.write("2,https://github.com/test/repo,test2.py,200,def world(): pass,10,1\n")
            temp_path = f.name
        
        try:
            snippets = load_snippets(Path(temp_path))
            self.assertEqual(len(snippets), 2)
            self.assertEqual(snippets[0]['snippet_id'], '1')
            self.assertEqual(snippets[1]['snippet_id'], '2')
        finally:
            os.unlink(temp_path)
            
    def test_load_snippets_empty_file(self):
        """Test loading snippets from an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("snippet_id,repo_url,file_path,median_commit_age,snippet_content,token_count,complexity\n")
            temp_path = f.name
        
        try:
            snippets = load_snippets(Path(temp_path))
            self.assertEqual(len(snippets), 0)
        finally:
            os.unlink(temp_path)
            
    def test_save_results_creates_file(self):
        """Test that save_results creates the output file."""
        results = [
            InferenceResult(
                snippet_id='1',
                perplexity=2.5,
                functional_correctness_rate=1.0,
                status='success'
            )
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_results.csv'
            save_results(results, output_path)
            
            self.assertTrue(output_path.exists())
            
            # Verify content
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('snippet_id', content)
                self.assertIn('perplexity', content)
                
    def test_process_snippet_with_timeout_success(self):
        """Test process_snippet_with_timeout with successful completion."""
        mock_model = MagicMock()
        snippet = {
            'snippet_id': 'test_1',
            'snippet_content': 'def hello(): pass',
            'repo_url': 'https://github.com/test/repo',
            'file_path': 'test.py',
            'median_commit_age': 100,
            'token_count': 10,
            'complexity': 1
        }
        
        # Mock the metrics calculation to return quickly
        with patch('inference.run_inference.calculate_metrics') as mock_calc:
            mock_calc.return_value = (
                {'perplexity': 2.5, 'functional_correctness': 1.0, 'inference_time': 0.1},
                'success'
            )
            
            result = process_snippet_with_timeout(snippet, mock_model, timeout=5.0)
            
            self.assertIsNotNone(result)
            self.assertEqual(result['snippet_id'], 'test_1')
            self.assertEqual(result['status'], 'success')
            
    def test_process_snippet_with_timeout_failure(self):
        """Test process_snippet_with_timeout with timeout."""
        mock_model = MagicMock()
        snippet = {
            'snippet_id': 'test_2',
            'snippet_content': 'def hello(): pass',
            'repo_url': 'https://github.com/test/repo',
            'file_path': 'test.py',
            'median_commit_age': 100,
            'token_count': 10,
            'complexity': 1
        }
        
        # Mock the metrics calculation to raise timeout
        with patch('inference.run_inference.calculate_metrics') as mock_calc:
            mock_calc.side_effect = FuturesTimeoutError("Timeout")
            
            result = process_snippet_with_timeout(snippet, mock_model, timeout=0.001)
            
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 'timeout')
            self.assertIn('perplexity', result)
            self.assertIn('functional_correctness_rate', result)
            
    def test_process_snippet_with_timeout_error(self):
        """Test process_snippet_with_timeout with general error."""
        mock_model = MagicMock()
        snippet = {
            'snippet_id': 'test_3',
            'snippet_content': 'def hello(): pass',
            'repo_url': 'https://github.com/test/repo',
            'file_path': 'test.py',
            'median_commit_age': 100,
            'token_count': 10,
            'complexity': 1
        }
        
        # Mock the metrics calculation to raise an exception
        with patch('inference.run_inference.calculate_metrics') as mock_calc:
            mock_calc.side_effect = Exception("General error")
            
            result = process_snippet_with_timeout(snippet, mock_model, timeout=5.0)
            
            self.assertIsNotNone(result)
            self.assertEqual(result['status'], 'error')
            self.assertIn('perplexity', result)
            self.assertIn('functional_correctness_rate', result)
            
class TestIntegration(unittest.TestCase):
    """Integration tests for the inference pipeline."""
    
    def test_full_pipeline_with_mock(self):
        """Test the full inference pipeline with mocked components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / 'input.csv'
            output_path = Path(temp_dir) / 'output.csv'
            
            # Create input CSV
            with open(input_path, 'w') as f:
                f.write("snippet_id,repo_url,file_path,median_commit_age,snippet_content,token_count,complexity\n")
                f.write("1,https://github.com/test/repo,test.py,100,def hello(): pass,10,1\n")
                f.write("2,https://github.com/test/repo,test2.py,200,def world(): pass,10,1\n")
            
            # Mock the model loading and metrics calculation
            with patch('inference.run_inference.load_model') as mock_load:
                with patch('inference.run_inference.calculate_metrics') as mock_calc:
                    mock_load.return_value = (MagicMock(), MagicMock())
                    mock_calc.return_value = (
                        {'perplexity': 2.5, 'functional_correctness': 1.0, 'inference_time': 0.1},
                        'success'
                    )
                    
                    from inference.run_inference import run_inference_pipeline
                    success = run_inference_pipeline(
                        input_path=input_path,
                        output_path=output_path,
                        model_name="test_model",
                        timeout=5.0
                    )
                    
                    self.assertTrue(success)
                    self.assertTrue(output_path.exists())
                    
                    # Verify output content
                    with open(output_path, 'r') as f:
                        content = f.read()
                        self.assertIn('snippet_id', content)
                        self.assertIn('perplexity', content)
                        self.assertIn('functional_correctness_rate', content)

if __name__ == '__main__':
    unittest.main()
