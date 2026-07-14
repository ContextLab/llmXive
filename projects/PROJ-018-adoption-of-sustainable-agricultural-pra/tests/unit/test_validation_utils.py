import pytest
from pathlib import Path
import os
import sys
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from validate_quickstart import run_script, validate_outputs

class TestRunScript:
    def test_script_exists_and_runs(self, tmp_path):
        """Test that run_script returns True for a valid script"""
        # Create a dummy script that exits 0
        script = tmp_path / "dummy.py"
        script.write_text("import sys\nsys.exit(0)")
        
        result = run_script(script)
        assert result is True

    def test_script_not_found(self, tmp_path):
        """Test that run_script returns False for missing script"""
        fake_path = tmp_path / "nonexistent.py"
        result = run_script(fake_path)
        assert result is False

    def test_script_fails(self, tmp_path):
        """Test that run_script returns False for script with exit code != 0"""
        script = tmp_path / "fail.py"
        script.write_text("import sys\nsys.exit(1)")
        
        result = run_script(script)
        assert result is False

class TestValidateOutputs:
    def test_all_files_exist(self, tmp_path):
        """Test validation returns True when all files exist"""
        file1 = tmp_path / "file1.csv"
        file2 = tmp_path / "file2.yaml"
        file1.touch()
        file2.touch()

        files = ["file1.csv", "file2.yaml"]
        result = validate_outputs(files, tmp_path)
        assert result is True

    def test_missing_file(self, tmp_path):
        """Test validation returns False when a file is missing"""
        file1 = tmp_path / "file1.csv"
        file1.touch()

        files = ["file1.csv", "missing.yaml"]
        result = validate_outputs(files, tmp_path)
        assert result is False

    def test_empty_list(self, tmp_path):
        """Test validation returns True for empty list of files"""
        result = validate_outputs([], tmp_path)
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
