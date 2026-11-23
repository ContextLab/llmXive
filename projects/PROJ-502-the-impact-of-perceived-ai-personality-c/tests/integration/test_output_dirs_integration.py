"""
Integration test for output directory creation.
Verifies the complete workflow of creating output directories.
"""
import os
import pytest
from pathlib import Path
import tempfile
import subprocess
import sys

def test_output_dirs_script_execution():
    """Test that the script can be executed successfully and creates directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        code_dir = temp_path / "code"
        code_dir.mkdir()
        
        # Copy the script to temp location
        script_content = (Path(__file__).parent.parent.parent / "code" / "create_output_dirs.py").read_text()
        (code_dir / "create_output_dirs.py").write_text(script_content)
        
        # Run the script
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            result = subprocess.run(
                [sys.executable, str(code_dir / "create_output_dirs.py")],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check exit code
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            
            # Verify directories were created
            output_base = temp_path / "output"
            figures_dir = output_base / "figures"
            reports_dir = output_base / "reports"
            
            assert output_base.exists(), "output directory should exist"
            assert figures_dir.exists(), "output/figures directory should exist"
            assert reports_dir.exists(), "output/reports directory should exist"
            
            # Verify .gitkeep files
            assert (figures_dir / ".gitkeep").exists()
            assert (reports_dir / ".gitkeep").exists()
            
        finally:
            os.chdir(original_cwd)

def test_output_dirs_persist_after_execution():
    """Test that created directories persist after script execution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        code_dir = temp_path / "code"
        code_dir.mkdir()
        
        script_content = (Path(__file__).parent.parent.parent / "code" / "create_output_dirs.py").read_text()
        (code_dir / "create_output_dirs.py").write_text(script_content)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            
            # First execution
            subprocess.run(
                [sys.executable, str(code_dir / "create_output_dirs.py")],
                capture_output=True,
                check=True
            )
            
            # Verify first run
            assert (temp_path / "output" / "figures").exists()
            
            # Second execution (should not fail)
            subprocess.run(
                [sys.executable, str(code_dir / "create_output_dirs.py")],
                capture_output=True,
                check=True
            )
            
            # Verify still exists
            assert (temp_path / "output" / "figures").exists()
            assert (temp_path / "output" / "reports").exists()
            
        finally:
            os.chdir(original_cwd)
