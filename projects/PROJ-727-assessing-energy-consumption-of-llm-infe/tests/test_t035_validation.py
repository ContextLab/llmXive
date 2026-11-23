"""
Test for T035: Final Validation Logic.
This test verifies that the validation logic in code/final_validation.py works correctly
by checking against mock files.
"""
import os
import csv
import tempfile
import shutil
import unittest
from pathlib import Path

# We need to import the functions from final_validation
# Since the script is in code/, we might need to adjust sys.path if running directly
# But assuming the test runner adds the root to path or we import relative to project root
try:
    from code.final_validation import check_file_exists, check_csv_content, check_log_content
except ImportError:
    # Fallback for local execution if path isn't set up
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.final_validation import check_file_exists, check_csv_content, check_log_content

class TestT035Validation(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data", "processed")
        self.logs_dir = os.path.join(self.test_dir, "logs")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_check_file_exists_positive(self):
        """Test that check_file_exists returns True for existing non-empty file."""
        filepath = os.path.join(self.data_dir, "test.txt")
        with open(filepath, 'w') as f:
            f.write("content")
        
        # Temporarily patch the function to use our test dir? 
        # The function takes a relative path. We can't easily patch it to use a temp dir
        # without modifying the function signature or using absolute paths.
        # Instead, let's test the logic by creating a file in the expected relative location
        # and mocking the current working directory? 
        # Simpler: Just test the logic with absolute paths by creating a wrapper or 
        # testing the internal logic directly if possible.
        # Since the function uses Path(filepath), it resolves relative to CWD.
        # We will test by creating a file in a known relative path within a temp CWD?
        # Actually, the easiest way to test these functions in isolation is to 
        # create the files in the temp dir and pass absolute paths, 
        # but the function logic is simple enough that we can trust it if it works with absolute paths.
        
        # Let's just test with absolute paths for robustness in this unit test
        abs_filepath = os.path.join(self.data_dir, "test_abs.txt")
        with open(abs_filepath, 'w') as f:
            f.write("content")
        
        # The function doesn't care if it's relative or absolute, as long as it exists
        # But to be safe, let's just verify the function works with absolute paths
        # We need to be careful: the function in final_validation.py uses relative paths 
        # when called from main(). For unit testing, we test the helper functions.
        # The helper functions take a string path.
        
        # Test with absolute path
        result = check_file_exists(abs_filepath)
        self.assertTrue(result)

    def test_check_file_exists_negative_missing(self):
        """Test that check_file_exists returns False for missing file."""
        filepath = os.path.join(self.data_dir, "missing.txt")
        result = check_file_exists(filepath)
        self.assertFalse(result)

    def test_check_file_exists_negative_empty(self):
        """Test that check_file_exists returns False for empty file."""
        filepath = os.path.join(self.data_dir, "empty.txt")
        with open(filepath, 'w') as f:
            pass # Create empty file
        
        result = check_file_exists(filepath)
        self.assertFalse(result)

    def test_check_csv_content_positive(self):
        """Test check_csv_content with valid CSV."""
        csv_path = os.path.join(self.data_dir, "valid.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
            writer.writeheader()
            writer.writerow({'col1': 'val1', 'col2': 'val2'})
        
        result = check_csv_content(csv_path, ['col1', 'col2'])
        self.assertTrue(result)

    def test_check_csv_content_missing_columns(self):
        """Test check_csv_content with missing columns."""
        csv_path = os.path.join(self.data_dir, "missing_cols.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1'])
            writer.writeheader()
            writer.writerow({'col1': 'val1'})
        
        result = check_csv_content(csv_path, ['col1', 'col2'])
        self.assertFalse(result)

    def test_check_csv_content_empty_data(self):
        """Test check_csv_content with header but no data."""
        csv_path = os.path.join(self.data_dir, "empty_data.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1'])
            writer.writeheader()
        
        result = check_csv_content(csv_path, ['col1'])
        self.assertFalse(result)

    def test_check_log_content_positive(self):
        """Test check_log_content with valid log."""
        log_path = os.path.join(self.logs_dir, "pipeline.log")
        with open(log_path, 'w') as f:
            f.write("Pipeline completed in 120 seconds.\nDuration: 2 minutes.")
        
        result = check_log_content(log_path)
        self.assertTrue(result)

    def test_check_log_content_negative_missing(self):
        """Test check_log_content with missing file."""
        log_path = os.path.join(self.logs_dir, "missing.log")
        result = check_log_content(log_path)
        self.assertFalse(result)

    def test_check_log_content_negative_no_duration(self):
        """Test check_log_content with file but no duration info."""
        log_path = os.path.join(self.logs_dir, "no_duration.log")
        with open(log_path, 'w') as f:
            f.write("Just some text without duration.")
        
        result = check_log_content(log_path)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()