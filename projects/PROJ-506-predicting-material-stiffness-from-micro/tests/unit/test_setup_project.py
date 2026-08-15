import os
import sys
from pathlib import Path
import pytest

# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project import create_directories, verify_structure

class TestProjectSetup:
    def test_directories_created(self, tmp_path, monkeypatch):
        """Test that create_directories creates the expected folder structure."""
        monkeypatch.chdir(tmp_path)
        dirs = create_directories()
        
        expected_subdirs = [
            "code/data_generation",
            "code/training",
            "code/evaluation",
            "code/utils",
            "data/raw",
            "data/processed",
            "tests/unit",
            "tests/contract",
            "tests/integration",
            "specs/001-predict-stiffness-cnn/contracts",
        ]
        
        for sub in expected_subdirs:
            assert (tmp_path / sub).is_dir(), f"Directory {sub} was not created"

    def test_verify_structure_success(self, tmp_path, monkeypatch):
        """Test that verify_structure returns True after setup."""
        monkeypatch.chdir(tmp_path)
        # Run the setup logic
        create_directories()
        # Create the required init files manually for the test
        (tmp_path / "code").mkdir()
        (tmp_path / "code" / "__init__.py").touch()
        (tmp_path / "code" / "data_generation").mkdir()
        (tmp_path / "code" / "data_generation" / "__init__.py").touch()
        (tmp_path / "code" / "training").mkdir()
        (tmp_path / "code" / "training" / "__init__.py").touch()
        (tmp_path / "code" / "evaluation").mkdir()
        (tmp_path / "code" / "evaluation" / "__init__.py").touch()
        (tmp_path / "code" / "utils").mkdir()
        (tmp_path / "code" / "utils" / "__init__.py").touch()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").touch()
        (tmp_path / "tests" / "unit").mkdir()
        (tmp_path / "tests" / "unit" / "__init__.py").touch()
        (tmp_path / "tests" / "contract").mkdir()
        (tmp_path / "tests" / "contract" / "__init__.py").touch()
        (tmp_path / "tests" / "integration").mkdir()
        (tmp_path / "tests" / "integration" / "__init__.py").touch()
        
        # Create placeholder files
        (tmp_path / "code" / "main.py").touch()
        (tmp_path / "code" / "data_generation" / "generate_microstructures.py").touch()
        (tmp_path / "code" / "data_generation" / "compute_stiffness.py").touch()
        (tmp_path / "code" / "training" / "model.py").touch()
        (tmp_path / "code" / "training" / "train.py").touch()
        (tmp_path / "code" / "evaluation" / "stats_utils.py").touch()
        (tmp_path / "code" / "evaluation" / "evaluate.py").touch()
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "constitution_amendment_proposal.md").touch()

        success, msg = verify_structure()
        assert success is True, f"Verification failed: {msg}"
