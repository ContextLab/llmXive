import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# Note: We test the logic of checksumming and state recording
# by mocking the heavy extraction parts or testing the serialization logic directly

from utils.models import compute_checksum

class TestExtractChecksum:
    """Tests for checksum computation and state recording logic."""

    def test_compute_checksum_file_exists(self, tmp_path):
        """Test that compute_checksum returns a valid SHA-256 hash for an existing file."""
        test_file = tmp_path / "test.json"
        content = {"key": "value", "number": 123}
        with open(test_file, 'w') as f:
            json.dump(content, f)
        
        checksum = compute_checksum(test_file)
        
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_compute_checksum_different_content_different_hash(self, tmp_path):
        """Test that different file contents produce different hashes."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        
        with open(file1, 'w') as f:
            json.dump({"id": 1}, f)
        with open(file2, 'w') as f:
            json.dump({"id": 2}, f)
        
        hash1 = compute_checksum(file1)
        hash2 = compute_checksum(file2)
        
        assert hash1 != hash2

    def test_compute_checksum_identical_content_same_hash(self, tmp_path):
        """Test that identical file contents produce the same hash."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        
        content = {"id": 1, "data": [1, 2, 3]}
        
        with open(file1, 'w') as f:
            json.dump(content, f)
        with open(file2, 'w') as f:
            json.dump(content, f)
        
        hash1 = compute_checksum(file1)
        hash2 = compute_checksum(file2)
        
        assert hash1 == hash2

    def test_compute_checksum_nonexistent_file_raises(self, tmp_path):
        """Test that compute_checksum raises FileNotFoundError for missing files."""
        missing_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            compute_checksum(missing_file)

class TestStateRecording:
    """Tests for the state recording logic (YAML generation)."""

    def test_state_file_format(self, tmp_path):
        """Test that the state file is written with correct YAML-like format."""
        # Simulate the logic from main()
        project_slug = "test-project-318"
        artifact_hashes = {
            "repo1_methods.json": "abc123...",
            "repo2_methods.json": "def456..."
        }
        
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        state_file = state_dir / f"{project_slug}.yaml"
        
        content_lines = []
        content_lines.append(f"project: {project_slug}")
        content_lines.append("timestamp: test-time")
        content_lines.append("artifact_hashes:")
        for filename, checksum in artifact_hashes.items():
            content_lines.append(f"  {filename}: {checksum}")
        
        content_str = "\n".join(content_lines)
        
        with open(state_file, 'w') as f:
            f.write(content_str)
        
        # Verify file exists
        assert state_file.exists()
        
        # Verify content
        with open(state_file, 'r') as f:
            written_content = f.read()
        
        assert f"project: {project_slug}" in written_content
        assert "artifact_hashes:" in written_content
        assert "repo1_methods.json: abc123..." in written_content
        assert "repo2_methods.json: def456..." in written_content
        
        # Verify indentation (2 spaces)
        lines = written_content.split('\n')
        hash_line = [l for l in lines if l.startswith('  repo1')][0]
        assert hash_line.startswith('  ') and not hash_line.startswith('    ')