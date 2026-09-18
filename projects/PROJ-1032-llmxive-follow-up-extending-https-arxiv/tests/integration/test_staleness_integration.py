"""Integration tests for staleness queue in training."""
import pytest
import torch
import json
import os
import tempfile
from pathlib import Path
from src.llmxive.staleness_queue import StalenessQueue
from src.llmxive.trainer import AsyncRLTrainer

class TestStalenessIntegration:
    """Integration tests for staleness functionality."""
    
    def test_staleness_queue_integration(self):
        """Test staleness queue in a training-like scenario."""
        queue = StalenessQueue(buffer_size=5)
        
        # Simulate gradient updates with varying staleness
        for i in range(10):
            grad = torch.randn(10)
            queue.push(grad, staleness=i)
        
        # Check queue size
        assert len(queue) == 5
        
        # Check staleness clamping
        oldest = queue.get_oldest()
        assert oldest[1] == 4  # Clamped to buffer_size - 1
    
    def test_trainer_with_staleness(self):
        """Test trainer with non-zero staleness."""
        trainer = AsyncRLTrainer(
            model_id="phi-2",
            staleness=2,
            max_steps=10
        )
        
        trainer.train()
        
        # Verify logs
        with open(trainer.metrics.log_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 10
        # All logs should have staleness=2 (or clamped)
        for log in logs:
            assert log["staleness"] <= 2 + 5  # Within expected range
