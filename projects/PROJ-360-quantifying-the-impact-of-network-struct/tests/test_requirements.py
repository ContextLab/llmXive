"""
Test suite to verify that all required dependencies are importable.
This validates the project initialization for T002.
"""
import sys
import importlib

REQUIRED_PACKAGES = [
    "pymatgen",
    "networkx",
    "sklearn",
    "pandas",
    "requests",
    "numpy",
    "statsmodels",
]

def test_dependencies_importable():
    """Verify that all core dependencies listed in requirements.txt can be imported."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    assert not missing, f"Missing required dependencies: {missing}"

def test_specific_modules():
    """Verify specific sub-modules often used in the pipeline are available."""
    # pymatgen
    import pymatgen.core
    assert hasattr(pymatgen.core, 'Structure')
    
    # networkx
    import networkx as nx
    assert hasattr(nx, 'Graph')
    
    # sklearn
    from sklearn.linear_model import LinearRegression
    assert LinearRegression is not None
    
    # pandas
    import pandas as pd
    assert hasattr(pd, 'DataFrame')
    
    # numpy
    import numpy as np
    assert hasattr(np, 'array')
    
    # statsmodels
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    assert variance_inflation_factor is not None