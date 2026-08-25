"""
Pytest configuration and fixtures for the llmXive project.

Provides shared fixtures and configuration for all test modules.
"""
import pytest
import os
import sys
from pathlib import Path

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def test_data_dir(project_root):
    """Return the test data directory."""
    return project_root / "tests" / "data"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Return a temporary output directory for test artifacts."""
    return tmp_path

@pytest.fixture
def sample_config(project_root):
    """Return a sample configuration dictionary."""
    return {
        "seed": 42,
        "streaming_chunk_size": 100,
        "optical_flow_threshold": 0.05,
        "vlm_confidence_threshold": 0.8,
        "latency_threshold_ms": 50,
    }
