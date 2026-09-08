"""Pytest configuration and fixtures for llmXive."""
import pytest
import os
from pathlib import Path

@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return Path(__file__).resolve().parent.parent
