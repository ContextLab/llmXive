import torch
import pytest
import os
import sys
import tempfile
import pandas as pd

# Import the EarlyStopping class from the test_training_loop module where it is defined
from tests.test_training_loop import EarlyStopping, MetricRecord

def test_early_stopping_patience():
    """
    Test that EarlyStopping stops training after 'patience' epochs without improvement.
    """
    early_stopper = EarlyStopping(patience=2, delta=0.01, mode='min')
    
    # Simulate a loss curve that improves then plateaus
    losses = [1.0, 0.9, 0.85, 0.85, 0.85] 
    
    should_stop = False
    for epoch, loss in enumerate(losses):
        should_stop = early_stopper(loss)
        if should_stop:
            break
    
    # Should stop at epoch 3 (index 3), which is the 4th epoch (0, 1, 2, 3)
    # Improvement at 0, 1, 2. 
    # Epoch 3: 0.85 vs 0.85 (delta 0.01 required). No improvement. Count = 1.
    # Epoch 4: 0.85 vs 0.85. No improvement. Count = 2 (patience reached).
    # So it should return True at epoch 4 (index 4).
    # Let's re-verify logic:
    # 0: 1.0 -> best=1.0, counter=0
    # 1: 0.9 -> best=0.9, counter=0
    # 2: 0.85 -> best=0.85, counter=0
    # 3: 0.85 -> 0.85 >= 0.85 - 0.01? Yes. No improvement. counter=1.
    # 4: 0.85 -> counter=2. Stop.
    assert should_stop, "Early stopping should trigger after patience is exceeded"
    assert early_stopper.counter == 2

def test_early_stopping_improvement():
    """
    Test that EarlyStopping resets counter when improvement is seen.
    """
    early_stopper = EarlyStopping(patience=2, delta=0.01, mode='min')
    
    # Loss improves, then stagnates, then improves again
    losses = [1.0, 0.9, 0.85, 0.85, 0.80, 0.80]
    
    should_stop = False
    for epoch, loss in enumerate(losses):
        should_stop = early_stopper(loss)
        if should_stop:
            break
    
    # Should NOT stop at epoch 5 because epoch 4 reset the counter.
    assert not should_stop, "Early stopping should not trigger if improvement occurs"
    assert early_stopper.counter == 0

def test_early_stopping_no_improvement_threshold():
    """
    Test that small improvements below delta do not reset the counter.
    """
    early_stopper = EarlyStopping(patience=2, delta=0.1, mode='min')
    
    losses = [1.0, 0.95, 0.94] # 0.95 is improvement, but 0.94 is only 0.01 better than 0.95 (delta 0.1)
    
    # 0: 1.0 -> best=1.0
    # 1: 0.95 -> best=0.95, counter=0
    # 2: 0.94 -> 0.94 < 0.95 - 0.1? No. No improvement. counter=1.
    
    should_stop = early_stopper(losses[2])
    assert not should_stop
    assert early_stopper.counter == 1

def test_early_stopping_integration_with_training_loop():
    """
    Integration test: Ensure EarlyStopping works correctly within a simulated training loop.
    """
    early_stopper = EarlyStopping(patience=2, delta=0.01, mode='min')
    
    # Simulate a training loop that runs for max 10 epochs
    max_epochs = 10
    epoch = 0
    losses = [1.0, 0.9, 0.85, 0.85, 0.85, 0.85]
    
    for loss in losses:
        epoch += 1
        if early_stopper(loss):
            break
    
    # Should stop after epoch 4 (index 4 in losses list, but 5th iteration)
    # Wait, let's re-trace:
    # i=0, loss=1.0 -> best=1.0, counter=0
    # i=1, loss=0.9 -> best=0.9, counter=0
    # i=2, loss=0.85 -> best=0.85, counter=0
    # i=3, loss=0.85 -> no improvement, counter=1
    # i=4, loss=0.85 -> no improvement, counter=2 -> STOP
    # So loop breaks at i=4.
    
    assert epoch == 5, f"Training should stop at epoch 5, but stopped at {epoch}"