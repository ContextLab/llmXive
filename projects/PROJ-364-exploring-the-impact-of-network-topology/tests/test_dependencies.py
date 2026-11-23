"""
Smoke test to verify all required dependencies are installed and importable.
This ensures T002 (Initialize Python 3.11 project with dependencies) is successful.
"""
import sys

def test_python_version():
    """Verify Python 3.11+ is being used."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version}"

def test_numpy():
    import numpy as np
    assert np.__version__ is not None

def test_pandas():
    import pandas as pd
    assert pd.__version__ is not None

def test_scipy():
    from scipy import spatial
    assert spatial is not None

def test_scikit_learn():
    import sklearn
    assert sklearn.__version__ is not None

def test_networkx():
    import networkx as nx
    assert nx.__version__ is not None

def test_matplotlib():
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for CI
    import matplotlib.pyplot as plt
    assert plt is not None

def test_seaborn():
    import seaborn as sns
    assert sns.__version__ is not None

def test_pyyaml():
    import yaml
    assert yaml is not None

def test_jsonschema():
    import jsonschema
    assert jsonschema.__version__ is not None