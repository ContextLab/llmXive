"""
Unit tests for the update_state module.

Tests cover:
- SHA-256 hash computation
- Directory scanning
- State loading and saving
- Hash verification and change detection
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock
import sys
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.update_state import (
    compute_sha256,
    scan_directory,
    load_state,
    save_state,
    verify_hashes,
    main
)


class TestComputeSha256(TestCase):
    """Tests for the compute_sha256 function."""
    
    def test_compute_sha256_simple_file(self):
        """Test hash computation for a simple file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)
        
        try:
            # Compute expected hash
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            
            # Compute actual hash
            actual_hash = compute_sha256(temp_path)
            
            self.assertEqual(actual_hash, expected_hash)
        finally:
            temp_path.unlink()
    
    def test_compute_sha256_empty_file(self):
        """Test hash computation for an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = Path(f.name)
        
        try:
            expected_hash = hashlib.sha256(b"").hexdigest()
            actual_hash = compute_sha256(temp_path)
            self.assertEqual(actual_hash, expected_hash)
        finally:
            temp_path.unlink()
    
    def test_compute_sha256_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            compute_sha256(Path("nonexistent_file.txt"))


class TestScanDirectory(TestCase):
    """Tests for the scan_directory function."""
    
    def test_scan_directory_empty(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = scan_directory(Path(temp_dir))
            self.assertEqual(result, {})
    
    def test_scan_directory_with_files(self):
        """Test scanning a directory with tracked files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "test1.json").write_text("{}", suffix='.json')
            (temp_path / "test2.parquet").write_bytes(b"fake parquet")
            (temp_path / "test3.txt").write_text("text")
            (temp_path / "test4.csv").write_text("a,b\n1,2")
            (temp_path / "test5.yaml").write_text("key: value")
            
            # Create untracked file
            (temp_path / "test6.py").write_text("print('hello')")
            
            result = scan_directory(temp_path)
            
            # Should include all tracked extensions
            self.assertIn("test1.json", result)
            self.assertIn("test2.parquet", result)
            self.assertIn("test3.txt", result)
            self.assertIn("test4.csv", result)
            self.assertIn("test5.yaml", result)
            
            # Should exclude untracked extension
            self.assertNotIn("test6.py", result)
    
    def test_scan_directory_subdirectories(self):
        """Test scanning directories recursively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested structure
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "nested.json").write_text("{}")
            
            result = scan_directory(temp_path)
            
            # Should find file in subdirectory
            self.assertIn("subdir/nested.json", result)
    
    def test_scan_directory_nonexistent(self):
        """Test scanning a non-existent directory."""
        result = scan_directory(Path("nonexistent_dir"))
        self.assertEqual(result, {})


class TestLoadSaveState(TestCase):
    """Tests for load_state and save_state functions."""
    
    def test_save_and_load_state(self):
        """Test saving and loading state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.yaml"
            
            test_state = {
                "last_updated": "2023-01-01T00:00:00",
                "artifacts": {"file1.json": "abc123"},
                "pipeline_runs": [{"timestamp": "2023-01-01T00:00:00"}]
            }
            
            # Save state
            save_state(test_state, state_file)
            
            # Load state
            loaded_state = load_state(state_file)
            
            self.assertEqual(loaded_state, test_state)
    
    def test_load_nonexistent_state(self):
        """Test loading a non-existent state file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "nonexistent.yaml"
            
            result = load_state(state_file)
            
            # Should return default state
            self.assertIn("last_updated", result)
            self.assertIn("artifacts", result)
            self.assertIn("pipeline_runs", result)
            self.assertEqual(result["artifacts"], {})
            self.assertEqual(result["pipeline_runs"], [])
    
    def test_save_state_creates_directories(self):
        """Test that save_state creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "subdir" / "nested" / "state.yaml"
            
            test_state = {"test": "data"}
            save_state(test_state, state_file)
            
            self.assertTrue(state_file.exists())


class TestVerifyHashes(TestCase):
    """Tests for the verify_hashes function."""
    
    def test_verify_no_changes(self):
        """Test verification with no changes."""
        current = {"file1.json": "abc123", "file2.json": "def456"}
        previous = {"file1.json": "abc123", "file2.json": "def456"}
        
        changes = verify_hashes(current, previous)
        
        self.assertEqual(changes['added'], [])
        self.assertEqual(changes['modified'], [])
        self.assertEqual(changes['deleted'], [])
    
    def test_verify_added_files(self):
        """Test verification with added files."""
        current = {"file1.json": "abc123", "file3.json": "ghi789"}
        previous = {"file1.json": "abc123"}
        
        changes = verify_hashes(current, previous)
        
        self.assertEqual(changes['added'], ["file3.json"])
        self.assertEqual(changes['modified'], [])
        self.assertEqual(changes['deleted'], [])
    
    def test_verify_deleted_files(self):
        """Test verification with deleted files."""
        current = {"file1.json": "abc123"}
        previous = {"file1.json": "abc123", "file2.json": "def456"}
        
        changes = verify_hashes(current, previous)
        
        self.assertEqual(changes['added'], [])
        self.assertEqual(changes['modified'], [])
        self.assertEqual(changes['deleted'], ["file2.json"])
    
    def test_verify_modified_files(self):
        """Test verification with modified files."""
        current = {"file1.json": "newhash123"}
        previous = {"file1.json": "oldhash456"}
        
        changes = verify_hashes(current, previous)
        
        self.assertEqual(changes['added'], [])
        self.assertEqual(changes['modified'], ["file1.json"])
        self.assertEqual(changes['deleted'], [])
    
    def test_verify_mixed_changes(self):
        """Test verification with mixed changes."""
        current = {
            "file1.json": "abc123",  # unchanged
            "file2.json": "newhash",  # modified
            "file3.json": "ghi789"    # added
        }
        previous = {
            "file1.json": "abc123",  # unchanged
            "file2.json": "oldhash",  # modified
            "file4.json": "jkl012"    # deleted
        }
        
        changes = verify_hashes(current, previous)
        
        self.assertEqual(set(changes['added']), {"file3.json"})
        self.assertEqual(changes['modified'], ["file2.json"])
        self.assertEqual(changes['deleted'], ["file4.json"])


class TestMain(TestCase):
    """Tests for the main function."""
    
    @patch('code.update_state.scan_directory')
    @patch('code.update_state.load_state')
    @patch('code.update_state.save_state')
    def test_main_execution(self, mock_save, mock_load, mock_scan):
        """Test main function execution flow."""
        # Setup mocks
        mock_load.return_value = {
            "last_updated": None,
            "artifacts": {"old.json": "oldhash"},
            "pipeline_runs": []
        }
        mock_scan.return_value = {
            "data/raw/file1.json": "hash1",
            "models/model.json": "hash2"
        }
        
        # Run main
        main()
        
        # Verify scan_directory was called for each artifact directory
        self.assertEqual(mock_scan.call_count, len([
            Path("data/raw"),
            Path("data/processed"),
            Path("models"),
            Path("artifacts/reports"),
            Path("artifacts/figures"),
            Path("data")
        ]))
        
        # Verify load_state was called
        mock_load.assert_called_once()
        
        # Verify save_state was called with correct structure
        mock_save.assert_called_once()
        saved_state = mock_save.call_args[0][0]
        
        self.assertIn("last_updated", saved_state)
        self.assertIn("artifacts", saved_state)
        self.assertIn("pipeline_runs", saved_state)
        self.assertEqual(len(saved_state['pipeline_runs']), 1)
        self.assertIn("changes", saved_state['pipeline_runs'][0])
