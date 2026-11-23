"""
Pytest configuration and fixtures.

This file contains shared fixtures and configuration for all tests.
"""
import pytest
import sys
import os

# Add src to path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add src to path for all tests."""
    src_path = os.path.join(os.path.dirname(__file__), "..", "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    yield
    # Cleanup not strictly necessary but good practice
    if src_path in sys.path:
        sys.path.remove(src_path)

@pytest.fixture
def sample_message():
    """Provide a sample message dictionary for testing."""
    return {
        "message_id": "test_001",
        "text": "Great job! 👏🎉",
        "emoji_present": True,
        "emoji_count": 2,
        "emoji_types": ["clapping hands", "party popper"],
        "text_length": 12,
        "punctuation_count": 2
    }

@pytest.fixture
def sample_analysis_result():
    """Provide a sample analysis result for testing."""
    return {
        "analysis_id": "test_analysis_001",
        "correlation_pearson": 0.65,
        "correlation_spearman": 0.62,
        "regression_beta": 0.58,
        "p_value": 0.0001,
        "significant": True,
        "sample_size": 1000
    }
