"""
Unit tests for the Artifact Logger (T022b).

Tests verify that the artifact logger correctly scans directories,
calculates hashes, and compiles logs without requiring full model training.
"""

import os
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
import sys
code_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
if code_root not in sys.path:
    sys.path.insert(0, code_root)

from utils.artifact_logger import (
    calculate_file_sha256,
    scan_directory_for_artifacts,
    load_json_artifact,
    compile_artifact_log,
    save_artifact_log
)


class TestCalculateSha256(unittest.TestCase):
    """Tests for SHA-256 calculation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Hello, World!")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_calculate_hash(self):
        """Test that hash is calculated correctly."""
        # Known hash for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = calculate_file_sha256(self.test_file)
        self.assertEqual(result, expected_hash)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with self.assertRaises(FileNotFoundError):
            calculate_file_sha256("non_existent_file.txt")


class TestScanDirectory(unittest.TestCase):
    """Tests for directory scanning."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create test structure
        os.makedirs(os.path.join(self.temp_dir, "subdir"))
        with open(os.path.join(self.temp_dir, "file1.pt"), 'w') as f:
            f.write("data")
        with open(os.path.join(self.temp_dir, "file2.json"), 'w') as f:
            f.write("{}")
        with open(os.path.join(self.temp_dir, "file3.txt"), 'w') as f:
            f.write("ignore")
        with open(os.path.join(self.temp_dir, "subdir", "nested.pt"), 'w') as f:
            f.write("data")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_scan_pt_files(self):
        """Test scanning for .pt files."""
        result = scan_directory_for_artifacts(self.temp_dir, ['.pt'])
        self.assertEqual(len(result), 2)
        paths = [r['relative_path'] for r in result]
        self.assertIn('file1.pt', paths)
        self.assertIn('subdir/nested.pt', paths)

    def test_scan_json_files(self):
        """Test scanning for .json files."""
        result = scan_directory_for_artifacts(self.temp_dir, ['.json'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relative_path'], 'file2.json')


class TestLoadJsonArtifact(unittest.TestCase):
    """Tests for JSON loading."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.valid_file = os.path.join(self.temp_dir, "valid.json")
        self.invalid_file = os.path.join(self.temp_dir, "invalid.json")
        
        with open(self.valid_file, 'w') as f:
            json.dump({"key": "value"}, f)
        with open(self.invalid_file, 'w') as f:
            f.write("{not valid json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_valid_json(self):
        """Test loading valid JSON."""
        result = load_json_artifact(self.valid_file)
        self.assertEqual(result, {"key": "value"})

    def test_load_invalid_json(self):
        """Test handling invalid JSON."""
        result = load_json_artifact(self.invalid_file)
        self.assertIsNone(result)

    def test_load_missing_file(self):
        """Test handling missing file."""
        result = load_json_artifact("non_existent.json")
        self.assertIsNone(result)


class TestCompileArtifactLog(unittest.TestCase):
    """Tests for compiling the full artifact log."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create mock files
        self.weights_dir = os.path.join(self.temp_dir, "weights")
        os.makedirs(self.weights_dir)
        with open(os.path.join(self.weights_dir, "best_model.pt"), 'w') as f:
            f.write("weights")

        self.metrics_file = os.path.join(self.temp_dir, "metrics.json")
        with open(self.metrics_file, 'w') as f:
            json.dump({"mse": 0.5}, f)

        self.predictions_file = os.path.join(self.temp_dir, "predictions.json")
        with open(self.predictions_file, 'w') as f:
            json.dump({"predictions": [1, 2, 3]}, f)

        self.comparison_file = os.path.join(self.temp_dir, "comparison.json")
        with open(self.comparison_file, 'w') as f:
            json.dump({"test": "result"}, f)

        self.attribution_file = os.path.join(self.temp_dir, "attribution.json")
        with open(self.attribution_file, 'w') as f:
            json.dump({"maps": []}, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_compile_log(self):
        """Test that compile_artifact_log creates a valid structure."""
        log_data = compile_artifact_log(
            weights_dir=self.weights_dir,
            metrics_file=self.metrics_file,
            predictions_file=self.predictions_file,
            comparison_file=self.comparison_file,
            attribution_file=self.attribution_file
        )

        self.assertIn("timestamp", log_data)
        self.assertTrue(log_data["fr_007_compliance"])
        self.assertIn("artifacts", log_data)
        self.assertIn("validation_summary", log_data)

        # Check validation summary
        summary = log_data["validation_summary"]
        self.assertTrue(summary["weights_found"])
        self.assertTrue(summary["metrics_loaded"])
        self.assertTrue(summary["predictions_loaded"])
        self.assertTrue(summary["comparison_loaded"])
        self.assertTrue(summary["attribution_loaded"])


class TestSaveArtifactLog(unittest.TestCase):
    """Tests for saving the artifact log."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "logs", "test_log.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_save_log(self):
        """Test saving log to file."""
        log_data = {"test": "data", "timestamp": "2023-01-01"}
        save_artifact_log(log_data, self.output_path)
        
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, log_data)


if __name__ == '__main__':
    unittest.main()