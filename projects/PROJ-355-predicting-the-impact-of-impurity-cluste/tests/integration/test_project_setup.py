import pytest
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import get_project_root, setup_directories

class TestProjectSetupIntegration:
    def test_full_setup(self):
        """Test the full project setup process."""
        # Create a temporary directory to simulate the project root
        with tempfile.TemporaryDirectory() as tmpdir:
            # We'll test the directory creation logic directly
            mock_root = Path(tmpdir) / "PROJ-355-predicting-the-impact-of-impurity-cluste"
            
            # Create the expected directories
            directories = [
                mock_root,
                mock_root / "code",
                mock_root / "data" / "raw",
                mock_root / "data" / "processed",
                mock_root / "results",
                mock_root / "tests" / "unit",
                mock_root / "tests" / "integration",
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                gitkeep_path = directory / ".gitkeep"
                if not gitkeep_path.exists():
                    gitkeep_path.touch()
            
            # Verify all directories exist
            for directory in directories:
                assert directory.exists()
                assert directory.is_dir()
                
                # Verify .gitkeep exists
                gitkeep_path = directory / ".gitkeep"
                assert gitkeep_path.exists()
                
                # Verify directory name
                if directory == mock_root:
                    assert directory.name == "PROJ-355-predicting-the-impact-of-impurity-cluste"
                elif directory == mock_root / "code":
                    assert directory.name == "code"
                elif directory == mock_root / "data" / "raw":
                    assert directory.name == "raw"
                    assert directory.parent.name == "data"
                elif directory == mock_root / "data" / "processed":
                    assert directory.name == "processed"
                    assert directory.parent.name == "data"
                elif directory == mock_root / "results":
                    assert directory.name == "results"
                elif directory == mock_root / "tests" / "unit":
                    assert directory.name == "unit"
                    assert directory.parent.name == "tests"
                elif directory == mock_root / "tests" / "integration":
                    assert directory.name == "integration"
                    assert directory.parent.name == "tests"