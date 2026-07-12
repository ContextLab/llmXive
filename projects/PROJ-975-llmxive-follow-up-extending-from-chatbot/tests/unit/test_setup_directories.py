import os
import pytest
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from setup_directories import create_project_structure

class TestSetupDirectories:
    """Tests for the directory creation logic."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to tmp_path to isolate test
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            result = create_project_structure()

            # Check counts
            assert result["created"] == 7
            assert result["existing"] == 0
            assert result["total"] == 7

            # Check specific directories exist
            required_dirs = [
                "data/raw",
                "data/results",
                "code",
                "tests/unit",
                "tests/contract",
                "contracts",
                "projects/PROJ-975-llmxive-follow-up-extending-from-chatbot"
            ]

            for dir_name in required_dirs:
                full_path = os.path.join(str(tmp_path), dir_name)
                assert os.path.isdir(full_path), f"Directory {dir_name} was not created."

        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories_gracefully(self, tmp_path):
        """Verify that the function handles pre-existing directories without error."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            # Pre-create one directory
            os.makedirs("data/raw", exist_ok=True)

            result = create_project_structure()

            # Should report 1 existing, 6 created
            assert result["existing"] == 1
            assert result["created"] == 6

            # Verify the pre-existing one is still there
            assert os.path.isdir("data/raw")

        finally:
            os.chdir(original_cwd)

    def test_nested_structure_created(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            result = create_project_structure()
            assert result["created"] == 7

            # Verify deep nesting
            assert os.path.isdir("data/raw")
            assert os.path.isdir("data/results")
            assert os.path.isdir("tests/unit")
            assert os.path.isdir("tests/contract")
            assert os.path.isdir("projects/PROJ-975-llmxive-follow-up-extending-from-chatbot")

        finally:
            os.chdir(original_cwd)
