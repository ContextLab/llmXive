import pytest
import torch
import os
import sys
from unittest.mock import patch, MagicMock
from src.llmxive.trainer import AsyncRLTrainer
from src.llmxive.config import TrainingConfig, StalenessConfig
from src.llmxive.exceptions import ERR_CPU_LOAD_FAIL

class TestTrainerMemory:
    """Unit tests for memory monitoring functionality in trainer.py"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock training configuration"""
        config = MagicMock()
        config.model_id = "microsoft/phi-2"
        config.max_samples = 100
        config.max_steps = 100
        config.staleness_level = 1
        config.buffer_size = 10
        config.seed = 42
        return config
    
    @pytest.fixture
    def trainer(self, mock_config):
        """Create a trainer instance with mock config"""
        staleness_config = StalenessConfig(
            staleness_level=mock_config.staleness_level,
            buffer_size=mock_config.buffer_size
        )
        return AsyncRLTrainer(mock_config, staleness_config)
    
    def test_memory_check_returns_positive_value(self, trainer):
        """Test that memory check returns a positive float"""
        ram_usage = trainer._check_memory_usage()
        assert isinstance(ram_usage, float)
        assert ram_usage > 0
        assert ram_usage < 100  # Reasonable upper bound
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_memory_limit_enforcement_passes(self, mock_process, trainer):
        """Test that memory enforcement passes when under limit"""
        # Mock memory info to return 5GB usage
        mock_process.return_value.memory_info.return_value.rss = 5 * (1024 ** 3)
        
        # Should not raise
        trainer._enforce_memory_limit()
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_memory_limit_enforcement_fails(self, mock_process, trainer):
        """Test that memory enforcement raises when over limit"""
        # Mock memory info to return 7GB usage (above 6.5GB limit)
        mock_process.return_value.memory_info.return_value.rss = 7 * (1024 ** 3)
        
        with pytest.raises(ERR_CPU_LOAD_FAIL) as exc_info:
            trainer._enforce_memory_limit()
        
        assert "Memory usage" in str(exc_info.value)
        assert "exceeds limit" in str(exc_info.value)
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_peak_memory_logging(self, mock_process, trainer):
        """Test that peak memory is logged correctly"""
        # Mock memory info to return 5GB usage
        mock_process.return_value.memory_info.return_value.rss = 5 * (1024 ** 3)
        
        # Mock metrics to verify logging
        trainer.metrics = MagicMock()
        
        trainer._log_peak_memory(100)
        
        # Verify metrics logging
        trainer.metrics.log_metric.assert_called_once_with('peak_ram_gb', 5.0, 100)
    
    def test_max_memory_threshold(self, trainer):
        """Test that max memory threshold is set correctly"""
        assert trainer.max_memory_gb == 6.5
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_memory_check_during_training_step(self, mock_process, trainer):
        """Test that memory is checked during training step"""
        # Mock memory info to return 5GB usage
        mock_process.return_value.memory_info.return_value.rss = 5 * (1024 ** 3)
        
        # Mock model and data
        trainer.model = MagicMock()
        trainer.tokenizer = MagicMock()
        
        # Mock batch
        batch = {
            'input_ids': torch.randint(0, 1000, (2, 10)),
            'attention_mask': torch.ones(2, 10)
        }
        
        # Mock outputs
        trainer.model.return_value.loss = torch.tensor(0.5)
        
        # Mock metrics
        trainer.metrics = MagicMock()
        
        # Should complete without error
        result = trainer.train_step(batch, 0)
        
        assert 'loss' in result
        assert 'grad_norm' in result
        assert 'ram_usage' in result
    
    @patch('src.llmxive.trainer.psutil.Process')
    def test_memory_abort_during_training(self, mock_process, trainer):
        """Test that training aborts when memory exceeds limit"""
        # Mock memory to start low then go high
        mock_process.return_value.memory_info.side_effect = [
            5 * (1024 ** 3),  # Initial check
            7 * (1024 ** 3),  # During training step
        ]
        
        # Mock model and data
        trainer.model = MagicMock()
        trainer.tokenizer = MagicMock()
        
        # Mock batch
        batch = {
            'input_ids': torch.randint(0, 1000, (2, 10)),
            'attention_mask': torch.ones(2, 10)
        }
        
        # Mock metrics
        trainer.metrics = MagicMock()
        
        # Should raise ERR_CPU_LOAD_FAIL
        with pytest.raises(ERR_CPU_LOAD_FAIL):
            trainer.train_step(batch, 0)