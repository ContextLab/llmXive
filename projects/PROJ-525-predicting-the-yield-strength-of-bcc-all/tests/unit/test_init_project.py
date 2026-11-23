"""
Unit tests for project initialization checks (T002).
"""
import sys
import unittest
from unittest.mock import patch, MagicMock
from code.init_project import check_python_version, check_dependencies, REQUIRED_PACKAGES

class TestInitProject(unittest.TestCase):

    def test_python_version_check_pass(self):
        """Test that check_python_version passes on valid version."""
        # Since we are running on the current interpreter, if this is 3.11+, it should pass
        # We can't easily mock sys.version to trigger a failure without complex setup,
        # so we just ensure it doesn't crash on success.
        try:
            check_python_version()
        except SystemExit as e:
            if e.code != 0:
                self.fail("check_python_version exited with error on valid environment")

    @patch('code.init_project.__import__')
    def test_check_dependencies_missing(self, mock_import):
        """Test that check_dependencies fails when a package is missing."""
        mock_import.side_effect = ImportError("No module named 'missing_pkg'")
        
        # We need to temporarily replace REQUIRED_PACKAGES to test a specific missing one
        # or just test that it raises SystemExit
        with patch('code.init_project.REQUIRED_PACKAGES', ['missing_pkg']):
            with self.assertRaises(SystemExit) as context:
                check_dependencies()
            self.assertEqual(context.exception.code, 1)

    @patch('code.init_project.__import__')
    def test_check_dependencies_all_present(self, mock_import):
        """Test that check_dependencies passes when all packages are present."""
        mock_import.return_value = MagicMock()
        
        with patch('code.init_project.REQUIRED_PACKAGES', ['fake_pkg']):
            try:
                check_dependencies()
            except SystemExit:
                self.fail("check_dependencies raised SystemExit when all packages present")

if __name__ == '__main__':
    unittest.main()