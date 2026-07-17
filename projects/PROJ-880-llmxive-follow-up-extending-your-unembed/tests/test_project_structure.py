"""
Test to verify the project structure is correctly initialized.
"""
import os
import unittest

class TestProjectStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Determine root directory (parent of 'tests')
        cls.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "tests",
            "contracts",
        ]

    def test_directories_exist(self):
        """Verify all required directories exist."""
        missing = []
        for d in self.required_dirs:
            path = os.path.join(self.root, d)
            if not os.path.isdir(path):
                missing.append(d)
        
        self.assertEqual(len(missing), 0, f"Missing directories: {missing}")

    def test_code_package_exists(self):
        """Verify code/__init__.py exists."""
        path = os.path.join(self.root, "code", "__init__.py")
        self.assertTrue(os.path.isfile(path), "code/__init__.py not found")

    def test_tests_package_exists(self):
        """Verify tests/__init__.py exists."""
        path = os.path.join(self.root, "tests", "__init__.py")
        self.assertTrue(os.path.isfile(path), "tests/__init__.py not found")

if __name__ == "__main__":
    unittest.main()