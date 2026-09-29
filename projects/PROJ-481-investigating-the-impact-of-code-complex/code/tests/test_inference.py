import sys
import os
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.inference import detect_hallucination

class TestHallucinationDetection(unittest.TestCase):
    
    def test_detect_hallucination_non_code(self):
        """Test detection of non-code output."""
        non_code = "This is just text, not code."
        self.assertTrue(detect_hallucination(non_code))
    
    def test_detect_hallucination_valid_code(self):
        """Test that valid code is not flagged."""
        valid_code = "def hello():\n    print('Hello')"
        self.assertFalse(detect_hallucination(valid_code))
    
    def test_detect_hallucination_empty(self):
        """Test empty string handling."""
        self.assertTrue(detect_hallucination(""))

def main():
    unittest.main()

if __name__ == '__main__':
    main()
