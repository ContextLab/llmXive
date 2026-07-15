import torch
import pytest
import os
import sys
import tempfile
import pandas as pd
import time
from metrics.perplexity import log_perplexity_to_csv
from models.baseline_transformer import create_baseline_model
from data.dataset_loader import get_wikitext_dataloader

class EarlyStopping:
    """
    Early stopping to stop training when validation loss does not improve.
    
    Attributes:
        patience (int): Number of epochs with no improvement after which training will be stopped.
        delta (float): Minimum change in the monitored quantity to qualify as an improvement.
        counter (int): Current epoch counter since last improvement.
        best_score (float): Best validation loss seen so far.
        early_stop (bool): Flag to indicate if early stopping has been triggered.
    """
    def __init__(self, patience=2, delta=0.01):
        self.patience = patience
        self.delta = delta
        self.counter = 0
        self.best_score = None
        self.early_stop = False

    def __call__(self, val_loss):
        if self.best_score is None:
            self.best_score = val_loss
            self.counter = 0
        elif val_loss > self.best_score - self.delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = val_loss
            self.counter = 0

def test_early_stopping_patience():
    """Test that early stopping triggers after patience epochs of no improvement."""
    stopping = EarlyStopping(patience=3, delta=0.01)
    
    # Simulate no improvement
    for i in range(3):
        stopping(1.0)  # Same loss, no improvement
        assert not stopping.early_stop, f"Should not stop at epoch {i}"
    
    # One more epoch without improvement should trigger stop
    stopping(1.0)
    assert stopping.early_stop, "Should have stopped after patience epochs"

def test_early_stopping_improvement():
    """Test that early stopping resets counter on improvement."""
    stopping = EarlyStopping(patience=2, delta=0.01)
    
    # Initial
    stopping(1.0)
    assert stopping.best_score == 1.0
    
    # Improvement
    stopping(0.9)
    assert stopping.best_score == 0.9
    assert stopping.counter == 0
    
    # No improvement
    stopping(0.95)
    assert stopping.counter == 1
    
    # Improvement again should reset counter
    stopping(0.85)
    assert stopping.best_score == 0.85
    assert stopping.counter == 0

def test_early_stopping_no_improvement_threshold():
    """Test that small improvements within delta threshold don't count as improvement."""
    stopping = EarlyStopping(patience=2, delta=0.05)
    
    stopping(1.0)
    # Improvement smaller than delta
    stopping(0.98)  # 0.02 improvement < 0.05 delta
    assert stopping.counter == 1
    assert stopping.best_score == 1.0  # Should not update best score
    
    # Another small improvement
    stopping(0.96)  # 0.04 improvement < 0.05 delta
    assert stopping.counter == 2
    assert stopping.early_stop, "Should have stopped after patience epochs"

def test_early_stopping_integration_with_training_loop():
    """Test early stopping integrated with a simulated training loop."""
    model = create_baseline_model()
    train_loader, val_loader = get_wikitext_dataloader(batch_size=16)
    
    stopping = EarlyStopping(patience=2, delta=0.01)
    
    # Simulate a few epochs where loss plateaus
    for epoch in range(5):
        # Simulate validation loss (plateauing at 1.0)
        val_loss = 1.0
        stopping(val_loss)
        
        if stopping.early_stop:
            break
    
    assert stopping.early_stop, "Training should have stopped due to early stopping"
    assert stopping.counter >= stopping.patience, "Counter should have reached patience"

def test_early_stopping_with_real_metrics_logging():
    """Test early stopping with actual metric logging to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test_metrics.csv")
        
        # Create a mock model and data
        model = create_baseline_model()
        train_loader, val_loader = get_wikitext_dataloader(batch_size=16)
        
        stopping = EarlyStopping(patience=2, delta=0.01)
        
        # Simulate training with plateauing loss
        for epoch in range(5):
            # Simulate validation loss
            val_loss = 1.0 + (0.001 * epoch)  # Slightly increasing loss
            perplexity = torch.exp(torch.tensor(val_loss)).item()
            
            # Log metrics
            log_perplexity_to_csv(csv_path, epoch=epoch, perplexity=perplexity, 
                                energy_per_token=0.0, wall_clock_time=1.0)
            
            # Check early stopping
            stopping(val_loss)
            if stopping.early_stop:
                break
        
        # Verify CSV was created and has correct structure
        assert os.path.exists(csv_path), "CSV file should be created"
        df = pd.read_csv(csv_path)
        assert 'epoch' in df.columns, "CSV should have epoch column"
        assert 'perplexity' in df.columns, "CSV should have perplexity column"
        assert len(df) <= stopping.patience + 1, "Training should have stopped early"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])