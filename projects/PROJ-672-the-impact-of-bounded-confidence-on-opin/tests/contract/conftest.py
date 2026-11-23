"""
Contract-specific test configuration.
Inherits from root conftest.py but can add contract-specific fixtures.
"""
import pytest
from pathlib import Path

# Import project root path from root conftest
from tests.conftest import project_root_path


@pytest.fixture
def contracts_dir():
    """Returns the path to the contracts directory."""
    return project_root_path / "code" / "contracts"
