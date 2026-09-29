"""Pytest configuration and fixtures."""
import os
import pytest
from pathlib import Path

@pytest.fixture
def data_dir():
    """Provide the path to the data directory."""
    return Path("data")

@pytest.fixture
def code_dir():
    """Provide the path to the code directory."""
    return Path("code")