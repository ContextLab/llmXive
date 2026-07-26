"""
Pytest configuration and fixtures for the molecular reactivity project.

This file sets up the test environment, ensuring that the project's
code directory is accessible and that necessary configurations are loaded.
"""
import os
import sys
import pytest

# Add the project root to the Python path
# This assumes the tests are run from the project root or via pytest with proper discovery
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure the 'code' directory is in the path
code_dir = os.path.join(project_root, 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Fixture to set up the test environment before any tests run.
    This ensures that the logging and configuration are initialized.
    """
    # Import config to ensure it's loaded
    from code.config import get_config
    config = get_config()
    
    # Log that tests are starting
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Test environment initialized.")
    
    yield
    
    # Teardown if necessary
    logger.info("Test environment teardown.")

@pytest.fixture
def sample_valid_smiles():
    """Fixture providing a list of valid SMILES strings for testing."""
    return [
        "C",
        "CC",
        "c1ccccc1",
        "CCO",
        "O=C=O",
        "[13CH4]",
        "[NH4+]",
    ]

@pytest.fixture
def sample_invalid_smiles():
    """Fixture providing a list of invalid SMILES strings for testing."""
    return [
        "",
        "   ",
        "C(C",
        "CC)",
        "INVALID",
        "C\x00C",
    ]