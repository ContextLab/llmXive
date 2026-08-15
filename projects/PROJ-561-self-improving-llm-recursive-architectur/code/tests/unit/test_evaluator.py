"""
Unit tests for pipeline/evaluator.py
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import torch.nn as nn
import numpy as np
from pipeline.evaluator import (
    VerificationGate,
    load_gsm8k_dataset,
    load_arc_challenge_dataset,
    load_boolq_dataset,
    compute_gsm8k_accuracy,
    compute_arc_challenge_accuracy,
    compute_boolq_ece,
    run_all_benchmarks
)

class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 1)
    
    def forward(self, x):
        return self.linear(x)

class DummyTokenizer:
    def encode(self, text, **kwargs):
        return [1, 2, 3]
    
    def decode(self, ids):
        return "mock answer"

class TestVerificationGate(unittest.TestCase):
    def test_validate_predictions_correct(self):
        gate = VerificationGate()
        preds = [1, 2, 3]
        labels = [1, 2, 3]
        self.assertTrue(gate.validate_predictions(preds, labels))

    def test_validate_predictions_length_mismatch(self):
        gate = VerificationGate()
        preds = [1, 2]
        labels = [1, 2, 3]
        self.assertFalse(gate.validate_predictions(preds, labels))

class TestGSM8KAccuracy(unittest.TestCase):
    @patch('pipeline.evaluator.load_gsm8k')
    def test_compute_gsm8k_accuracy(self, mock_load):
        mock_load.return_value = [{'question': 'What is 2+2?', 'answer': '4'}]
        model = DummyModel()
        acc = compute_gsm8k_accuracy(model, mock_load.return_value)
        self.assertIsInstance(acc, float)
        # Since we mock inference, it should return 0.0 as per implementation
        self.assertEqual(acc, 0.0)

    @patch('pipeline.evaluator.load_gsm8k')
    def test_compute_gsm8k_accuracy_empty_dataset(self, mock_load):
        mock_load.return_value = []
        model = DummyModel()
        acc = compute_gsm8k_accuracy(model, mock_load.return_value)
        self.assertEqual(acc, 0.0)

class TestARCChallengeAccuracy(unittest.TestCase):
    @patch('pipeline.evaluator.load_arc_challenge')
    def test_compute_arc_challenge_accuracy(self, mock_load):
        mock_load.return_value = [{'question': 'Q', 'choices': ['A', 'B'], 'answer': 'A'}]
        model = DummyModel()
        acc = compute_arc_challenge_accuracy(model, mock_load.return_value)
        self.assertIsInstance(acc, float)
        self.assertEqual(acc, 0.0)

class TestBoolqECE(unittest.TestCase):
    @patch('pipeline.evaluator.load_boolq')
    def test_compute_boolq_ece(self, mock_load):
        mock_load.return_value = [{'question': 'Q', 'answer': True}]
        model = DummyModel()
        ece = compute_boolq_ece(model, mock_load.return_value)
        self.assertIsInstance(ece, float)
        self.assertEqual(ece, 0.0)

class TestRunAllBenchmarks(unittest.TestCase):
    @patch('pipeline.evaluator.load_gsm8k_dataset')
    @patch('pipeline.evaluator.load_arc_challenge_dataset')
    @patch('pipeline.evaluator.load_boolq_dataset')
    def test_run_all_benchmarks(self, mock_boolq, mock_arc, mock_gsm8k):
        mock_gsm8k.return_value = [{'q': '1'}]
        mock_arc.return_value = [{'q': '2'}]
        mock_boolq.return_value = [{'q': '3'}]
        
        model = DummyModel()
        results = run_all_benchmarks(model)
        
        self.assertIn('GSM8K_accuracy', results)
        self.assertIn('ARC_Challenge_accuracy', results)
        self.assertIn('BoolQ_ECE', results)
        self.assertIsInstance(results['GSM8K_accuracy'], float)

    @patch('pipeline.evaluator.load_gsm8k_dataset')
    @patch('pipeline.evaluator.load_arc_challenge_dataset')
    @patch('pipeline.evaluator.load_boolq_dataset')
    def test_run_all_benchmarks_missing_data(self, mock_boolq, mock_arc, mock_gsm8k):
        mock_gsm8k.side_effect = FileNotFoundError("Missing")
        mock_arc.return_value = [{'q': '2'}]
        mock_boolq.return_value = [{'q': '3'}]
        
        model = DummyModel()
        results = run_all_benchmarks(model)
        
        self.assertIsNone(results['GSM8K_accuracy'])
        self.assertIsInstance(results['ARC_Challenge_accuracy'], float)
        self.assertIsInstance(results['BoolQ_ECE'], float)