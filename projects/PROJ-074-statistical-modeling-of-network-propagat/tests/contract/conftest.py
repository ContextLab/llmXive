"""Shared fixtures for contract tests."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def contracts_dir():
    """Return the contracts directory path."""
    return Path(__file__).parent.parent.parent / "contracts"