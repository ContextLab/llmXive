"""
Test suite to verify that all required dependencies in requirements.txt
can be imported successfully. This ensures the environment is set up correctly.
"""
import unittest
import importlib

REQUIRED_MODULES = [
    'pandas',
    'numpy',
    'scipy',
    'sklearn',  # scikit-learn imports as sklearn
    'yaml',     # pyyaml imports as yaml
    'requests',
    'biom',     # biom-format imports as biom
    'dotenv',   # python-dotenv imports as dotenv
]

class TestRequirements(unittest.TestCase):
    def test_all_dependencies_importable(self):
        """Verify that all packages listed in requirements.txt can be imported."""
        missing = []
        for module in REQUIRED_MODULES:
            try:
                importlib.import_module(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            self.fail(f"The following required dependencies are missing or failed to import: {missing}")

if __name__ == '__main__':
    unittest.main()