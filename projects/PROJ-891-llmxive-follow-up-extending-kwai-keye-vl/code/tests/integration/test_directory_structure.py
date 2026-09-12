"""
Integration test to verify directory structure requirements.
"""
import os
import pytest
from pathlib import Path

def test_directory_structure_requirements():
    """Verify that all required directories exist."""
    root = Path(__file__).parent.parent.parent
    
    # Check unit test directory
    unit_dir = root / "code" / "tests" / "unit"
    assert unit_dir.exists(), f"Unit test directory missing: {unit_dir}"
    
    # Check integration test directory
    integration_dir = root / "code" / "tests" / "integration"
    assert integration_dir.exists(), f"Integration test directory missing: {integration_dir}"
    
    # Check __init__.py files for proper package structure
    assert (unit_dir / "__init__.py").exists(), "Missing __init__.py in tests/unit"
    assert (integration_dir / "__init__.py").exists(), "Missing __init__.py in tests/integration"
