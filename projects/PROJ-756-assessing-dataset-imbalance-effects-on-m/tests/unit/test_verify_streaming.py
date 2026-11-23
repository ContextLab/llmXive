"""
Unit tests for T052: verify_streaming_strategy.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from verify_streaming_strategy import check_file, STREAMING_PATTERN, ANTI_PATTERNS

class TestStreamingVerification(unittest.TestCase):

    def test_streaming_pattern_match(self):
        """Test that the regex correctly identifies streaming=True"""
        valid_code = "ds = load_dataset('oqmd', streaming=True)"
        self.assertTrue(STREAMING_PATTERN.search(valid_code))

        valid_code2 = "load_dataset('aflow', split='train', streaming=True)"
        self.assertTrue(STREAMING_PATTERN.search(valid_code2))

        invalid_code = "load_dataset('oqmd', streaming=False)"
        self.assertFalse(STREAMING_PATTERN.search(invalid_code))

    def test_anti_pattern_list_detection(self):
        """Test that anti-patterns are detected"""
        for pattern in ANTI_PATTERNS:
            # Test a known anti-pattern string
            test_str = "list(dataset)" if "list" in pattern.pattern else "dataset[:]"
            if "list" in pattern.pattern:
                test_str = "list(dataset)"
            elif "to_pandas" in pattern.pattern:
                test_str = "dataset.to_pandas()"
            elif "np.array" in pattern.pattern:
                test_str = "np.array(dataset)"
            
            self.assertTrue(pattern.search(test_str), f"Failed to detect: {pattern.pattern}")

    def test_check_file_missing(self):
        """Test behavior when file is missing"""
        compliant, streaming, anti = check_file("non_existent_file.py")
        self.assertFalse(compliant)
        self.assertEqual(len(anti), 1)
        self.assertIn("File missing", anti[0])

    def test_check_file_compliant_streaming(self):
        """Test a compliant file with streaming"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from datasets import load_dataset\n")
            f.write("ds = load_dataset('test', streaming=True)\n")
            f.write("for row in ds:\n")
            f.write("    pass\n")
            temp_path = f.name

        try:
            compliant, streaming, anti = check_file(temp_path)
            self.assertTrue(compliant)
            self.assertTrue(len(streaming) > 0)
            self.assertEqual(len(anti), 0)
        finally:
            os.unlink(temp_path)

    def test_check_file_anti_pattern(self):
        """Test detection of anti-patterns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from datasets import load_dataset\n")
            f.write("ds = load_dataset('test', streaming=True)\n")
            f.write("data = list(ds)\n") # Anti-pattern
            temp_path = f.name

        try:
            compliant, streaming, anti = check_file(temp_path)
            self.assertFalse(compliant)
            self.assertTrue(len(anti) > 0)
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
