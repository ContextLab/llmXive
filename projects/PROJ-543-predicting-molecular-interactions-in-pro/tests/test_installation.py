"""
Test to verify that required dependencies are installed and importable.
"""
import pytest
import sys

# List of required packages to verify
REQUIRED_PACKAGES = [
    "torch",
    "torch_geometric",
    "rdkit",
    "datasets",
    "sklearn",  # scikit-learn imports as sklearn
    "pandas",
    "yaml",     # pyyaml imports as yaml
    "Bio",      # biopython imports as Bio
]

@pytest.mark.parametrize("package_name", REQUIRED_PACKAGES)
def test_package_import(package_name):
    """Test that each required package can be imported."""
    try:
        __import__(package_name)
    except ImportError as e:
        pytest.fail(f"Failed to import {package_name}: {e}")

def test_torch_geometric_availability():
    """Test that torch_geometric is properly installed and accessible."""
    try:
        import torch_geometric
        # Verify it has expected attributes
        assert hasattr(torch_geometric, 'data'), "torch_geometric.data not found"
        assert hasattr(torch_geometric, 'nn'), "torch_geometric.nn not found"
    except ImportError:
        pytest.fail("torch_geometric not properly installed")

def test_rdkit_availability():
    """Test that RDKit is properly installed and accessible."""
    try:
        from rdkit import Chem
        from rdkit import RDLogger
    except ImportError:
        pytest.fail("RDKit not properly installed")

def test_biopython_availability():
    """Test that Biopython is properly installed and accessible."""
    try:
        from Bio import SeqIO
        from Bio.PDB import PDBParser
    except ImportError:
        pytest.fail("Biopython not properly installed")

def test_datasets_availability():
    """Test that Hugging Face datasets is properly installed."""
    try:
        import datasets
        assert hasattr(datasets, 'load_dataset'), "load_dataset not found"
    except ImportError:
        pytest.fail("datasets not properly installed")