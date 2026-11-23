"""
Test suite to verify that core dependencies are installed and importable.
"""
import pytest

def test_rdkit_import():
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError as e:
        pytest.fail(f"RDKit import failed: {e}")

def test_pandas_import():
    try:
        import pandas as pd
    except ImportError as e:
        pytest.fail(f"Pandas import failed: {e}")

def test_numpy_import():
    try:
        import numpy as np
    except ImportError as e:
        pytest.fail(f"Numpy import failed: {e}")

def test_sklearn_import():
    try:
        import sklearn
    except ImportError as e:
        pytest.fail(f"Scikit-learn import failed: {e}")

def test_datasets_import():
    try:
        from datasets import load_dataset
    except ImportError as e:
        pytest.fail(f"Datasets library import failed: {e}")

def test_huggingface_hub_import():
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as e:
        pytest.fail(f"Huggingface Hub import failed: {e}")

def test_pymatgen_import():
    try:
        import pymatgen
    except ImportError as e:
        pytest.fail(f"Pymatgen import failed: {e}")

def test_pycifrw_import():
    try:
        import PycifRW
    except ImportError as e:
        pytest.fail(f"PycifRW import failed: {e}")

def test_shap_import():
    try:
        import shap
    except ImportError as e:
        pytest.fail(f"SHAP import failed: {e}")