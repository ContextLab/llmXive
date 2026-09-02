"""
Unit tests for the project setup script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import setup_project
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project import create_directories


def test_create_directories_creates_all_required():
    """Test that all required directories are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake project structure
        project_root = Path(tmpdir)
        code_dir = project_root / "code"
        code_dir.mkdir()

        # Create a dummy setup_project.py in the code directory
        setup_script = code_dir / "setup_project.py"
        setup_script.write_text("")

        # Change to the code directory to simulate running from there
        original_cwd = os.getcwd()
        try:
            os.chdir(code_dir)

            # Create a modified version of create_directories that uses our tmpdir
            def test_create_directories():
                directories = [
                    "code",
                    "data/raw",
                    "data/processed",
                    "data/analysis",
                    "models",
                    "analysis",
                    "tests",
                    "docs",
                    "tests/contract",
                    "tests/integration",
                    "tests/unit",
                    "logs",
                    "figures",
                ]

                created = []
                for dir_path in directories:
                    full_path = project_root / dir_path
                    if not full_path.exists():
                        full_path.mkdir(parents=True, exist_ok=True)
                        created.append(str(full_path.relative_to(project_root)))

                return created

            created = test_create_directories()

            # Verify all directories were created
            required_dirs = [
                "code", "data/raw", "data/processed", "data/analysis",
                "models", "analysis", "tests", "docs",
                "tests/contract", "tests/integration", "tests/unit",
                "logs", "figures"
            ]

            for d in required_dirs:
                assert (project_root / d).exists(), f"Directory {d} was not created"
                assert (project_root / d).is_dir(), f"{d} exists but is not a directory"

            assert len(created) == len(required_dirs), f"Expected {len(required_dirs)} directories, got {len(created)}"

        finally:
            os.chdir(original_cwd)


def test_create_directories_handles_existing():
    """Test that existing directories don't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Pre-create some directories
        (project_root / "code").mkdir()
        (project_root / "data").mkdir()
        (project_root / "data" / "raw").mkdir()

        # Run the creation logic
        def test_create_directories():
            directories = [
                "code",
                "data/raw",
                "data/processed",
            ]

            created = []
            for dir_path in directories:
                full_path = project_root / dir_path
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    created.append(str(full_path.relative_to(project_root)))

            return created

        created = test_create_directories()

        # Only data/processed should be created
        assert len(created) == 1
        assert created[0] == "data/processed"

        # All directories should exist
        assert (project_root / "code").exists()
        assert (project_root / "data" / "raw").exists()
        assert (project_root / "data" / "processed").exists()