"""
Contract test for T002: Data subdirectory permissions.

This test verifies that the data subdirectories are created with exactly
755 permissions as required by the task specification.
"""

import os
import stat
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_subdirs import create_data_subdirectories, verify_directories


class TestT002PermissionsContract:
    """Contract tests for T002 directory permissions."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exact_755_permissions(self):
        """
        Contract: All data subdirectories must have exactly 755 permissions.

        This is a hard requirement from T002 specification.
        """
        create_data_subdirectories(Path(self.test_dir))

        expected_paths = ["data/raw", "data/processed", "data/logs"]

        for rel_path in expected_paths:
            full_path = Path(self.test_dir) / rel_path
            assert full_path.exists(), f"Directory {rel_path} does not exist"

            # Get permissions in octal
            mode = full_path.stat().st_mode & 0o777
            assert mode == 0o755, (
                f"Directory {rel_path} has permissions {oct(mode)}, "
                f"but must be exactly 0o755 as per T002 specification"
            )

    def test_permissions_via_ls_command(self):
        """
        Contract: Verify permissions using system ls command.

        This provides independent verification that permissions are set correctly.
        """
        create_data_subdirectories(Path(self.test_dir))

        for subdir_name in ["raw", "processed", "logs"]:
            result = subprocess.run(
                ["ls", "-ld", str(Path(self.test_dir) / "data" / subdir_name)],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse permissions from ls output (e.g., "drwxr-xr-x")
            perms = result.stdout.split()[0]
            assert perms == "drwxr-xr-x", (
                f"Directory {subdir_name} has permissions {perms}, "
                f"expected drwxr-xr-x (755)"
            )

    def test_all_required_subdirectories_exist(self):
        """
        Contract: All three required subdirectories must exist.

        T002 requires: data/raw/, data/processed/, data/logs/
        """
        create_data_subdirectories(Path(self.test_dir))

        required = ["data/raw", "data/processed", "data/logs"]
        for rel_path in required:
            path = Path(self.test_dir) / rel_path
            assert path.exists(), f"Required directory {rel_path} is missing"
            assert path.is_dir(), f"{rel_path} is not a directory"

    def test_no_other_permissions_granted(self):
        """
        Contract: Ensure no additional permissions beyond 755 are set.

        This prevents accidental permission escalation.
        """
        create_data_subdirectories(Path(self.test_dir))

        subdir = Path(self.test_dir) / "data" / "raw"
        mode = subdir.stat().st_mode

        # 755 in binary: 111 101 101
        # Should NOT have: write for group, write for others
        assert not (mode & stat.S_IWGRP), "Group write permission should not be set"
        assert not (mode & stat.S_IWOTH), "Others write permission should not be set"

        # Should have: read, write, execute for owner; read, execute for group/others
        assert mode & stat.S_IRWXU == stat.S_IRWXU, "Owner should have rwx"
        assert (mode & stat.S_IRGRP) and (mode & stat.S_IXGRP), "Group should have rx"
        assert (mode & stat.S_IROTH) and (mode & stat.S_IXOTH), "Others should have rx"