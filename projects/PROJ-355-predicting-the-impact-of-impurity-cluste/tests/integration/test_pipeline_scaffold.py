"""
Integration tests for the pipeline scaffold.

These tests verify that the basic pipeline structure is in place
and that modules can be imported and instantiated correctly.
"""
import pytest
from pathlib import Path
import sys

# Ensure imports work
from config import get_project_root
from validators import validate_citations


def test_project_structure_exists():
    """Verify that the expected project directory structure exists."""
    root = get_project_root()
    
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
    ]
    
    for dir_name in expected_dirs:
        dir_path = root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_core_modules_importable():
    """Verify that core modules can be imported without errors."""
    # Test imports that should exist based on the API surface
    try:
        from data.download import download_bulk_configs
        from data.gb_builder import build_gb_supercell
        from data.descriptors import compute_rdf_peak
        from validators import validate_citations
        from config import get_config_summary
    except ImportError as e:
        pytest.fail(f"Core module import failed: {e}")

def test_contract_files_exist():
    """Verify that contract schema files exist."""
    root = get_project_root()
    
    contracts = [
        "contracts/dataset.schema.yaml",
        "contracts/output.schema.yaml"
    ]
    
    for contract in contracts:
        contract_path = root / contract
        assert contract_path.exists(), f"Contract file {contract} does not exist"
        assert contract_path.stat().st_size > 0, f"Contract file {contract} is empty"
