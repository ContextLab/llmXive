"""
Unit test to verify that the required test directory structure exists.
This ensures T001c is successfully completed.
"""
import os
import pytest
from pathlib import Path

def test_unit_directory_exists():
    """Verify tests/unit/ directory exists."""
    unit_dir = Path(__file__).parent
    assert unit_dir.exists(), f"Unit test directory {unit_dir} does not exist"
    assert unit_dir.is_dir(), f"{unit_dir} is not a directory"

def test_integration_directory_exists():
    """Verify tests/integration/ directory exists."""
    parent = Path(__file__).parent
    integration_dir = parent / "integration"
    assert integration_dir.exists(), f"Integration test directory {integration_dir} does not exist"
    assert integration_dir.is_dir(), f"{integration_dir} is not a directory"

def test_contract_directory_exists():
    """Verify tests/contract/ directory exists."""
    parent = Path(__file__).parent
    contract_dir = parent / "contract"
    assert contract_dir.exists(), f"Contract test directory {contract_dir} does not exist"
    assert contract_dir.is_dir(), f"{contract_dir} is not a directory"
