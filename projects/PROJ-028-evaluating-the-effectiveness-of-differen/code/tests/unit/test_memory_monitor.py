"""
Unit tests for memory monitoring and model reloading logic in T017.
"""

import gc
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path if needed, though usually handled by pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.evaluation.runner import _check_and_handle_memory_pressure
from src.models.loader import get_current_ram_usage_gb, load_model, unload_model
from src.utils.logging import ResourceLogger

class TestMemoryMonitoring:
    @patch('src.evaluation.runner.get_current_ram_usage_gb')
    @patch('src.evaluation.runner.gc')
    @patch('src.evaluation.runner.unload_model')
    def test_memory_below_threshold_no_action(self, mock_unload, mock_gc, mock_ram):
        """Test that no action is taken when RAM is below threshold."""
        mock_ram.return_value = 4.0  # 4GB
        logger = MagicMock()
        
        result = _check_and_handle_memory_pressure(logger)
        
        assert result is False
        mock_gc.collect.assert_not_called()
        mock_unload.assert_not_called()
        logger.log_resource.assert_not_called()

    @patch('src.evaluation.runner.get_current_ram_usage_gb')
    @patch('src.evaluation.runner.gc')
    @patch('src.evaluation.runner.unload_model')
    def test_memory_above_threshold_triggers_action(self, mock_unload, mock_gc, mock_ram):
        """Test that GC and unload are triggered when RAM exceeds threshold."""
        # Simulate RAM above 6.5GB
        mock_ram.side_effect = [7.0, 5.0]  # First call: high, Second call (after unload): lower
        
        logger = MagicMock()
        
        result = _check_and_handle_memory_pressure(logger)
        
        assert result is True
        mock_gc.collect.assert_called_once()
        mock_unload.assert_called_once()
        # Verify logging
        assert logger.log_resource.call_count >= 2  # MEMORY_PRESSURE and MEMORY_RECOVERY

    @patch('src.models.loader.get_current_ram_usage_gb')
    def test_load_model_switches_to_fp16_on_high_ram(self, mock_ram):
        """Test that load_model attempts FP16 if RAM is high."""
        mock_ram.return_value = 7.0  # High RAM
        
        # We need to mock the actual model loading to avoid dependency on transformers
        with patch('src.models.loader.ResourceLogger'):
            model = load_model(precision="fp32")
            
            # Should have switched to fp16
            assert model["precision"] == "fp16"

    @patch('src.models.loader.get_current_ram_usage_gb')
    def test_unload_model_frees_memory(self, mock_ram):
        """Test that unload_model sets model to None."""
        mock_ram.return_value = 5.0
        
        # Load first
        with patch('src.models.loader.ResourceLogger'):
            load_model()
            assert model is not None # Should be loaded
            
            unload_model()
            
            # Check global state (if accessible) or just verify the call happened
            # Since _current_model is global in loader, we can check it
            from src.models.loader import _current_model
            assert _current_model is None