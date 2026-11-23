"""
Unit tests for T005d: Project State Generation.

Verifies that the project state YAML is generated correctly,
contains valid hashes for configuration files, and respects
the dependency on Git initialization.
"""
import os
import sys
import tempfile
import shutil
import yaml
import subprocess
import hashlib
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.generate_project_state import compute_file_hash, PROJECT_ID, CONFIG_FILES

def test_compute_file_hash_existing_file():
    """Test that compute_file_hash correctly hashes an existing file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        file_hash = compute_file_hash(temp_path)
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert file_hash == expected_hash
    finally:
        temp_path.unlink()

def test_compute_file_hash_missing_file():
    """Test that compute_file_hash raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/file.txt"))

def test_project_state_generation_with_git(tmp_path):
    """Test that project state is generated correctly when git is initialized."""
    # Setup temporary project directory
    os.chdir(tmp_path)
    
    # Create .git directory (simulating T005c)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    
    # Create dummy config files
    for config_file in CONFIG_FILES:
        (tmp_path / config_file).write_text(f"# Content of {config_file}\n")
    
    # Run the script
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project_state.py"
    # We need to run it in the context where PROJECT_ROOT is correct
    # Since the script uses __file__ to determine root, we can run it directly
    import subprocess
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Verify output file exists
    state_dir = tmp_path / "state" / "projects"
    output_file = state_dir / f"{PROJECT_ID}.yaml"
    assert output_file.exists(), "State file was not generated"
    
    # Verify content
    with open(output_file, 'r') as f:
        state_data = yaml.safe_load(f)
    
    assert state_data["project_id"] == PROJECT_ID
    assert "git_status" in state_data
    assert state_data["git_status"] == "initialized"
    assert "constitution_principle_v" in state_data
    assert "files" in state_data["constitution_principle_v"]
    
    # Verify hashes are correct
    for config_file in CONFIG_FILES:
        assert config_file in state_data["constitution_principle_v"]["files"]
        expected_hash = compute_file_hash(tmp_path / config_file)
        assert state_data["constitution_principle_v"]["files"][config_file] == expected_hash

def test_project_state_generation_without_git(tmp_path):
    """Test that script fails gracefully when git is not initialized."""
    os.chdir(tmp_path)
    
    # Create dummy config files but NO .git directory
    for config_file in CONFIG_FILES:
        (tmp_path / config_file).write_text(f"# Content of {config_file}\n")
    
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project_state.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    
    # Should exit with error code 1
    assert result.returncode != 0
    assert "git" in result.stdout.lower() or "git" in result.stderr.lower()