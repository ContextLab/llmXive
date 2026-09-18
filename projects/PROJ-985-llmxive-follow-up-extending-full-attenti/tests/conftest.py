"""
Pytest configuration and fixtures for the llmXive project.

This file provides shared fixtures and configuration for all test suites.
"""
import os
import sys
import pytest
import logging
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(autouse=True)
def setup_project_path():
    """Ensure the project root is in sys.path for imports."""
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
    # Cleanup if necessary
    if str(root) in sys.path:
        sys.path.remove(str(root))

@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent.parent / "data" / "test_data"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    return tmp_path

# Configure logging for tests
@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for test runs."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield
    # Reset logging if needed

# Skip markers for optional dependencies
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import datasets
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    import kenlm
    HAS_KENLM = True
except ImportError:
    HAS_KENLM = False

def pytest_runtest_setup(item):
    """Skip tests if required dependencies are missing."""
    if item.get_closest_marker("requires_gpu") and (not HAS_TORCH or not torch.cuda.is_available()):
        pytest.skip("GPU not available")
    
    if item.get_closest_marker("requires_datasets") and not HAS_DATASETS:
        pytest.skip("datasets library not installed")
    
    if item.get_closest_marker("requires_spacy") and not HAS_SPACY:
        pytest.skip("spaCy not installed")
    
    if item.get_closest_marker("requires_kenlm") and not HAS_KENLM:
        pytest.skip("kenlm not installed")