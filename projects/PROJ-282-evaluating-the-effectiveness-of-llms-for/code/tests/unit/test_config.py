"""
Unit tests for src/utils/config.py
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import (
    get_available_ram_gb,
    select_model_by_ram,
    CANDIDATE_MODELS,
    MAX_RAM_GB,
    RuntimeConfig,
    get_config
)

class TestConfigRAMDetection:
    """Tests for RAM detection logic."""

    @patch('src.utils.config.psutil.virtual_memory')
    def test_get_available_ram_gb_success(self, mock_virtual_memory):
        """Test that get_available_ram_gb correctly calculates available RAM."""
        mock_mem = MagicMock()
        mock_mem.available = 8 * (1024 ** 3)  # 8 GB in bytes
        mock_virtual_memory.return_value = mock_mem

        ram_gb = get_available_ram_gb()
        
        assert isinstance(ram_gb, float)
        assert abs(ram_gb - 8.0) < 0.01

    @patch('src.utils.config.psutil.virtual_memory')
    def test_get_available_ram_gb_fallback(self, mock_virtual_memory):
        """Test fallback behavior when psutil fails."""
        mock_virtual_memory.side_effect = Exception("Mock failure")
        
        # Should not raise, but return a default value
        ram_gb = get_available_ram_gb()
        assert isinstance(ram_gb, float)
        assert ram_gb > 0

class TestDynamicModelSelection:
    """Tests for the dynamic model selection strategy."""

    def test_select_model_fits_exact(self):
        """Test selection when available RAM exactly matches a model requirement."""
        # Mock available RAM to be slightly less than the second model but more than the first
        # First model: 4.5 GB, Second: 5.5 GB
        # Set available to 5.0 GB -> should pick first
        with patch('src.utils.config.get_available_ram_gb', return_value=5.0):
            selected = select_model_by_ram()
            assert selected["name"] == "CodeLlamaB"
            assert selected["estimated_ram_gb"] == 4.5

    def test_select_model_larger_available(self):
        """Test selection when enough RAM for a larger model."""
        # Set available to 7.0 GB -> should pick the largest (distilled Llama-2: 6.5 GB)
        with patch('src.utils.config.get_available_ram_gb', return_value=7.5):
            selected = select_model_by_ram()
            # Should pick the largest that fits
            assert selected["name"] == "distilled Llama-2"

    def test_select_model_insufficient_ram(self):
        """Test that RuntimeError is raised when no model fits."""
        # Set available to 1.0 GB -> no model fits (smallest is 4.5 GB)
        with patch('src.utils.config.get_available_ram_gb', return_value=1.0):
            with pytest.raises(RuntimeError) as exc_info:
                select_model_by_ram()
            assert "Insufficient RAM" in str(exc_info.value)

    def test_model_ordering(self):
        """Verify that CANDIDATE_MODELS is ordered by estimated RAM (smallest first)."""
        rams = [m["estimated_ram_gb"] for m in CANDIDATE_MODELS]
        assert rams == sorted(rams), "CANDIDATE_MODELS must be ordered by estimated_ram_gb ascending"

class TestRuntimeConfig:
    """Tests for RuntimeConfig dataclass and factory."""

    def test_get_config_returns_valid_object(self):
        """Test that get_config returns a valid RuntimeConfig with a selected model."""
        # Mock RAM to ensure a model is selected
        with patch('src.utils.config.get_available_ram_gb', return_value=5.0):
            config = get_config()
            
            assert isinstance(config, RuntimeConfig)
            assert config.selected_model is not None
            assert "name" in config.selected_model
            assert "repo_id" in config.selected_model
            assert config.ram_cap_gb == MAX_RAM_GB
            assert config.random_seed == 42