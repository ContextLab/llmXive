"""
Unit tests for ConfigurableXAIWrapper (T013b).
"""
import pytest
from unittest.mock import patch, MagicMock

from simulator.xai_wrapper import ConfigurableXAIWrapper, RuleBasedXAI, SHAPWrapper, LIMEWrapper
from simulator.interfaces.explainable import XAIOverlay


class TestRuleBasedXAI:
    """Tests for the rule-based fallback implementation."""

    def test_generate_overlay_valid_difficulty(self):
        """Test overlay generation with valid difficulty."""
        algo = RuleBasedXAI()
        overlay = algo.generate_overlay(task_difficulty=0.5, seed=42)

        assert isinstance(overlay, XAIOverlay)
        assert overlay.algorithm == "rule_based"
        assert 0.0 <= overlay.opacity <= 1.0
        assert len(overlay.regions) > 0
        assert "explanation_text" in overlay.explanation_text

    def test_generate_overlay_boundary_values(self):
        """Test overlay generation with boundary difficulty values."""
        algo = RuleBasedXAI()

        # Test difficulty = 0.0
        overlay_low = algo.generate_overlay(task_difficulty=0.0, seed=42)
        assert overlay_low.opacity >= 0.2  # Base opacity

        # Test difficulty = 1.0
        overlay_high = algo.generate_overlay(task_difficulty=1.0, seed=42)
        assert overlay_high.opacity <= 1.0
        assert overlay_high.opacity >= overlay_low.opacity

    def test_generate_overlay_clamping(self):
        """Test that difficulty values outside [0, 1] are clamped."""
        algo = RuleBasedXAI()

        # Negative difficulty
        overlay_neg = algo.generate_overlay(task_difficulty=-0.5, seed=42)
        assert overlay_neg.opacity == algo.generate_overlay(task_difficulty=0.0, seed=42).opacity

        # Over 1.0 difficulty
        overlay_high = algo.generate_overlay(task_difficulty=2.0, seed=42)
        assert overlay_high.opacity == algo.generate_overlay(task_difficulty=1.0, seed=42).opacity


class TestConfigurableXAIWrapper:
    """Tests for the main wrapper class."""

    def test_init_default_algorithm(self):
        """Test initialization with default algorithm."""
        wrapper = ConfigurableXAIWrapper()
        assert wrapper.get_current_algorithm() == "rule_based"

    def test_init_valid_algorithms(self):
        """Test initialization with valid algorithm names."""
        for algo_name in ["rule_based", "shap", "lime"]:
            wrapper = ConfigurableXAIWrapper(algorithm=algo_name)
            assert wrapper.get_current_algorithm() == algo_name

    def test_init_invalid_algorithm_raises(self):
        """Test initialization with invalid algorithm name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown algorithm"):
            ConfigurableXAIWrapper(algorithm="invalid_algo")

    def test_generate_overlay(self):
        """Test overlay generation through the wrapper."""
        wrapper = ConfigurableXAIWrapper()
        overlay = wrapper.generate_overlay(task_difficulty=0.7, seed=123)

        assert isinstance(overlay, XAIOverlay)
        assert overlay.opacity > 0

    def test_set_algorithm_dynamic_switch(self):
        """Test switching algorithm at runtime."""
        wrapper = ConfigurableXAIWrapper(algorithm="rule_based")
        assert wrapper.get_current_algorithm() == "rule_based"

        # Switch to another (even if it falls back)
        wrapper.set_algorithm("shap")
        # The active algorithm might be 'shap' or 'rule_based' (fallback)
        assert wrapper.get_current_algorithm() in ["shap", "rule_based"]

    def test_set_algorithm_invalid(self):
        """Test setting an invalid algorithm raises ValueError."""
        wrapper = ConfigurableXAIWrapper()
        with pytest.raises(ValueError, match="Unknown algorithm"):
            wrapper.set_algorithm("nonexistent")


class TestSHAPWrapper:
    """Tests for SHAPWrapper (with mocking)."""

    @patch('importlib.import_module')
    def test_shap_available(self, mock_import):
        """Test behavior when SHAP is available."""
        mock_shap = MagicMock()
        mock_import.return_value = mock_shap

        wrapper = SHAPWrapper()
        assert wrapper._available is True

        overlay = wrapper.generate_overlay(task_difficulty=0.5, seed=42)
        assert overlay.algorithm == "shap"
        mock_import.assert_called_once_with("shap")

    @patch('importlib.import_module')
    def test_shap_unavailable_fallback(self, mock_import):
        """Test fallback to rule-based when SHAP is not available."""
        mock_import.side_effect = ImportError("No module named 'shap'")

        wrapper = SHAPWrapper()
        assert wrapper._available is False

        overlay = wrapper.generate_overlay(task_difficulty=0.5, seed=42)
        # Should fallback to rule_based behavior
        assert overlay.algorithm == "rule_based"


class TestLIMEWrapper:
    """Tests for LIMEWrapper (with mocking)."""

    @patch('importlib.import_module')
    def test_lime_available(self, mock_import):
        """Test behavior when LIME is available."""
        mock_lime = MagicMock()
        mock_import.return_value = mock_lime

        wrapper = LIMEWrapper()
        assert wrapper._available is True

        overlay = wrapper.generate_overlay(task_difficulty=0.5, seed=42)
        assert overlay.algorithm == "lime"
        mock_import.assert_called_once_with("lime")

    @patch('importlib.import_module')
    def test_lime_unavailable_fallback(self, mock_import):
        """Test fallback to rule-based when LIME is not available."""
        mock_import.side_effect = ImportError("No module named 'lime'")

        wrapper = LIMEWrapper()
        assert wrapper._available is False

        overlay = wrapper.generate_overlay(task_difficulty=0.5, seed=42)
        # Should fallback to rule_based behavior
        assert overlay.algorithm == "rule_based"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])