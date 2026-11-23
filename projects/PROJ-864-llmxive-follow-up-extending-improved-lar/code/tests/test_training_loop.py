"""
Integration tests for the training loop and logging functionality.

Verifies that the training loop completes without errors and logs
the required metrics per epoch.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

import torch
from training.train_loop import TextDataset, prepare_dataloaders, train_epoch, evaluate_epoch
from models.autoregressive import create_autoregressive_model
from utils.config import get_embed_dim, get_num_heads, get_vocab_size, get_max_seq_length, get_learning_rate, get_batch_size


class TestTrainingLoopLogging(unittest.TestCase):
    """Test cases for training loop and logging."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a small sample dataset for testing
        self.sample_data_path = self.temp_path / "sample_train.jsonl"
        with open(self.sample_data_path, "w", encoding="utf-8") as f:
            for i in range(100):
                f.write(json.dumps({"text": f"Sample text {i} for testing purposes.", "tokens": 10}) + "\n")
        
        self.sample_val_path = self.temp_path / "sample_val.jsonl"
        with open(self.sample_val_path, "w", encoding="utf-8") as f:
            for i in range(20):
                f.write(json.dumps({"text": f"Validation text {i} for testing.", "tokens": 8}) + "\n")

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_training_loop_runs_without_error(self):
        """Verify that a single epoch of training runs without errors."""
        # Create a small model for testing
        model = create_autoregressive_model()
        model.train()
        
        # Prepare dataloaders
        train_loader, val_loader = prepare_dataloaders(
            train_path=str(self.sample_data_path),
            val_path=str(self.sample_val_path),
            batch_size=2,
            max_seq_length=16
        )
        
        # Run one epoch
        try:
            train_loss = train_epoch(model, train_loader, device="cpu")
            val_loss = evaluate_epoch(model, val_loader, device="cpu")
            
            self.assertIsInstance(train_loss, float)
            self.assertIsInstance(val_loss, float)
            self.assertGreaterEqual(train_loss, 0)
            self.assertGreaterEqual(val_loss, 0)
            
        except Exception as e:
            self.fail(f"Training loop failed with error: {e}")

    def test_training_logs_metrics(self):
        """Verify that training logs the required metrics."""
        from training.callbacks import create_logging_callback
        
        model = create_autoregressive_model()
        model.train()
        
        train_loader, val_loader = prepare_dataloaders(
            train_path=str(self.sample_data_path),
            val_path=str(self.sample_val_path),
            batch_size=2,
            max_seq_length=16
        )
        
        log_path = self.temp_path / "training_log.csv"
        callback = create_logging_callback(str(log_path))
        
        # Run one epoch with callback
        train_loss = train_epoch(model, train_loader, device="cpu")
        val_loss = evaluate_epoch(model, val_loader, device="cpu")
        
        # Trigger callback
        callback.on_epoch_end(1, train_loss, val_loss, seed_id=0)
        
        # Verify log file exists and contains data
        self.assertTrue(log_path.exists(), "Training log file not created")
        
        with open(log_path, "r") as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0, "Training log file is empty")


def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTrainingLoopLogging)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
