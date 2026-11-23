import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.dataset.curate_dataset import generate_puzzles, compute_checksum
from code.dataset.verifier import PuzzleVerifier

class TestCurateDataset(TestCase):
    """Tests for the dataset curation module."""

    def setUp(self):
        """Set up a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_puzzles_creates_files(self):
        """Test that generate_puzzles creates the expected number of files."""
        count = 5
        files = generate_puzzles(
            output_dir=self.output_path,
            count=count,
            min_size=5,
            max_size=10,
            seed=12345
        )
        
        self.assertEqual(len(files), count)
        self.assertTrue(all(f.exists() for f in files))

    def test_generated_files_are_valid_json(self):
        """Test that all generated files are valid JSON."""
        count = 3
        files = generate_puzzles(
            output_dir=self.output_path,
            count=count,
            min_size=5,
            max_size=10,
            seed=54321
        )
        
        verifier = PuzzleVerifier()
        
        for file_path in files:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Verify required fields exist
            self.assertIn("id", data)
            self.assertIn("type", data)
            self.assertIn("size", data)
            self.assertIn("initial_state", data)
            self.assertIn("constraints", data)
            
            # Verify checksum is present
            self.assertIn("checksum", data)
            
            # Verify the checksum matches the file content
            computed_checksum = compute_checksum(file_path)
            self.assertEqual(data["checksum"], computed_checksum)

    def test_checksum_computation_is_deterministic(self):
        """Test that checksum computation is deterministic."""
        count = 2
        files = generate_puzzles(
            output_dir=self.output_path,
            count=count,
            min_size=5,
            max_size=10,
            seed=99999
        )
        
        # Read first file and compute checksum
        file_path = files[0]
        checksum1 = compute_checksum(file_path)
        
        # Compute again
        checksum2 = compute_checksum(file_path)
        
        self.assertEqual(checksum1, checksum2)

    def test_manifest_is_created(self):
        """Test that a manifest file is created after generation."""
        count = 3
        generate_puzzles(
            output_dir=self.output_path,
            count=count,
            min_size=5,
            max_size=10,
            seed=11111
        )
        
        manifest_path = self.output_path / "manifest.json"
        self.assertTrue(manifest_path.exists())
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        self.assertIn("total_puzzles", manifest)
        self.assertEqual(manifest["total_puzzles"], count)
        self.assertIn("files", manifest)
        self.assertEqual(len(manifest["files"]), count)