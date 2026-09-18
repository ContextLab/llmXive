"""Unit tests for trainer memory management."""
import pytest
import torch
import os
import sys
from unittest.mock import patch, MagicMock
from src.llmxive.trainer import AsyncRLTrainer

class TestTrainerMemory:
    """Tests for memory management in trainer."""
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_memory_check_pass(self, mock_process):
        """Test that memory check passes when under limit."""
        mock_process.return_value.memory_info.return_value.rss = 1 * 1024**3  # 1GB
        
        trainer = AsyncRLTrainer(model_id="phi-2", max_memory_gb=6.5)
        
        # Should not raise
        trainer._check_memory()
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_memory_check_fail(self, mock_process):
        """Test that memory check fails when over limit."""
        mock_process.return_value.memory_info.return_value.rss = 10 * 1024**3  # 10GB
        
        trainer = AsyncRLTrainer(model_id="phi-2", max_memory_gb=6.5)
        
        with pytest.raises(MemoryError):
            trainer._check_memory()
