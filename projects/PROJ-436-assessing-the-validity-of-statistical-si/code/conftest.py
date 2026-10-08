"""
Pytest configuration and fixtures for the llmXive research pipeline.
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the code directory to sys.path for tests."""
    code_dir = Path(__file__).parent
    sys.path.insert(0, str(code_dir))
    yield
    sys.path.remove(str(code_dir))

@pytest.fixture
def test_log_file(tmp_path):
    """Fixture to provide a temporary log file path."""
    log_path = tmp_path / "test_run.log"
    return str(log_path)

@pytest.fixture
def setup_test_logging(test_log_file):
    """Fixture to configure logging for tests."""
    from code import setup_logging
    logger = setup_logging(level=logging.DEBUG, log_file=test_log_file)
    yield logger
    # Cleanup: remove handlers to avoid pollution in subsequent tests
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

@pytest.fixture
def sample_config_dict():
    """Fixture providing a sample configuration dictionary for testing."""
    return {
        "dataset_id": 436,
        "missing_mechanism": "MCAR",
        "missing_rate": 0.1,
        "outcome_type": "continuous",
        "analysis_method": "t_test",
        "iterations": 100,
        "random_seed": 42
    }

@pytest.fixture
def small_dataset_path(tmp_path):
    """Fixture creating a small CSV file for testing data loading."""
    import pandas as pd
    data = {
        "treatment": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        "outcome": [1.2, 2.3, 1.5, 2.1, 1.8, 2.4, 1.1, 2.0, 1.6, 2.2],
        "age": [25, 30, 35, 40, 28, 32, 38, 42, 27, 33]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "small_dataset.csv"
    df.to_csv(path, index=False)
    return str(path)