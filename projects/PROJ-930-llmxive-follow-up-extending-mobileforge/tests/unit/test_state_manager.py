"""
Unit tests for the state manager (Constitution Principle III).
Tests verify checksum calculation, artifact registration, and verification.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import pytest

# We need to import the module. Since tests are at code/tests/unit,
# and utils is at code/utils, we add code to path.
import sys
from pathlib import Path

# Determine project root (parent of code/)
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.state_manager import (
    compute_sha256,
    register_artifact,
    verify_artifact,
    initialize_state_structure,
    STATE_DIR,
    CHECKSUMS_FILE,
    VERSIONS_FILE,
)


class TestStateManager(TestCase):
    def setUp(self):
        """
        Create a temporary directory structure for testing.
        We mock the STATE_DIR to avoid polluting the actual project state during tests.
        However, since the module uses global paths, we need to be careful.
        
        Strategy: 
        1. Create a temp dir.
        2. Monkey-patch the global STATE_DIR and file paths in the module.
        3. Run tests.
        4. Restore.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.original_state_dir = STATE_DIR
        self.original_checksums = CHECKSUMS_FILE
        self.original_versions = VERSIONS_FILE

        # We cannot easily reassign module-level globals if they are used in other functions
        # without reloading the module. Instead, we will test the logic that doesn't depend
        # on global path resolution, or we will create a test harness that mimics the behavior.
        
        # For this task, we will test the pure functions and the file I/O logic by
        # temporarily creating a fake state structure in a temp dir if possible,
        # or by testing the compute_sha256 function which is pure.
        
        # To properly test the registration, we need to patch the paths.
        # Since the module is already imported, we patch the globals in the module.
        import utils.state_manager as sm_module
        self.test_state_dir = Path(self.temp_dir) / "state"
        self.test_state_dir.mkdir()
        
        # Patch the module's globals
        sm_module.STATE_DIR = self.test_state_dir
        sm_module.CHECKSUMS_FILE = self.test_state_dir / "checksums.json"
        sm_module.VERSIONS_FILE = self.test_state_dir / "versions.json"

        # Re-run initialization to create empty files in temp dir
        initialize_state_structure()

    def tearDown(self):
        """Restore original paths and clean up temp dir."""
        import utils.state_manager as sm_module
        sm_module.STATE_DIR = self.original_state_dir
        sm_module.CHECKSUMS_FILE = self.original_checksums
        sm_module.VERSIONS_FILE = self.original_versions
        
        # Clean up temp dir
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_compute_sha256(self):
        """Test SHA256 calculation on a known string."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)

        try:
            # Known hash for "test data"
            expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
            result = compute_sha256(temp_path)
            self.assertEqual(result, expected)
        finally:
            temp_path.unlink()

    def test_compute_sha256_missing_file(self):
        """Test that compute_sha256 raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            compute_sha256(Path("/nonexistent/file.txt"))

    def test_register_artifact(self):
        """Test registering an artifact."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content")
            temp_path = Path(f.name)

        try:
            # Ensure state files exist in temp dir
            if not self.test_state_dir.exists():
                self.test_state_dir.mkdir()
            
            record = register_artifact(
                temp_path,
                task_id="T004",
                description="Test artifact",
                artifact_type="test"
            )

            self.assertEqual(record["task_id"], "T004")
            self.assertEqual(record["description"], "Test artifact")
            self.assertIn("checksum", record)
            self.assertTrue(record["checksum"].isalnum())

            # Verify file exists in state
            self.assertTrue(self.test_state_dir.exists())
            self.assertTrue(CHECKSUMS_FILE.exists())
        finally:
            temp_path.unlink()

    def test_verify_artifact_success(self):
        """Test verifying a valid artifact."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content")
            temp_path = Path(f.name)

        try:
            # Register first
            register_artifact(temp_path, "T004", "Test")
            
            # Verify should pass
            self.assertTrue(verify_artifact(temp_path))
        finally:
            temp_path.unlink()

    def test_verify_artifact_failure(self):
        """Test verifying an artifact that has been modified."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content")
            temp_path = Path(f.name)

        try:
            # Register
            register_artifact(temp_path, "T004", "Test")
            
            # Modify file
            with open(temp_path, "w") as f:
                f.write("modified content")
            
            # Verify should fail
            self.assertFalse(verify_artifact(temp_path))
        finally:
            temp_path.unlink()

    def test_register_missing_file(self):
        """Test that registering a missing file raises error."""
        with self.assertRaises(FileNotFoundError):
            register_artifact(Path("/nonexistent/file.txt"), "T004", "Test")
