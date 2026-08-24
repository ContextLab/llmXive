"""
Integration test for T001c: Checksum Configuration.

Verifies that the checksum_config.py script runs successfully
and produces a valid state file with real SHA256 hashes.
"""
import os
import sys
import subprocess
import yaml
from pathlib import Path

# Add code directory to path
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

def test_checksum_script_execution():
    """Test that the checksum script runs and exits with code 0."""
    script_path = code_dir / "checksum_config.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "Checksums written to:" in result.stdout

def test_state_file_created():
    """Test that the state file exists after script execution."""
    state_file = project_root / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"
    assert state_file.exists(), "State file was not created"

def test_state_file_contains_real_hashes():
    """Test that the state file contains real, non-empty SHA256 hashes."""
    state_file = project_root / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"
    with open(state_file, "r") as f:
        state = yaml.safe_load(f)

    assert "artifact_hashes" in state, "artifact_hashes section missing"
    hashes = state["artifact_hashes"]

    # Check specific files exist and have non-trivial hashes
    required_files = [
        "README.md",
        ".gitignore",
        "code/requirements.txt",
        "code/pytest.ini"
    ]

    for file_path in required_files:
        assert file_path in hashes, f"Hash for {file_path} missing"
        hash_value = hashes[file_path]
        assert len(hash_value) == 64, f"Invalid SHA256 length for {file_path}"
        assert hash_value != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", \
            f"Hash for {file_path} is the empty file hash"

def test_hash_correctness():
    """Verify that the stored hash matches the actual file content."""
    import hashlib
    from pathlib import Path

    state_file = project_root / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"
    with open(state_file, "r") as f:
        state = yaml.safe_load(f)

    hashes = state["artifact_hashes"]

    for rel_path, stored_hash in hashes.items():
        full_path = project_root / rel_path
        if not full_path.exists():
            continue  # Skip if file was deleted externally

        # Compute actual hash
        sha256_hash = hashlib.sha256()
        with open(full_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest()

        assert stored_hash == actual_hash, \
            f"Hash mismatch for {rel_path}: stored={stored_hash}, actual={actual_hash}"
