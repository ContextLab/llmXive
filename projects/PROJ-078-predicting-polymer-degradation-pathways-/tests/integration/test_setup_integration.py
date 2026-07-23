import os
import shutil
import tempfile
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import create_directories


class TestSetupIntegration:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_full_directory_structure_persists(self):
        """Integration test: Verify directory structure persists after function call."""
        create_directories()
        
        # Re-verify existence after function returns
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/reports",
            "tests",
            "state"
        ]
        
        for dir_name in expected_dirs:
            path = Path(self.temp_dir) / dir_name
            assert path.exists() and path.is_dir()

    def test_writing_to_created_directories(self):
        """Integration test: Verify we can write files to the created directories."""
        create_directories()
        
        # Try writing a dummy file to data/raw
        raw_file = Path(self.temp_dir) / "data" / "raw" / "test_file.txt"
        try:
            with open(raw_file, 'w') as f:
                f.write("test content")
            assert raw_file.exists()
            assert raw_file.read_text() == "test content"
        finally:
            if raw_file.exists():
                raw_file.unlink()
