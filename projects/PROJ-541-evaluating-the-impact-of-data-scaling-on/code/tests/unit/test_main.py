import unittest
from pathlib import Path
import pandas as pd
import os

# Import the main function from your script
from code.main import ensure_directories, main

class TestMain(unittest.TestCase):

    def test_ensure_directories(self):
        """Test that ensure_directories creates the necessary directories."""
        ensure_directories()
        self.assertTrue(Path("code").exists())
        self.assertTrue(Path("data").exists())
        self.assertTrue(Path("results").exists())
        self.assertTrue(Path("logs").exists())

    def test_main_creates_csv(self):
      """Test that main() creates the simulation results CSV."""
      # Clean up any existing file
      if Path("results/simulation_results.csv").exists():
          Path("results/simulation_results.csv").unlink()

      main()
      self.assertTrue(Path("results/simulation_results.csv").exists())
      df = pd.read_csv("results/simulation_results.csv")
      self.assertGreater(len(df), 0)  # Check that the CSV is not empty



if __name__ == '__main__':
    unittest.main()