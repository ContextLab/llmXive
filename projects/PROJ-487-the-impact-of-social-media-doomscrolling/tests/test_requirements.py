"""
Test suite to verify dependencies are installed correctly.
"""
import unittest
import importlib
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestDependenciesInstalled(unittest.TestCase):
    """Verify that all required packages are importable."""

    REQUIRED_PACKAGES = [
        "pandas",
        "numpy",
        "statsmodels",
        "requests",
        "sklearn",  # scikit-learn imports as sklearn
        "matplotlib",
        "seaborn",
        "yaml",     # pyyaml imports as yaml
        "pytrends",
        "dotenv"    # python-dotenv imports as dotenv
    ]

    def test_all_packages_importable(self):
        """Test that all required packages can be imported."""
        missing = []
        for package in self.REQUIRED_PACKAGES:
            try:
                importlib.import_module(package)
            except ImportError:
                missing.append(package)

        if missing:
            self.fail(f"The following packages are missing: {missing}")

    def test_pandas_version(self):
        """Test that pandas is installed and has a version."""
        import pandas as pd
        self.assertTrue(hasattr(pd, "__version__"))
        self.assertGreater(len(pd.__version__), 0)

    def test_numpy_version(self):
        """Test that numpy is installed and has a version."""
        import numpy as np
        self.assertTrue(hasattr(np, "__version__"))
        self.assertGreater(len(np.__version__), 0)

    def test_statsmodels_available(self):
        """Test that statsmodels is available."""
        import statsmodels.api as sm
        self.assertIsNotNone(sm)

    def test_sklearn_available(self):
        """Test that scikit-learn is available."""
        import sklearn
        self.assertIsNotNone(sklearn)

    def test_matplotlib_available(self):
        """Test that matplotlib is available."""
        import matplotlib
        self.assertIsNotNone(matplotlib)

    def test_seaborn_available(self):
        """Test that seaborn is available."""
        import seaborn as sns
        self.assertIsNotNone(sns)

    def test_requests_available(self):
        """Test that requests is available."""
        import requests
        self.assertIsNotNone(requests)

    def test_yaml_available(self):
        """Test that pyyaml is available."""
        import yaml
        self.assertIsNotNone(yaml)

    def test_pytrends_available(self):
        """Test that pytrends is available."""
        import pytrends
        self.assertIsNotNone(pytrends)

if __name__ == "__main__":
    unittest.main()