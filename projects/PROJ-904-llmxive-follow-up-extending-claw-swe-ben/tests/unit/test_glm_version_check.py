"""
Unit tests for statsmodels version compatibility check in glm_analyzer.py.

Tests that the module raises a RuntimeError if statsmodels version is < 0.14.0.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
import statsmodels

def test_version_check_passes():
    """Test that the module loads successfully when statsmodels version is sufficient."""
    # This test passes if the module imports without error
    # The actual check happens at import time in glm_analyzer.py
    try:
        from analysis.glm_analyzer import check_statsmodels_version
        # If we get here, the version was sufficient
        assert True
    except RuntimeError as e:
        pytest.fail(f"Unexpected RuntimeError: {e}")

def test_version_check_raises_on_old_version():
    """Test that a RuntimeError is raised when statsmodels version is < 0.14.0."""
    # Mock the statsmodels version to be old
    with patch('analysis.glm_analyzer.statsmodels.__version__', '0.13.0'):
        with pytest.raises(RuntimeError) as exc_info:
            # We need to re-execute the check function
            from analysis.glm_analyzer import check_statsmodels_version
            check_statsmodels_version()
        
        assert "statsmodels version 0.13.0 is insufficient" in str(exc_info.value)
        assert "0.14.0" in str(exc_info.value)

def test_version_check_0_14_0_exact():
    """Test that version 0.14.0 passes the check."""
    with patch('analysis.glm_analyzer.statsmodels.__version__', '0.14.0'):
        try:
            from analysis.glm_analyzer import check_statsmodels_version
            check_statsmodels_version()
            assert True
        except RuntimeError:
            pytest.fail("Version 0.14.0 should pass the check")

def test_version_check_0_15_0():
    """Test that version 0.15.0 passes the check."""
    with patch('analysis.glm_analyzer.statsmodels.__version__', '0.15.0'):
        try:
            from analysis.glm_analyzer import check_statsmodels_version
            check_statsmodels_version()
            assert True
        except RuntimeError:
            pytest.fail("Version 0.15.0 should pass the check")