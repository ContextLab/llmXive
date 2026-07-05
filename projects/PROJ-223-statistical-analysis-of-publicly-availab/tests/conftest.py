"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
import logging

# Ensure the project root is in the path so relative imports work during tests
# This assumes the tests are run from the project root: pytest
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging for tests to avoid silent failures
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@pytest.fixture(scope="session")
def data_dirs():
    """
    Provides paths to the data directories defined in the project structure.
    Returns a dictionary with keys: 'raw', 'processed', 'reports'.
    """
    # Construct paths relative to the project root
    base = os.path.join(project_root, "data")
    return {
        "raw": os.path.join(base, "raw"),
        "processed": os.path.join(base, "processed"),
        "reports": os.path.join(base, "reports"),
    }

@pytest.fixture(scope="session")
def code_dirs():
    """
    Provides paths to the code directories for validation.
    """
    base = os.path.join(project_root, "code")
    return {
        "base": base,
    }

@pytest.fixture
def sample_df():
    """
    Provides a minimal pandas DataFrame for unit testing logic.
    """
    import pandas as pd
    import numpy as np
    return pd.DataFrame({
        "severity": [1, 2, 3],
        "latitude": [40.0, 41.0, 42.0],
        "longitude": [-90.0, -91.0, -92.0],
        "timestamp": pd.to_datetime(["2022-01-01 12:00", "2022-01-01 13:00", "2022-01-01 14:00"])
    })