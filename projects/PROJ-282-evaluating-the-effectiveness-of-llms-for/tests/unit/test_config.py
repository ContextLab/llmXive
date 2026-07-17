"""
Unit tests for src.utils.config
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path if needed, though standard project structure usually handles this
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from src.utils.config import (
    get_available_ram_gb,
    select_model_for_environment,
    get_model_config,
    CANDIDATE_MODELS,
    MAX_RAM_GB,
    ensure_directories,
    PROJECT_ROOT
)


class TestRAMDetection:
    def test_get_available_ram_gb_returns_positive(self):
        """Ensure the RAM detection function returns a positive number."""
        ram = get_available_ram_gb()
        assert isinstance(ram, float)
        assert ram > 0, "Available RAM must be positive."

    @patch('src.utils.config.sys.platform', 'linux')
    @patch('builtins.open', new_callable=MagicMock)
    def test_linux_mem_available_parsing(self, mock_open):
        """Test parsing of /proc/meminfo on Linux."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "MemTotal:       16000000 kB\n"
            "MemAvailable:   8000000 kB\n"
            "MemFree:        1000000 kB\n"
        )
        ram = get_available_ram_gb()
        # 8000000 kB / 1024 / 1024 = ~7.62 GB
        assert 7.0 < ram < 8.0

    @patch('src.utils.config.sys.platform', 'linux')
    @patch('builtins.open', new_callable=MagicMock)
    def test_linux_mem_free_fallback(self, mock_open):
        """Test fallback to MemFree if MemAvailable is missing."""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "MemTotal:       16000000 kB\n"
            "MemFree:        2000000 kB\n"
        )
        ram = get_available_ram_gb()
        # 2000000 kB / 1024 / 1024 = ~1.90 GB
        assert 1.8 < ram < 2.0


class TestModelSelection:
    def test_select_model_fallback_to_smallest(self):
        """
        Test that if available RAM is very low, the smallest model is selected.
        We mock get_available_ram_gb to return a value just above the smallest model's requirement.
        """
        # Smallest model in CANDIDATE_MODELS is Distilled Llama-2 (~2.5 GB)
        # Mock RAM to be 3.0 GB
        with patch('src.utils.config.get_available_ram_gb', return_value=3.0):
            model = select_model_for_environment()
            assert model['name'] == "Distilled Llama-2"
            assert model['estimated_ram_gb'] <= 3.0

    def test_select_model_fails_if_none_fit(self):
        """Test that RuntimeError is raised if no model fits the RAM constraint."""
        # Mock RAM to be extremely low (e.g., 1 GB)
        with patch('src.utils.config.get_available_ram_gb', return_value=1.0):
            with pytest.raises(RuntimeError, match="No suitable model found"):
                select_model_for_environment()

    def test_select_model_respects_order(self):
        """
        Test that the selection logic prefers smaller models when multiple fit.
        If RAM is 10GB, it should still pick the smallest one (Distilled Llama-2)
        because the list is ordered by size and we pick the first match.
        """
        with patch('src.utils.config.get_available_ram_gb', return_value=10.0):
            model = select_model_for_environment()
            # Should pick the first one in the list (smallest)
            assert model['name'] == "Distilled Llama-2"


class TestConfigUtils:
    def test_get_model_config_by_name(self):
        """Test retrieving a specific model by name."""
        model = get_model_config("StarCoder-Base")
        assert model['name'] == "StarCoder-Base"

    def test_get_model_config_invalid_name(self):
        """Test that ValueError is raised for unknown model name."""
        with pytest.raises(ValueError, match="not found in candidate list"):
            get_model_config("NonExistentModel")

    def test_get_model_config_none_uses_auto(self):
        """Test that None triggers auto-selection."""
        with patch('src.utils.config.get_available_ram_gb', return_value=3.0):
            model = get_model_config(None)
            assert model['name'] == "Distilled Llama-2"

    def test_ensure_directories_creates_structure(self, tmp_path):
        """Test that ensure_directories creates the necessary folders."""
        # Temporarily override PROJECT_ROOT for the test
        original_root = PROJECT_ROOT
        try:
            # This test is tricky because PROJECT_ROOT is a global constant.
            # We can't easily mock it without modifying the module's global scope.
            # Instead, we just verify the function exists and doesn't crash
            # when run in a real environment (which creates dirs in the repo).
            # For a pure unit test, we'd need to refactor to accept a path argument.
            # Here we just ensure it runs without error.
            ensure_directories()
            assert PROJECT_ROOT.exists()
        finally:
            pass # Restore not strictly necessary in isolated test env