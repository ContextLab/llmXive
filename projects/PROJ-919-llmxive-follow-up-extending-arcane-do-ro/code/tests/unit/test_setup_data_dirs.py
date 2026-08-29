"""
Unit tests for the data directory setup script.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import the script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from setup_data_dirs import setup_directories

class TestDataDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock the project structure: temp_dir/code/scripts/
        self.script_dir = Path(self.temp_dir) / "code" / "scripts"
        self.script_dir.mkdir(parents=True)
        
        # Create a dummy script file to match __file__ behavior
        self.dummy_script = self.script_dir / "setup_data_dirs.py"
        self.dummy_script.write_text("pass")

        yield

        # Cleanup
        shutil.rmtree(self.temp_dir)

    def test_setup_directories_creates_structure(self):
        """Test that setup_directories creates the required folders."""
        # We need to monkeypatch the script path to point to our temp dir
        # Since the function uses __file__, we simulate it by changing the module's __file__
        import setup_data_dirs
        original_file = setup_data_dirs.__file__
        setup_data_dirs.__file__ = str(self.dummy_script)

        try:
            result = setup_directories()
            
            assert result is True
            
            # Verify directories exist
            project_root = self.script_dir.parent
            data_root = project_root / "data"
            artifacts_root = project_root / "artifacts"
            
            expected_dirs = [
                data_root / "raw",
                data_root / "derived",
                data_root / "gold_standard",
                artifacts_root
            ]
            
            for dir_path in expected_dirs:
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
                # Check for .gitkeep
                gitkeep = dir_path / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep not found in {dir_path}"
        finally:
            setup_data_dirs.__file__ = original_file

    def test_setup_directories_idempotent(self):
        """Test that running setup_directories twice doesn't fail."""
        import setup_data_dirs
        original_file = setup_data_dirs.__file__
        setup_data_dirs.__file__ = str(self.dummy_script)

        try:
            # Run twice
            result1 = setup_directories()
            result2 = setup_directories()
            
            assert result1 is True
            assert result2 is True
        finally:
            setup_data_dirs.__file__ = original_file