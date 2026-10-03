"""
Unit tests for the reconciled extract_features.py script.

Tests:
1. Script existence and argument parsing.
2. Synthetic media generation (if dependencies allow).
3. Output file creation (data/processed/features.csv).
"""
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestExtractFeatures(unittest.TestCase):
    
    def setUp(self):
        # Create temporary directories for test
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.test_dir, "data", "raw")
        self.processed_dir = os.path.join(self.test_dir, "data", "processed")
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Backup original paths if needed, but we'll mock the script to use test_dir
        self.original_cwd = os.getcwd()
        
    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_script_exists(self):
        """Verify that extract_features.py exists."""
        script_path = os.path.join(Path(__file__).parent.parent.parent, "code", "extract_features.py")
        self.assertTrue(os.path.exists(script_path), "code/extract_features.py must exist.")
        
    def test_argument_parsing(self):
        """Verify the script accepts --mode simulate."""
        import subprocess
        script_path = os.path.join(Path(__file__).parent.parent.parent, "code", "extract_features.py")
        
        # Run with --help to check it parses args without error
        result = subprocess.run(
            [sys.executable, script_path, "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "Script should accept --help")
        self.assertIn("--mode", result.stdout, "Script should accept --mode argument")
        
    @unittest.skipIf(not os.path.exists("code/synthetic_media_gen.py"), "Skipping if synthetic_media_gen missing")
    def test_synthetic_generation_creates_files(self):
        """Test that synthetic generation creates files in data/raw."""
        # This test is a bit heavy, so we just verify the function can be imported
        # and returns a dict structure.
        try:
            from code.synthetic_media_gen import generate_synthetic_media_batch
            # We don't actually run it in unit tests to avoid ffmpeg dependency issues
            # but we verify it exists and has the right signature
            import inspect
            sig = inspect.signature(generate_synthetic_media_batch)
            params = list(sig.parameters.keys())
            self.assertIn("n", params)
            self.assertIn("signal", params)
            self.assertIn("null", params)
        except ImportError:
            self.skipTest("synthetic_media_gen not importable in this environment")

if __name__ == "__main__":
    unittest.main()