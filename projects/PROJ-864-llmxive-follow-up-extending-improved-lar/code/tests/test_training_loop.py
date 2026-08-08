"""
Integration test for training loop logging (US2).

This test verifies that the training loop correctly logs metrics
(epoch, train_loss, val_loss, gap, time, ram) as expected by the
callbacks module and that the training completes without OOM errors
on a small subset of the Micro-Corpus.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import (
    get_config,
    get_batch_size,
    get_learning_rate,
    get_num_epochs,
    get_data_dir,
    get_processed_dir,
    get_artifacts_dir,
    reset_config,
    ConfigError,
)
from utils.logging import get_logger, setup_logging, reset_logging
from utils.monitor import get_ram_usage_gb
from models.config import get_model_config
from training.callbacks import TrainingCallback, LogMetricsCallback
from training.train_loop import train_epoch, run_training

logger = get_logger(__name__)

class TestTrainingLoopLogging(unittest.TestCase):
    """Integration tests for training loop logging functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        reset_logging()
        setup_logging(level="INFO")
        # Ensure config is loaded
        try:
            reset_config()
            get_config()
        except ConfigError as e:
            logger.warning(f"Config not fully loaded, using defaults: {e}")

    def setUp(self):
        """Set up per-test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir)
        
        # Create a minimal mock dataset for testing
        self._create_mock_dataset()

    def _create_mock_dataset(self):
        """Create a small mock dataset for integration testing."""
        processed_dir = Path(self.temp_dir) / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a small JSONL file with mock training data
        mock_data_path = processed_dir / "micro_corpus.jsonl"
        mock_data = []
        for i in range(100):  # Small dataset for quick testing
            mock_data.append({
                "text": f"This is mock training data sample {i} for integration testing.",
                "id": i
            })
        
        with open(mock_data_path, 'w') as f:
            for item in mock_data:
                f.write(json.dumps(item) + '\n')
        
        # Update config to use our temp directory
        os.environ["DATA_DIR"] = str(Path(self.temp_dir).parent)
        os.environ["PROCESSED_DIR"] = str(processed_dir)

    def tearDown(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_metrics_callback_initialization(self):
        """Test that LogMetricsCallback initializes correctly."""
        callback = LogMetricsCallback()
        self.assertIsInstance(callback.logs, list)
        self.assertEqual(len(callback.logs), 0)

    def test_log_metrics_callback_on_epoch_end(self):
        """Test that LogMetricsCallback logs metrics correctly at epoch end."""
        callback = LogMetricsCallback()
        
        # Simulate epoch end with sample metrics
        epoch = 1
        train_loss = 2.5
        val_loss = 2.3
        gap = 0.2
        time_elapsed = 120.5
        ram_usage = 4.2
        
        callback.on_epoch_end(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            gap=gap,
            time_elapsed=time_elapsed,
            ram_usage=ram_usage
        )
        
        self.assertEqual(len(callback.logs), 1)
        log_entry = callback.logs[0]
        
        self.assertEqual(log_entry["epoch"], epoch)
        self.assertAlmostEqual(log_entry["train_loss"], train_loss, places=4)
        self.assertAlmostEqual(log_entry["val_loss"], val_loss, places=4)
        self.assertAlmostEqual(log_entry["gap"], gap, places=4)
        self.assertAlmostEqual(log_entry["time"], time_elapsed, places=2)
        self.assertAlmostEqual(log_entry["ram"], ram_usage, places=2)

    def test_training_loop_logs_metrics(self):
        """Test that the training loop actually logs metrics to disk."""
        # Create a temporary file for logs
        log_file_path = self.artifacts_dir / "training_logs_test.csv"
        
        # Setup callback to write to our temp file
        callback = LogMetricsCallback(log_file=str(log_file_path))
        
        # Run a single epoch training on mock data
        # We'll use a very small batch size and few steps for testing
        config = get_config()
        
        try:
            # Run training for 1 epoch with mock data
            metrics = run_training(
                num_epochs=1,
                batch_size=2,
                callbacks=[callback],
                data_dir=Path(self.temp_dir),
                processed_dir=Path(self.temp_dir) / "processed"
            )
            
            # Verify log file was created and contains data
            self.assertTrue(log_file_path.exists(), "Log file was not created")
            
            with open(log_file_path, 'r') as f:
                lines = f.readlines()
            
            self.assertGreater(len(lines), 1, "Log file is empty or has no data rows")
            
            # Check header
            header = lines[0].strip()
            self.assertIn("epoch", header)
            self.assertIn("train_loss", header)
            self.assertIn("val_loss", header)
            self.assertIn("gap", header)
            self.assertIn("time", header)
            self.assertIn("ram", header)
            
        except Exception as e:
            logger.error(f"Training loop test failed: {e}")
            raise

    def test_no_oom_error_on_small_dataset(self):
        """Test that training completes without OOM on small dataset."""
        callback = LogMetricsCallback()
        
        try:
            # Run a single epoch
            run_training(
                num_epochs=1,
                batch_size=1,
                callbacks=[callback],
                data_dir=Path(self.temp_dir),
                processed_dir=Path(self.temp_dir) / "processed"
            )
            
            # If we get here without OOM, test passes
            self.assertTrue(True)
            
        except MemoryError:
            self.fail("Training loop raised MemoryError on small dataset")
        except Exception as e:
            # Other exceptions might be expected if models aren't fully implemented
            # but we're specifically testing for OOM
            if "CUDA out of memory" in str(e) or "OOM" in str(e):
                self.fail(f"Training loop raised OOM error: {e}")
            # Re-raise other exceptions as they might indicate other issues
            raise

    def test_gap_calculation(self):
        """Test that generalization gap is calculated correctly."""
        callback = LogMetricsCallback()
        
        train_loss = 2.0
        val_loss = 2.5
        expected_gap = val_loss - train_loss  # 0.5
        
        callback.on_epoch_end(
            epoch=1,
            train_loss=train_loss,
            val_loss=val_loss,
            gap=expected_gap,
            time_elapsed=10.0,
            ram_usage=3.0
        )
        
        log_entry = callback.logs[0]
        self.assertAlmostEqual(log_entry["gap"], expected_gap, places=4)

    def test_log_file_format(self):
        """Test that the log file has the correct CSV format."""
        log_file_path = self.artifacts_dir / "training_logs_format_test.csv"
        callback = LogMetricsCallback(log_file=str(log_file_path))
        
        # Add some sample logs
        for epoch in range(1, 4):
            callback.on_epoch_end(
                epoch=epoch,
                train_loss=2.0 - epoch * 0.1,
                val_loss=2.2 - epoch * 0.1,
                gap=0.2,
                time_elapsed=epoch * 30.0,
                ram_usage=4.0 + epoch * 0.1
            )
        
        # Write logs to file
        callback.save_logs()
        
        with open(log_file_path, 'r') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        self.assertEqual(len(lines), 4)  # Header + 3 data rows
        
        # Check that all required columns are present
        header = lines[0].split(',')
        required_columns = ["epoch", "train_loss", "val_loss", "gap", "time", "ram"]
        for col in required_columns:
            self.assertIn(col, header, f"Missing column: {col}")

def run_tests():
    """Run all tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrainingLoopLogging)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result

if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)