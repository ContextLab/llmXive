import unittest
from pathlib import Path
import pandas as pd
import os
from code.main import ensure_directories, main

class TestMain(unittest.TestCase):
    def test_ensure_directories(self):
        """Test directory creation."""
        ensure_directories()
        # Check if directories exist
        self.assertTrue(Path("data").exists())
        self.assertTrue(Path("results").exists())

    def test_main_entry_point(self):
        """Test main entry point."""
        # This test would require mocking the simulation loop
        pass
