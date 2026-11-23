"""
Integration tests for the pytest framework setup.
Verifies that the test framework can execute a simple integration scenario.
"""
import os
import sys
import pytest
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_integration_directory_exists():
    """Verify integration directory exists."""
    integration_dir = project_root / "tests" / "integration"
    assert integration_dir.exists()
    assert integration_dir.is_dir()

def test_utils_integration():
    """Test that utils functions work correctly in an integration context."""
    from utils import get_project_paths
    
    paths = get_project_paths()
    assert 'code' in paths
    assert 'data' in paths
    assert 'tests' in paths
    
    # Verify paths exist
    code_path = project_root / paths['code']
    data_path = project_root / paths['data']
    tests_path = project_root / paths['tests']
    
    assert code_path.exists()
    assert data_path.exists()
    assert tests_path.exists()

def test_data_models_integration():
    """Test that data models can be instantiated and used."""
    from data_models import PolymerRecord
    import numpy as np
    
    # Create a minimal valid record
    record = PolymerRecord(
        smiles="CC(=O)O",
        temperature=25.0,
        ph=7.0,
        uv=0.0,
        degradation_pathway="hydrolysis",
        source_id="test_001"
    )
    
    assert record.smiles == "CC(=O)O"
    assert record.temperature == 25.0
    assert record.degradation_pathway == "hydrolysis"
