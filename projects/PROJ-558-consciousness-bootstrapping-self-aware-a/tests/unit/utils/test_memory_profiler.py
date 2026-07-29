import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.memory_profiler import get_current_memory_mb, get_peak_memory_mb, get_peak_mb

class TestMemoryProfilerUtils(unittest.TestCase):
    
    def test_get_current_memory_mb_returns_positive(self):
        """Test that get_current_memory_mb returns a positive float."""
        mem = get_current_memory_mb()
        self.assertIsInstance(mem, float)
        self.assertGreater(mem, 0.0)

    def test_get_peak_memory_mb_returns_positive(self):
        """Test that get_peak_memory_mb returns a positive float."""
        mem = get_peak_memory_mb()
        self.assertIsInstance(mem, float)
        self.assertGreater(mem, 0.0)

    def test_get_peak_mb_extraction(self):
        """Test get_peak_mb helper with various result dicts."""
        # Normal case
        res = {"peak_memory_mb": 1024.5}
        self.assertEqual(get_peak_mb(res), 1024.5)
        
        # Missing key
        res = {"success": True}
        self.assertEqual(get_peak_mb(res), 0.0)
        
        # None value
        res = {"peak_memory_mb": None}
        self.assertEqual(get_peak_mb(res), 0.0)

if __name__ == "__main__":
    unittest.main()