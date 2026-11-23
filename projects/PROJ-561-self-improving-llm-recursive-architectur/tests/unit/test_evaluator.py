import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import torch.nn as nn
from pipeline.evaluator import (
    VerificationGate,
    compute_gsm8k_accuracy,
    compute_arc_challenge_accuracy,
    compute_wikitext2_ece,
    run_all_benchmarks
)
from datasets import Dataset
import numpy as np

class MockModel(nn.Module):
    """Mock model for testing"""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 10)
    
    def forward(self, x):
        return self.linear(x)
    
    def generate(self, *args, **kwargs):
        # Mock generate to return a fixed tensor
        return torch.tensor([[1, 2, 3, 4, 5]])

class MockTokenizer:
    """Mock tokenizer for testing"""
    def __init__(self):
        self.eos_token_id = 50256
    
    def __call__(self, text, return_tensors=None):
        return {"input_ids": torch.tensor([[1, 2, 3]])}
    
    def encode(self, text, add_special_tokens=False):
        return [1, 2, 3]
    
    def decode(self, tokens, skip_special_tokens=False):
        return "The answer is 42"

class TestVerificationGate(unittest.TestCase):
    def test_valid_dataset(self):
        gate = VerificationGate()
        self.assertTrue(gate.validate_dataset("gsm8k"))
        self.assertTrue(gate.validate_dataset("arc_challenge"))
        self.assertTrue(gate.validate_dataset("wikitext"))
    
    def test_invalid_dataset(self):
        gate = VerificationGate()
        with self.assertRaises(ValueError):
            gate.validate_dataset("invalid_dataset")

class TestGSM8KAccuracy(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_gsm8k_accuracy(self, mock_load_dataset):
        # Create mock dataset
        mock_data = [
            {"question": "What is 2+2?", "answer": "The answer is 4"},
            {"question": "What is 3+3?", "answer": "The answer is 6"}
        ]
        mock_dataset = Dataset.from_list(mock_data)
        mock_load_dataset.return_value = mock_dataset
        
        model = MockModel()
        tokenizer = MockTokenizer()
        
        accuracy = compute_gsm8k_accuracy(model, tokenizer, max_samples=2)
        
        # With our mock, both should be correct (42 matches 4 and 6 in string comparison fallback)
        # Actually, our mock returns "The answer is 42", which won't match "4" or "6"
        # So accuracy should be 0.0
        self.assertEqual(accuracy, 0.0)
    
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_gsm8k_accuracy_with_numeric_match(self, mock_load_dataset):
        # Create mock dataset
        mock_data = [
            {"question": "What is 2+2?", "answer": "The answer is 4"},
            {"question": "What is 3+3?", "answer": "The answer is 6"}
        ]
        mock_dataset = Dataset.from_list(mock_data)
        mock_load_dataset.return_value = mock_dataset
        
        model = MockModel()
        
        # Create a tokenizer that returns "42" for the first, "4" for the second
        class MockTokenizerWithCorrect:
            def __init__(self):
                self.eos_token_id = 50256
            
            def __call__(self, text, return_tensors=None):
                return {"input_ids": torch.tensor([[1, 2, 3]])}
            
            def encode(self, text, add_special_tokens=False):
                return [1, 2, 3]
            
            def decode(self, tokens, skip_special_tokens=False):
                # Return correct answer for second question
                if "3+3" in text:
                    return "The answer is 6"
                return "The answer is 4"
        
        tokenizer = MockTokenizerWithCorrect()
        
        accuracy = compute_gsm8k_accuracy(model, tokenizer, max_samples=2)
        
        # First is wrong (42 vs 4), second is correct (6 vs 6)
        self.assertEqual(accuracy, 0.5)

class TestARCChallengeAccuracy(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_arc_challenge_accuracy(self, mock_load_dataset):
        # Create mock dataset
        mock_data = [
            {
                "question": "What is the capital of France?",
                "choices": {"text": ["London", "Paris"], "label": ["A", "B"]},
                "answerKey": "B"
            }
        ]
        mock_dataset = Dataset.from_list(mock_data)
        mock_load_dataset.return_value = mock_dataset
        
        model = MockModel()
        tokenizer = MockTokenizer()
        
        accuracy = compute_arc_challenge_accuracy(model, tokenizer, max_samples=1)
        
        # Our mock always picks the last choice, which is "B"
        # So it should be correct
        self.assertEqual(accuracy, 1.0)

class TestWikitext2ECE(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_wikitext2_ece(self, mock_load_dataset):
        # Create mock dataset
        mock_data = [
            {"text": "The quick brown fox jumps over the lazy dog."},
            {"text": "Hello world"}
        ]
        mock_dataset = Dataset.from_list(mock_data)
        mock_load_dataset.return_value = mock_dataset
        
        model = MockModel()
        tokenizer = MockTokenizer()
        
        ece = compute_wikitext2_ece(model, tokenizer, max_samples=2)
        
        # ECE should be a float between 0 and 1
        self.assertIsInstance(ece, float)
        self.assertGreaterEqual(ece, 0.0)
        self.assertLessEqual(ece, 1.0)

class TestRunAllBenchmarks(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_run_all_benchmarks(self, mock_load_dataset):
        # Mock all datasets
        def mock_load(name, *args, **kwargs):
            if "gsm8k" in name:
                return Dataset.from_list([{"question": "Q", "answer": "A: 4"}])
            elif "arc" in name:
                return Dataset.from_list([{
                    "question": "Q",
                    "choices": {"text": ["A", "B"], "label": ["A", "B"]},
                    "answerKey": "B"
                }])
            else:
                return Dataset.from_list([{"text": "Sample text"}])
        
        mock_load_dataset.side_effect = mock_load
        
        model = MockModel()
        tokenizer = MockTokenizer()
        
        results = run_all_benchmarks(model, tokenizer, max_samples=1)
        
        self.assertIn("GSM8K", results)
        self.assertIn("ARC", results)
        self.assertIn("ECE", results)
        
        # All results should be floats
        self.assertIsInstance(results["GSM8K"], float)
        self.assertIsInstance(results["ARC"], float)
        self.assertIsInstance(results["ECE"], float)

if __name__ == "__main__":
    unittest.main()