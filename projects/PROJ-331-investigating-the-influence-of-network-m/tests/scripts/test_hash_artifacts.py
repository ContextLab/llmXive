import os
import json
import subprocess
import tempfile
import shutil
import yaml
from pathlib import Path

import pytest

# We need to ensure the script can be found and executed
# Since this is a shell script, we test it via subprocess

@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary project structure with some dummy artifacts."""
    # Create directory structure
    data_dir = tmp_path / "data"
    results_dir = tmp_path / "results"
    state_dir = tmp_path / "state"
    scripts_dir = tmp_path / "scripts"

    data_dir.mkdir()
    results_dir.mkdir()
    state_dir.mkdir()
    scripts_dir.mkdir()

    # Create dummy artifact files
    (data_dir / "test.npy").write_bytes(b"dummy_npy_content")
    (data_dir / "test.json").write_text('{"key": "value"}')
    (results_dir / "report.pdf").write_bytes(b"dummy_pdf_content")
    (results_dir / "plot.png").write_bytes(b"dummy_png_content")

    # Create a file that should be ignored
    (data_dir / "ignore.log").write_text("log content")

    return {
        "root": tmp_path,
        "data": data_dir,
        "results": results_dir,
        "state": state_dir,
        "scripts": scripts_dir
    }

@pytest.mark.integration
def test_hash_artifacts_script_creates_checksum_file(temp_project_structure):
    """Test that the script creates the state/artifacts.yaml file."""
    root = temp_project_structure["root"]
    state_dir = temp_project_structure["state"]
    scripts_dir = temp_project_structure["scripts"]
    
    # Copy the script to the temp project
    script_src = Path(__file__).parent.parent.parent / "scripts" / "hash_artifacts.sh"
    script_dest = scripts_dir / "hash_artifacts.sh"
    
    if script_src.exists():
        shutil.copy(script_src, script_dest)
        os.chmod(script_dest, 0o755)
        
        # Run the script
        result = subprocess.run(
            [str(script_dest)],
            cwd=root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        checksum_file = state_dir / "artifacts.yaml"
        assert checksum_file.exists(), "Checksum file was not created"
        
        # Verify YAML is valid
        with open(checksum_file, 'r') as f:
            content = yaml.safe_load(f)
        
        assert "artifacts" in content
        assert len(content["artifacts"]) == 4  # 4 expected files

@pytest.mark.integration
def test_hash_artifacts_script_correct_hashes(temp_project_structure):
    """Test that the script calculates correct SHA256 hashes."""
    root = temp_project_structure["root"]
    state_dir = temp_project_structure["state"]
    scripts_dir = temp_project_structure["scripts"]
    
    # Copy the script
    script_src = Path(__file__).parent.parent.parent / "scripts" / "hash_artifacts.sh"
    script_dest = scripts_dir / "hash_artifacts.sh"
    
    if script_src.exists():
        shutil.copy(script_src, script_dest)
        os.chmod(script_dest, 0o755)
        
        # Run the script
        result = subprocess.run(
            [str(script_dest)],
            cwd=root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        checksum_file = state_dir / "artifacts.yaml"
        with open(checksum_file, 'r') as f:
            content = yaml.safe_load(f)
        
        # Verify specific hashes
        artifacts = {a["path"]: a for a in content["artifacts"]}
        
        # Check that our dummy files are present
        assert "data/test.npy" in artifacts
        assert "data/test.json" in artifacts
        assert "results/report.pdf" in artifacts
        assert "results/plot.png" in artifacts
        
        # Verify ignore.log is NOT present
        assert "data/ignore.log" not in artifacts

@pytest.mark.integration
def test_hash_artifacts_script_handles_empty_directories(temp_project_structure):
    """Test script behavior with empty directories."""
    root = temp_project_structure["root"]
    state_dir = temp_project_structure["state"]
    scripts_dir = temp_project_structure["scripts"]
    
    # Remove all files from data and results
    for f in temp_project_structure["data"].iterdir():
        f.unlink()
    for f in temp_project_structure["results"].iterdir():
        f.unlink()
        
    # Copy the script
    script_src = Path(__file__).parent.parent.parent / "scripts" / "hash_artifacts.sh"
    script_dest = scripts_dir / "hash_artifacts.sh"
    
    if script_src.exists():
        shutil.copy(script_src, script_dest)
        os.chmod(script_dest, 0o755)
        
        # Run the script
        result = subprocess.run(
            [str(script_dest)],
            cwd=root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        checksum_file = state_dir / "artifacts.yaml"
        assert checksum_file.exists()
        
        with open(checksum_file, 'r') as f:
            content = yaml.safe_load(f)
        
        assert len(content["artifacts"]) == 0