import pytest
import numpy as np
import builtins
import pathlib

@pytest.fixture(scope="session")
def seed():
    """Fixed random seed for reproducibility."""
    return 42

@pytest.fixture
def tmp_path_fixture(tmp_path):
    """Provides a temporary directory for each test."""
    return tmp_path

# Inject Path into builtins for legacy tests that reference Path without import
builtins.Path = pathlib.Path
