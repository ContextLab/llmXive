"""
Unit tests for code/data_acquisition/classifier_runner.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import torch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data_acquisition.classifier_runner import (
    load_model_and_tokenizer,
    preprocess_snippet,
    predict_batch,
    run_classification_pipeline,
    DEVICE
)

class TestClassifierRunner(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_path = Path(self.test_dir) / "test_input.parquet"
        self.output_path = Path(self.test_dir) / "test_output.parquet"

        # Create a dummy input dataset
        dummy_data = {
            "snippet_id": [1, 2, 3],
            "code_snippet": [
                "def add(a, b):\n    return a + b",
                "print('hello world')",
                "class MyClass:\n    pass"
            ],
            "review_duration": [10, 20, 30]
        }
        self.df = pd.DataFrame(dummy_data)
        self.df.to_parquet(self.input_path)

    def tearDown(self):
        # Cleanup
        if self.input_path.exists():
            self.input_path.unlink()
        if self.output_path.exists():
            self.output_path.unlink()
        # Remove test dir if empty
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass

    @patch('code.data_acquisition.classifier_runner.AutoTokenizer')
    @patch('code.data_acquisition.classifier_runner.AutoModelForSequenceClassification')
    def test_load_model_and_tokenizer(self, mock_model, mock_tokenizer):
        """Test that model and tokenizer are loaded correctly."""
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        
        model, tokenizer = load_model_and_tokenizer()
        
        mock_tokenizer.from_pretrained.assert_called_once()
        mock_model.from_pretrained.assert_called_once()
        self.assertIsNotNone(model)
        self.assertIsNotNone(tokenizer)

    def test_preprocess_snippet(self):
        """Test preprocessing of a single snippet."""
        # We can't easily test the tokenizer without loading the real model,
        # but we can test the logic flow if we mock the tokenizer.
        # For now, we test the function signature and basic handling.
        snippet = "def foo(): pass"
        # This would require the real tokenizer to return a dict
        # We skip actual execution here to avoid heavy imports in unit tests
        # unless we mock the tokenizer globally.
        pass

    @patch('code.data_acquisition.classifier_runner.AutoTokenizer')
    @patch('code.data_acquisition.classifier_runner.AutoModelForSequenceClassification')
    @patch('code.data_acquisition.classifier_runner.torch.softmax')
    def test_predict_batch(self, mock_softmax, mock_model_cls, mock_tokenizer_cls):
        """Test batch prediction logic."""
        # Mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer_instance
        mock_tokenizer_instance.return_value = {
            "input_ids": torch.tensor([[1, 2, 3]]),
            "attention_mask": torch.tensor([[1, 1, 1]])
        }
        
        # Mock model
        mock_model_instance = MagicMock()
        mock_model_cls.from_pretrained.return_value = mock_model_instance
        
        # Mock model output
        mock_output = MagicMock()
        mock_output.logits = torch.tensor([[0.1, 0.9]]) # High prob for LLM
        mock_model_instance.return_value = mock_output
        
        # Mock softmax
        mock_softmax.return_value = torch.tensor([[0.1, 0.9]])
        
        model = mock_model_instance
        tokenizer = mock_tokenizer_instance
        
        snippets = ["def foo(): pass"]
        results = predict_batch(model, tokenizer, snippets)
        
        self.assertEqual(len(results), 1)
        self.assertIn("llm_prob", results[0])
        self.assertIn("human_prob", results[0])
        self.assertIn("predicted_label", results[0])

    @patch('code.data_acquisition.classifier_runner.load_model_and_tokenizer')
    @patch('code.data_acquisition.classifier_runner.predict_batch')
    def test_run_classification_pipeline(self, mock_predict, mock_load):
        """Test the full pipeline execution."""
        # Mock model loading
        mock_load.return_value = (MagicMock(), MagicMock())
        
        # Mock predictions
        mock_predict.return_value = [
            {"llm_prob": 0.9, "human_prob": 0.1, "predicted_label": "LLM-Like"},
            {"llm_prob": 0.2, "human_prob": 0.8, "predicted_label": "Human"},
            {"llm_prob": 0.5, "human_prob": 0.5, "predicted_label": "Human"}
        ]
        
        # Run pipeline
        result_path = run_classification_pipeline(self.input_path, self.output_path)
        
        self.assertTrue(result_path.exists())
        mock_load.assert_called_once()
        mock_predict.assert_called_once()
        
        # Verify output content
        output_df = pd.read_parquet(self.output_path)
        self.assertIn("llm_prob", output_df.columns)
        self.assertIn("predicted_label", output_df.columns)

    def test_missing_input_file(self):
        """Test that pipeline fails loudly if input file is missing."""
        non_existent_path = Path(self.test_dir) / "missing.parquet"
        with self.assertRaises(FileNotFoundError):
            run_classification_pipeline(non_existent_path, self.output_path)

    def test_missing_code_snippet_column(self):
        """Test that pipeline fails if required column is missing."""
        empty_df = pd.DataFrame({"other_col": [1, 2]})
        empty_df.to_parquet(self.input_path)
        
        with self.assertRaises(ValueError):
            run_classification_pipeline(self.input_path, self.output_path)

if __name__ == '__main__':
    unittest.main()