import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from scripts.setup_data_dirs import ensure_dir, init_checksums, register_artifact, compute_sha256

def test_ensure_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "test", "nested", "dir")
        result = ensure_dir(test_path)
        assert result.exists()
        assert result.is_dir()

def test_init_checksums():
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.json"
        
        # Test initialization
        data = init_checksums(checksum_file)
        assert data["version"] == "1.0.0"
        assert data["artifacts"] == {}
        
        # Test with initial artifacts
        init_data = {"test.txt": "abc123"}
        data = init_checksums(checksum_file, init_data)
        assert data["artifacts"]["test.txt"] == "abc123"

def test_register_artifact():
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.json"
        init_checksums(checksum_file)
        
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Register artifact
        register_artifact(checksum_file, "test.txt", test_file)
        
        # Verify checksum
        with open(checksum_file, "r") as f:
            data = json.load(f)
        
        assert "test.txt" in data["artifacts"]
        expected_checksum = compute_sha256(test_file)
        assert data["artifacts"]["test.txt"] == expected_checksum

def test_compute_sha256():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        checksum = compute_sha256(test_file)
        assert len(checksum) == 64  # SHA256 hex string length
        assert isinstance(checksum, str)
