"""
Unit tests for the evaluator module.
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import torch.nn as nn
import numpy as np
from pipeline.evaluator import (
    VerificationGate, 
    compute_gsm8k_accuracy, 
    compute_arc_challenge_accuracy, 
    compute_boolq_ece,
    run_all_benchmarks
)

class DummyModel(nn.Module):
    """A dummy model for testing."""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 10)
        
    def forward(self, x):
        return self.linear(x)
        
    def generate(self, input_ids, max_new_tokens, temperature, do_sample):
        # Mock generation that returns input_ids + some tokens
        return torch.cat([input_ids, torch.ones((input_ids.shape[0], 5), dtype=input_ids.dtype)], dim=1)

class DummyTokenizer:
    """A dummy tokenizer for testing."""
    def __init__(self):
        self.pad_token_id = 0
        
    def __call__(self, text, return_tensors, truncation, max_length):
        # Return mock tensor
        return {'input_ids': torch.tensor([[1, 2, 3, 4, 5]])}
        
    def decode(self, token_ids, skip_special_tokens):
        return "Mock response"
        
    @property
    def model_max_length(self):
        return 512

class TestVerificationGate(unittest.TestCase):
    def test_verification_gate_initialization(self):
        gate = VerificationGate()
        self.assertEqual(gate.benchmarks, ["gsm8k", "arc_challenge", "boolq"])
        
    def test_verify_input_valid(self):
        gate = VerificationGate()
        self.assertTrue(gate.verify_input({"data": "test"}))
        
    def test_verify_input_none(self):
        gate = VerificationGate()
        self.assertFalse(gate.verify_input(None))

class TestGSM8KAccuracy(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_gsm8k_accuracy(self, mock_load_dataset):
        # Mock dataset
        mock_dataset = [
            {'question': 'What is 2+2?', 'answer': 'The answer is 4.'},
            {'question': 'What is 3+3?', 'answer': 'The answer is 6.'}
        ]
        mock_load_dataset.return_value = mock_dataset
        
        model = DummyModel()
        tokenizer = DummyTokenizer()
        
        # Mock tokenizer methods
        tokenizer.decode = MagicMock(return_value="Question: What is 2+2?\nAnswer: The answer is 4.")
        
        accuracy = compute_gsm8k_accuracy(model, tokenizer, mock_dataset)
        
        self.assertIsInstance(accuracy, float)
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 1.0)

class TestARCChallengeAccuracy(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_arc_challenge_accuracy(self, mock_load_dataset):
        # Mock dataset
        mock_dataset = [
            {
                'question': 'What is the capital of France?',
                'choices': {
                    'text': ['Paris', 'London', 'Berlin'],
                    'label': ['A', 'B', 'C']
                },
                'answerKey': 'A'
            }
        ]
        mock_load_dataset.return_value = mock_dataset
        
        model = DummyModel()
        tokenizer = DummyTokenizer()
        
        accuracy = compute_arc_challenge_accuracy(model, tokenizer, mock_dataset)
        
        self.assertIsInstance(accuracy, float)
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 1.0)

class TestBoolqECE(unittest.TestCase):
    @patch('pipeline.evaluator.load_dataset')
    def test_compute_boolq_ece(self, mock_load_dataset):
        # Mock dataset
        mock_dataset = [
            {'question': 'Is the sky blue?', 'answer': True},
            {'question': 'Is grass red?', 'answer': False}
        ]
        mock_load_dataset.return_value = mock_dataset
        
        model = DummyModel()
        tokenizer = DummyTokenizer()
        
        # Mock the model's forward pass to return predictable logits
        original_forward = model.forward
        def mock_forward(x):
            class MockOutput:
                def __init__(self):
                    self.logits = torch.tensor([[[1.0, 0.0]]])  # High confidence for first class
            return MockOutput()
        
        model.forward = mock_forward
        
        ece = compute_boolq_ece(model, tokenizer, mock_dataset)
        
        self.assertIsInstance(ece, float)
        self.assertGreaterEqual(ece, 0.0)
        self.assertLessEqual(ece, 1.0)

class TestRunAllBenchmarks(unittest.TestCase):
    @patch('pipeline.evaluator.load_gsm8k_dataset')
    @patch('pipeline.evaluator.load_arc_challenge_dataset')
    @patch('pipeline.evaluator.load_boolq_dataset')
    def test_run_all_benchmarks(self, mock_boolq, mock_arc, mock_gsm8k):
        # Mock datasets
        mock_gsm8k.return_value = [{'question': 'Test', 'answer': '4'}]
        mock_arc.return_value = [{'question': 'Test', 'choices': {'text': ['A'], 'label': ['A']}, 'answerKey': 'A'}]
        mock_boolq.return_value = [{'question': 'Test', 'answer': True}]
        
        model = DummyModel()
        tokenizer = DummyTokenizer()
        
        # Mock the accuracy functions to return fixed values
        with patch('pipeline.evaluator.compute_gsm8k_accuracy', return_value=0.8), \
             patch('pipeline.evaluator.compute_arc_challenge_accuracy', return_value=0.7), \
             patch('pipeline.evaluator.compute_boolq_ece', return_value=0.1):
            
                results = run_all_benchmarks(model, tokenizer)
                
                self.assertIn('GSM8K', results)
                self.assertIn('ARC', results)
                self.assertIn('BoolQ', results)
                
                self.assertIsInstance(results['GSM8K'], float)
                self.assertIsInstance(results['ARC'], float)
                self.assertIsInstance(results['BoolQ'], float)
                
                self.assertEqual(results['GSM8K'], 0.8)
                self.assertEqual(results['ARC'], 0.7)
                self.assertEqual(results['BoolQ'], 0.1)

if __name__ == '__main__':
    unittest.main()