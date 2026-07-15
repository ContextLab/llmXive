"""
Tests for Task T003: Verify that required dependencies are installed and importable.
"""
import importlib
import sys

REQUIRED_PACKAGES = [
    "pandas",
    "scipy",
    "statsmodels",
    "numpy",
    "requests",
    "yaml",
    "jsonschema",
    "vaderSentiment"
]

def test_all_dependencies_importable():
    """Ensure all required packages defined in requirements.txt can be imported."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    
    assert not missing, f"The following dependencies are missing: {', '.join(missing)}"

def test_pandas_version():
    """Verify pandas is installed and has a reasonable version."""
    import pandas as pd
    # Just check that it has a version attribute
    assert hasattr(pd, '__version__')

def test_scipy_stats():
    """Verify scipy.stats is accessible."""
    from scipy import stats
    assert hasattr(stats, 'norm')

def test_vadersentiment():
    """Verify vaderSentiment is accessible."""
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    assert SentimentIntensityAnalyzer is not None