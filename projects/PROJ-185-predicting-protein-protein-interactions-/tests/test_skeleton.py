"""
Tests for the repository skeleton creation and verification.
Implements T001c logic: Verify repository skeleton directories exist after T001 execution.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from create_skeleton import main as create_main
from check_skeleton import missing_directories

class TestRepositorySkeleton:
    def test_create_skeleton_creates_dirs(self, tmp_path):
        """Test that create_skeleton creates the required directories."""
        # Change to temp dir to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Run the creation script
            exit_code = create_main()
            assert exit_code == 0

            # Verify directories exist
            required = [
                "src", "tests", "data", "results", "docs", "contracts",
                "scripts", "specs", "state", "figures", ".github/workflows"
            ]
            for d in required:
                assert (tmp_path / d).is_dir(), f"Directory {d} was not created"

            # Verify .gitkeep files exist
            for d in required:
                gitkeep = tmp_path / d / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep missing in {d}"

        finally:
            os.chdir(original_cwd)

    def test_check_skeleton_finds_missing(self, tmp_path):
        """Test that check_skeleton detects missing directories."""
        # Create a partial skeleton
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        missing = missing_directories(tmp_path)
        assert "data" in missing
        assert "results" in missing
        assert "docs" in missing

    def test_check_skeleton_all_present(self, tmp_path):
        """Test that check_skeleton passes when all dirs exist."""
        # Create full skeleton manually
        for d in ["src", "tests", "data", "results", "docs", "contracts",
                  "scripts", "specs", "state", "figures", ".github/workflows"]:
            (tmp_path / d).mkdir(parents=True)

        missing = missing_directories(tmp_path)
        assert len(missing) == 0

    def test_directories_exist(self, tmp_path):
        """
        T001c: Verify repository skeleton directories exist after T001 execution.
        This is the specific CI test requested in the task description.
        """
        # Simulate the state after T001 has run
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Execute T001 logic (create_skeleton)
            create_main()
            
            # Now verify the directories exist (the core of T001c)
            missing = missing_directories(tmp_path)
            
            # Assert no directories are missing
            assert len(missing) == 0, f"Repository skeleton incomplete. Missing directories: {missing}"
            
            # Explicitly check for the required set
            required_dirs = [
                "src", "tests", "data", "results", "docs", "contracts",
                "scripts", "specs", "state", "figures", ".github/workflows"
            ]
            for d in required_dirs:
                assert (tmp_path / d).is_dir(), f"Required directory '{d}' is missing after skeleton creation."
        
        finally:
            os.chdir(original_cwd)