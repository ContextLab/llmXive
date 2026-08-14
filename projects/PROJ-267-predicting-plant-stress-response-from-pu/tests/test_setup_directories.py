import unittest
from pathlib import Path
import code.setup_directories as setup_directories

class TestSetupDirectories(unittest.TestCase):

    def test_directory_creation(self):
        """Test that the directories are created."""
        dirs = [
            "code/data_ingestion",
            "code/modeling",
            "code/reporting",
            "code/utils",
            "tests",
            "data/raw",
            "data/processed",
            "results",
            "logs",
            "docs"
        ]

        for dir_path in dirs:
            self.assertTrue(Path(dir_path).exists(), f"Directory {dir_path} does not exist.")

if __name__ == '__main__':
    unittest.main()