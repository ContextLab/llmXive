import os

from setup_project_structure import DIRECTORIES, setup_directories

# Fix import path if running from tests/unit
# Assuming the script is in code/scripts/ or code/
# The import in the API surface says: from setup_project_structure import setup_directories, DIRECTORIES
# This implies the file is importable. We will mock the path if necessary in a real run,
# but here we assume the test runner sets up the path correctly or we import relative to code/.

# For the purpose of this artifact, we assume the file `code/setup_project_structure.py` exists
# and is importable. If the file is in `code/scripts/`, the import might need adjustment.
# Based on the API surface: `from setup_project_structure import setup_directories`
# This suggests the file is named `setup_project_structure.py` and is in the path.
# The artifact created above is at `code/scripts/setup_project_structure.py` but the API surface
# also lists `code/setup_project_structure.py`.
# Let's ensure the test imports from the correct location or adjust the import in the test.
# The API surface says: `import as: from setup_project_structure import setup_directories, main`
# This usually means the file is at the root of the code package or in the path.
# We will assume the test is run with `code/` in the PYTHONPATH.


class TestProjectStructure:
    """Tests for the project directory creation logic."""

    def test_setup_directories_creates_all_folders(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to temp directory to avoid polluting the actual project
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            created_dirs = setup_directories(tmp_path)

            # Verify count
            assert len(created_dirs) == len(DIRECTORIES)

            # Verify each directory exists
            for dir_name in DIRECTORIES:
                expected_path = tmp_path / dir_name
                assert expected_path.exists(), f"Directory {dir_name} was not created"
                assert expected_path.is_dir(), f"{dir_name} is not a directory"

        finally:
            os.chdir(original_cwd)

    def test_nested_directories_created(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            setup_directories(tmp_path)

            # Check specific nested paths
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "derived").exists()
            assert (tmp_path / "data" / "gold_standard").exists()
            assert (tmp_path / "specs" / "001-llmxive-follow-up-extending-arcane-do-ro").exists()
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Verify that running setup twice does not cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # First run
            setup_directories(tmp_path)

            # Second run should not raise and return same count
            created_dirs = setup_directories(tmp_path)
            assert len(created_dirs) == len(DIRECTORIES)
        finally:
            os.chdir(original_cwd)

    def test_specific_task_requirement_specs(self, tmp_path):
        """Verify the specific specs directory path required by T001."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            setup_directories(tmp_path)
            specs_path = tmp_path / "specs" / "001-llmxive-follow-up-extending-arcane-do-ro"
            assert (
                specs_path.exists()
            ), "The specific specs directory for this project was not created"
        finally:
            os.chdir(original_cwd)
