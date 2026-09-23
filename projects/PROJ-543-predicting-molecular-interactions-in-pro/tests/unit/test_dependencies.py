"""
Unit tests to verify that all required dependencies are installed and importable.
"""
import pytest
import sys
import subprocess

def test_torch_import():
    """Verify PyTorch can be imported."""
    try:
        import torch
        assert torch.__version__ is not None
    except ImportError:
        pytest.fail("torch is not installed or not importable")

def test_torch_geometric_import():
    """Verify torch_geometric can be imported."""
    try:
        import torch_geometric
        assert torch_geometric.__version__ is not None
    except ImportError:
        pytest.fail("torch_geometric is not installed or not importable")

def test_rdkit_import():
    """Verify RDKit can be imported."""
    try:
        from rdkit import Chem
        assert Chem is not None
    except ImportError:
        pytest.fail("rdkit is not installed or not importable")

def test_datasets_import():
    """Verify datasets can be imported."""
    try:
        from datasets import load_dataset
        assert load_dataset is not None
    except ImportError:
        pytest.fail("datasets is not installed or not importable")

def test_scikit_learn_import():
    """Verify scikit-learn can be imported."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        assert RandomForestClassifier is not None
    except ImportError:
        pytest.fail("scikit-learn is not installed or not importable")

def test_pandas_import():
    """Verify pandas can be imported."""
    try:
        import pandas as pd
        assert pd.DataFrame is not None
    except ImportError:
        pytest.fail("pandas is not installed or not importable")

def test_pyyaml_import():
    """Verify pyyaml can be imported."""
    try:
        import yaml
        assert yaml.safe_load is not None
    except ImportError:
        pytest.fail("pyyaml is not installed or not importable")

def test_biopython_import():
    """Verify Biopython can be imported."""
    try:
        from Bio import Align
        assert Align is not None
    except ImportError:
        pytest.fail("biopython is not installed or not importable")

def test_install_deps_script_exists():
    """Verify the install_deps.py script exists."""
    import os
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "code", "install_deps.py")
    assert os.path.exists(script_path), f"install_deps.py not found at {script_path}"

def test_requirements_txt_exists():
    """Verify requirements.txt exists."""
    import os
    req_path = os.path.join(os.path.dirname(__file__), "..", "..", "code", "requirements.txt")
    assert os.path.exists(req_path), f"requirements.txt not found at {req_path}"