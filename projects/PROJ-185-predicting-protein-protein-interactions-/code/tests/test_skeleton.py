import os
import sys
import tempfile
import pytest
from pathlib import Path
from create_skeleton import main

class TestRepositorySkeleton:
    def test_creates_all_directories(self, tmp_path):
        # Create a temporary project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Run the skeleton creator
            exit_code = main()
            assert exit_code == 0
            
            # Verify directories exist relative to tmp_path
            required = ["src", "tests", "data", "results", "docs", "contracts", "specs", ".github/workflows"]
            for d in required:
                assert (tmp_path / d).is_dir(), f"Directory {d} was not created"
        finally:
            os.chdir(original_cwd)

    def test_idempotent(self, tmp_path):
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            main()
            exit_code = main() # Run again
            assert exit_code == 0
            assert (tmp_path / "src").is_dir()
        finally:
            os.chdir(original_cwd)
