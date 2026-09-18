"""Integration test for synchronous training loop."""
import pytest
import torch
import json
import os
import tempfile
from pathlib import Path
from src.llmxive.trainer import AsyncRLTrainer
from src.llmxive.metrics import MetricsTracker

class TestSyncLoop:
    """Tests for synchronous (staleness=0) training loop."""
    
    def test_sync_loop_no_oom(self):
        """Test that sync loop completes without OOM."""
        # Use a small number of steps for testing
        trainer = AsyncRLTrainer(
            model_id="phi-2",
            staleness=0,
            max_steps=10,
            max_memory_gb=6.5
        )
        
        trainer.train()
        
        # Verify log file was created
        assert trainer.metrics.log_path.exists()
        
        # Verify log content
        with open(trainer.metrics.log_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 10
        assert all("reward" in log for log in logs)
        assert all("grad_norm" in log for log in logs)
    
    def test_sync_loop_staleness_zero(self):
        """Test that staleness=0 produces correct behavior."""
        trainer = AsyncRLTrainer(
            model_id="phi-2",
            staleness=0,
            max_steps=5
        )
        
        trainer.train()
        
        # Verify all steps have staleness=0
        with open(trainer.metrics.log_path, 'r') as f:
            logs = json.load(f)
        
        for log in logs:
            assert log["staleness"] == 0
