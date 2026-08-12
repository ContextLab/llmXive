import os
import sys
import unittest
from pathlib import Path

# Add the code directory to the path for imports
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from utils.config import get_project_root, get_artifacts_dir

class TestTrainingStructure(unittest.TestCase):
    """Test cases for training directory structure."""

    def test_artifacts_directory_exists(self):
        """Test that the artifacts directory exists."""
        artifacts_dir = get_artifacts_dir()
        self.assertTrue(artifacts_dir.exists(), "Artifacts directory should exist")
        self.assertTrue(artifacts_dir.is_dir(), "Artifacts should be a directory")

    def test_training_subdirectories(self):
        """Test that training subdirectories can be created."""
        artifacts_dir = get_artifacts_dir()
        checkpoints_dir = artifacts_dir / "checkpoints"
        
        # Create checkpoints directory
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify creation
        self.assertTrue(checkpoints_dir.exists(), "Checkpoints directory should be created")
        self.assertTrue(checkpoints_dir.is_dir(), "Checkpoints should be a directory")

def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTrainingStructure)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)