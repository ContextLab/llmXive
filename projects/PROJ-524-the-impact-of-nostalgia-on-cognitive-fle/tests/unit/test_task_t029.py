"""
Unit tests for code/task_t029_threshold_sensitivity.py.
Tests threshold sensitivity analysis logic.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t029_threshold_sensitivity import (
    is_borderline,
    analyze_threshold_sensitivity
)


class TestIsBorderline:
    def test_is_borderline_true(self):
        """Test borderline detection for p-value near 0.05."""
        assert is_borderline(0.049) is True
        assert is_borderline(0.051) is True
        assert is_borderline(0.05) is True

    def test_is_borderline_false(self):
        """Test non-borderline p-values."""
        assert is_borderline(0.01) is False
        assert is_borderline(0.10) is False
        assert is_borderline(0.001) is False

    def test_is_borderline_custom_threshold(self):
        """Test borderline detection with custom window."""
        # Default window is 0.01 (0.04 to 0.06)
        assert is_borderline(0.045) is True
        assert is_borderline(0.055) is True
        assert is_borderline(0.039) is False
        assert is_borderline(0.061) is False


class TestAnalyzeThresholdSensitivity:
    def test_analyze_threshold_sensitivity_stable(self):
        """Test sensitivity analysis with stable results."""
        results = [
            {'threshold': 0.01, 'is_significant': False, 'p_value': 0.15},
            {'threshold': 0.05, 'is_significant': False, 'p_value': 0.15},
            {'threshold': 0.10, 'is_significant': False, 'p_value': 0.15}
        ]

        analysis = analyze_threshold_sensitivity(results)

        assert analysis['is_stable'] is True
        assert analysis['sensitivity_flag'] == 'stable'

    def test_analyze_threshold_sensitivity_unstable(self):
        """Test sensitivity analysis with unstable results."""
        results = [
            {'threshold': 0.04, 'is_significant': False, 'p_value': 0.049},
            {'threshold': 0.05, 'is_significant': True, 'p_value': 0.049},
            {'threshold': 0.06, 'is_significant': True, 'p_value': 0.049}
        ]

        analysis = analyze_threshold_sensitivity(results)

        assert analysis['is_stable'] is False
        assert analysis['sensitivity_flag'] == 'sensitive_to_threshold'

    def test_analyze_threshold_sensitivity_borderline(self):
        """Test sensitivity analysis with borderline p-value."""
        results = [
            {'threshold': 0.04, 'is_significant': False, 'p_value': 0.049},
            {'threshold': 0.05, 'is_significant': True, 'p_value': 0.049},
            {'threshold': 0.10, 'is_significant': True, 'p_value': 0.049}
        ]

        analysis = analyze_threshold_sensitivity(results)

        assert analysis['borderline_p_value'] == 0.049
        assert analysis['sensitivity_flag'] == 'sensitive_to_threshold'

    def test_analyze_threshold_sensitivity_empty(self):
        """Test sensitivity analysis with empty results."""
        results = []

        analysis = analyze_threshold_sensitivity(results)

        assert analysis['is_stable'] is True
        assert analysis['sensitivity_flag'] == 'no_data'
