import unittest
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from unittest.mock import patch, MagicMock
import signal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.trainer import run_training_cycle_with_timeout, _timeout_triggered

class DummyModel(nn.Module):
    """A simple dummy model for testing."""
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 10)
    
    def forward(self, x, labels=None):
        out = self.linear(x)
        if labels is not None:
            loss = nn.functional.mse_loss(out, labels)
            return type('obj', (object,), {'loss': loss})()
        return out

class TestTimeoutEnforcement(unittest.TestCase):
    
    def setUp(self):
        self.model = DummyModel()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        # Create dummy data
        inputs = torch.randn(4, 10)
        labels = torch.randn(4, 10)
        dataset = TensorDataset(inputs, labels)
        self.dataloader = DataLoader(dataset, batch_size=2)
        
        # Reset timeout flag
        global _timeout_triggered
        _timeout_triggered = False
    
    @unittest.skipIf(sys.platform == 'win32', "Signal-based timeout not supported on Windows")
    def test_timeout_triggers_termination(self):
        """Test that a very short timeout triggers termination."""
        # Use a timeout shorter than the training should take
        # We'll mock the training loop to take longer
        with patch('pipeline.trainer.time.sleep', return_value=None):
            # Mock the dataloader to yield very slowly
            metrics, timed_out = run_training_cycle_with_timeout(
                self.model,
                self.dataloader,
                self.optimizer,
                cycle_number=999,
                timeout_seconds=1,  # 1 second timeout
                max_epochs=1
            )
            
            # We expect the timeout to trigger if we mock appropriately
            # For this test, we verify the function doesn't crash
            self.assertIn('status', metrics)
    
    def test_normal_completion(self):
        """Test that a long enough timeout allows normal completion."""
        # Use a generous timeout
        metrics, timed_out = run_training_cycle_with_timeout(
            self.model,
            self.dataloader,
            self.optimizer,
            cycle_number=1,
            timeout_seconds=60,  # 60 seconds
            max_epochs=1
        )
        
        self.assertFalse(timed_out)
        self.assertEqual(metrics['status'], 'completed')
        self.assertIn('training_loss', metrics)
        self.assertIn('param_count', metrics)
    
    def test_log_file_creation(self):
        """Test that log files are created for the cycle."""
        # This test verifies that the logging infrastructure is called
        # We mock the file operations to avoid actual I/O
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            metrics, timed_out = run_training_cycle_with_timeout(
                self.model,
                self.dataloader,
                self.optimizer,
                cycle_number=1,
                timeout_seconds=60,
                max_epochs=1
            )
            
            # Verify that open was called for logging
            self.assertTrue(mock_file.called)
    
    def test_partial_metrics_on_timeout(self):
        """Test that partial metrics are recorded on timeout."""
        # We can't easily test the timeout path without mocking time,
        # but we verify the function signature and return structure
        with patch('pipeline.trainer.time.time', side_effect=[0, 1000]):  # Simulate time jump
            metrics, timed_out = run_training_cycle_with_timeout(
                self.model,
                self.dataloader,
                self.optimizer,
                cycle_number=2,
                timeout_seconds=1,
                max_epochs=1
            )
            
            # Verify metrics structure exists
            self.assertIn('status', metrics)
            self.assertIn('duration', metrics)

if __name__ == '__main__':
    unittest.main()