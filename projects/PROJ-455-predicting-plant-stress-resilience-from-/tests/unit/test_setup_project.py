import os
import shutil
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import main

class TestSetupProject:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate the project root."""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    def test_creates_all_directories(self, temp_project_root):
        """Verify that main() creates all required directories."""
        expected_dirs = [
            "code/data",
            "code/models",
            "code/analysis",
            "tests/unit",
            "tests/integration",
            "tests/contract",
            "tests/benchmark",
            "contracts",
            "data/raw",
            "data/processed",
            "data/results",
        ]

        # Run the setup function
        exit_code = main()

        assert exit_code == 0, "main() should return 0 on success"

        # Verify all directories exist
        for dir_name in expected_dirs:
            full_path = temp_project_root / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"Path {dir_name} is not a directory"

    def test_idempotent(self, temp_project_root):
        """Verify that running main() twice does not cause errors."""
        # Run twice
        exit_code_1 = main()
        exit_code_2 = main()

        assert exit_code_1 == 0
        assert exit_code_2 == 0

        # Verify structure is still valid
        assert (temp_project_root / "code").exists()
        assert (temp_project_root / "data").exists()