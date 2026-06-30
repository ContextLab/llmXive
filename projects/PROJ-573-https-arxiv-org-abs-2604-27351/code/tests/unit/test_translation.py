"""
Unit tests for the UnifiedTranslator class.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.translation import UnifiedTranslator


class TestUnifiedTranslator:
    """Tests for UnifiedTranslator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.translator = UnifiedTranslator(fidelity_threshold=0.7)

    def test_translate_timeseries_1d(self):
        """Test time-series translation with 1D array."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        text = self.translator.translate_timeseries(data, label_name="test_var")

        assert "Mean test_var" in text
        assert "max" in text
        assert "min" in text
        assert "std" in text
        assert "trend" in text

        # Verify specific values
        assert "3.0000" in text  # Mean
        assert "5.0000" in text  # Max
        assert "1.0000" in text  # Min

    def test_translate_timeseries_2d_single_col(self):
        """Test time-series translation with 2D array (single column)."""
        data = np.array([[1.0], [2.0], [3.0]])
        text = self.translator.translate_timeseries(data, label_name="col1")

        assert "Mean col1" in text

    def test_translate_timeseries_empty(self):
        """Test time-series translation with empty array."""
        data = np.array([])
        text = self.translator.translate_timeseries(data, label_name="empty")

        assert "No data" in text

    def test_translate_timeseries_dict_input(self):
        """Test time-series translation with dict input."""
        data = {"values": [10, 20, 30], "label": "dict_var"}
        text = self.translator.translate_timeseries(data)

        assert "Mean dict_var" in text

    def test_translate_tabular_pandas(self):
        """Test tabular translation with Pandas DataFrame."""
        try:
            import pandas as pd
            df = pd.DataFrame({
                "A": [1, 2, 3],
                "B": [4.5, 5.5, 6.5],
                "Label": [0, 1, 0]
            })
            text = self.translator.translate_tabular(df, label_column="Label")

            assert "Row 1" in text
            assert "Row 2" in text
            assert "Row 3" in text
            assert "Label" in text
            assert "A" in text
            assert "B" in text
        except ImportError:
            pytest.skip("Pandas not available")

    def test_translate_tabular_dict_of_lists(self):
        """Test tabular translation with dict of lists."""
        data = {
            "col1": [1, 2],
            "col2": ["a", "b"],
            "target": [0, 1]
        }
        text = self.translator.translate_tabular(data, label_column="target")

        assert "Row 1" in text
        assert "Row 2" in text
        assert "col1=1" in text
        assert "col2=a" in text

    def test_translate_tabular_list_of_dicts(self):
        """Test tabular translation with list of dicts."""
        data = [
            {"x": 1, "y": 2, "z": 0},
            {"x": 3, "y": 4, "z": 1}
        ]
        text = self.translator.translate_tabular(data, label_column="z")

        assert "Row 1" in text
        assert "x=1" in text
        assert "z=0" in text

    def test_translate_all_heterogeneous(self):
        """Test translation of mixed modalities."""
        ts_data = np.array([1.0, 2.0, 3.0])
        tab_data = {"A": [1, 2], "B": [3, 4]}

        modalities = {
            "timeseries": ts_data,
            "tabular": tab_data
        }

        text = self.translator.translate_all(modalities, label_column="B")

        assert "[TIMESERIES]" in text
        assert "[TABULAR]" in text
        assert "Mean" in text

    def test_translate_all_missing_modality(self):
        """Test translation with None values."""
        modalities = {
            "timeseries": np.array([1.0, 2.0]),
            "tabular": None,
            "text": "hello"
        }

        text = self.translator.translate_all(modalities)

        assert "[TIMESERIES]" in text
        assert "[TEXT]" in text
        assert "[TABULAR]" not in text  # Should be skipped

    def test_validate_translation_timeseries(self):
        """Test fidelity validation for time-series."""
        data = np.random.randn(100) * 10 + 50
        text = self.translator.translate_timeseries(data, label_name="test")

        score = self.translator.validate_translation(data, text)

        assert 0.0 <= score <= 1.0
        # Should be relatively high for valid translation
        assert score > 0.5

    def test_validate_translation_tabular(self):
        """Test fidelity validation for tabular data."""
        try:
            import pandas as pd
            df = pd.DataFrame({
                "A": range(10),
                "B": range(10, 20),
                "Label": [0, 1] * 5
            })
            text = self.translator.translate_tabular(df, label_column="Label")

            score = self.translator.validate_translation(df, text)

            assert 0.0 <= score <= 1.0
            assert score > 0.4  # Should be decent
        except ImportError:
            pytest.skip("Pandas not available")

    def test_validate_translation_low_fidelity(self):
        """Test fidelity validation with low quality text."""
        data = np.array([1.0, 2.0, 3.0])
        bad_text = "no data here"

        score = self.translator.validate_translation(data, bad_text)

        assert score < 0.5

    def test_translate_timeseries_trend_detection(self):
        """Test trend detection logic."""
        # Increasing trend
        increasing = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        text_inc = self.translator.translate_timeseries(increasing, label_name="trend")
        assert "trend = increasing" in text_inc

        # Decreasing trend
        decreasing = np.array([8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0])
        text_dec = self.translator.translate_timeseries(decreasing, label_name="trend")
        assert "trend = decreasing" in text_dec

        # Stable trend
        stable = np.array([5.0, 5.1, 4.9, 5.0, 5.0, 5.1, 4.9, 5.0])
        text_stable = self.translator.translate_timeseries(stable, label_name="trend")
        assert "trend = stable" in text_stable

    def test_translate_tabular_float_formatting(self):
        """Test that floats are formatted consistently."""
        try:
            import pandas as pd
            df = pd.DataFrame({
                "float_col": [1.23456789, 9.87654321]
            })
            text = self.translator.translate_tabular(df)

            # Should have 4 decimal places
            assert "1.2346" in text
            assert "9.8765" in text
        except ImportError:
            pytest.skip("Pandas not available")

    def test_translate_all_with_text_modality(self):
        """Test translation including raw text modality."""
        modalities = {
            "text": "This is a raw text input",
            "timeseries": np.array([1.0, 2.0])
        }

        text = self.translator.translate_all(modalities)

        assert "This is a raw text input" in text
        assert "[TEXT]" in text
        assert "[TIMESERIES]" in text

    def test_invalid_input_type(self):
        """Test handling of invalid input types."""
        with pytest.raises(ValueError):
            self.translator.translate_timeseries("invalid_string")

    def test_fidelity_threshold_config(self):
        """Test that fidelity threshold is respected."""
        low_threshold_translator = UnifiedTranslator(fidelity_threshold=0.1)
        high_threshold_translator = UnifiedTranslator(fidelity_threshold=0.99)

        data = np.array([1.0, 2.0, 3.0])
        text = self.translator.translate_timeseries(data, label_name="test")

        # Score should be same, but warning behavior differs
        score_low = low_threshold_translator.validate_translation(data, text)
        score_high = high_threshold_translator.validate_translation(data, text)

        assert score_low == score_high