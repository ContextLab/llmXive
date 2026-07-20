"""
Tests for the Final Sanity Check (T031).

Verifies that the sanity check script correctly identifies
missing files and validates plot content (if possible).
"""
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

class TestSanityCheck(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = os.path.join(self.temp_dir, 'processed')
        os.makedirs(self.processed_dir)
        
        # Mock the config to use our temp directory
        self.original_processed_dir = None
        if 'DATA_PROCESSED_DIR' in sys.modules.get('code.config', {}).__dict__:
            pass # We will patch the import

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('code.sanity_check.DATA_PROCESSED_DIR')
    @patch('code.sanity_check.validate_plot')
    def test_all_files_exist_and_valid(self, mock_validate, mock_dir):
        """Test that the check passes when all files exist and validate_plot returns True."""
        mock_dir.return_value = self.processed_dir
        mock_validate.return_value = True

        # Create dummy files
        for fname in ['energy_bar.png', 'tradeoff_scatter.png']:
            open(os.path.join(self.processed_dir, fname), 'w').close()

        import code.sanity_check as sc
        result = sc.main()
        
        self.assertEqual(result, 0)
        self.assertEqual(mock_validate.call_count, 2)

    @patch('code.sanity_check.DATA_PROCESSED_DIR')
    def test_missing_file_fails(self, mock_dir):
        """Test that the check fails if a file is missing."""
        mock_dir.return_value = self.processed_dir
        
        # Create only one file
        open(os.path.join(self.processed_dir, 'energy_bar.png'), 'w').close()
        # tradeoff_scatter.png is missing

        import importlib
        # Re-import to pick up the new mock_dir if needed, or just run logic
        # We need to reload the module to see the mock
        if 'code.sanity_check' in sys.modules:
            importlib.reload(sys.modules['code.sanity_check'])
        
        import code.sanity_check as sc
        result = sc.main()
        
        self.assertEqual(result, 1)

    @patch('code.sanity_check.DATA_PROCESSED_DIR')
    @patch('code.sanity_check.validate_plot')
    def test_invalid_content_fails(self, mock_validate, mock_dir):
        """Test that the check fails if validate_plot returns False."""
        mock_dir.return_value = self.processed_dir
        mock_validate.return_value = False

        # Create dummy files
        for fname in ['energy_bar.png', 'tradeoff_scatter.png']:
            open(os.path.join(self.processed_dir, fname), 'w').close()

        import importlib
        if 'code.sanity_check' in sys.modules:
            importlib.reload(sys.modules['code.sanity_check'])
        
        import code.sanity_check as sc
        result = sc.main()
        
        self.assertEqual(result, 1)
        mock_validate.assert_called()

if __name__ == '__main__':
    unittest.main()