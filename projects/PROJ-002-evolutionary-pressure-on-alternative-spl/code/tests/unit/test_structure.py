import os
import pytest
from pathlib import Path

def test_unit_directory_exists():
    """Unit test verifying 'tests/unit' directory exists."""
    root = Path(__file__).resolve().parent.parent.parent
    unit_dir = root / "tests" / "unit"
    assert unit_dir.exists(), f"Unit directory missing: {unit_dir}"
    assert unit_dir.is_dir(), f"Unit path is not a directory: {unit_dir}"

def test_integration_directory_exists():
    """Unit test verifying 'tests/integration' directory exists."""
    root = Path(__file__).resolve().parent.parent.parent
    integration_dir = root / "tests" / "integration"
    assert integration_dir.exists(), f"Integration directory missing: {integration_dir}"
    assert integration_dir.is_dir(), f"Integration path is not a directory: {integration_dir}"

def test_contract_directory_exists():
    """Unit test verifying 'tests/contract' directory exists."""
    root = Path(__file__).resolve().parent.parent.parent
    contract_dir = root / "tests" / "contract"
    assert contract_dir.exists(), f"Contract directory missing: {contract_dir}"
    assert contract_dir.is_dir(), f"Contract path is not a directory: {contract_dir}"
