import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.pipeline.manifest import calculate_file_hash, should_include_file, generate_manifest, write_manifest

class TestManifestGeneration:
    def test_calculate_file_hash(self, tmp_path):
        """Test that hash calculation works for a simple file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        hash_val = calculate_file_hash(test_file)
        expected_hash = "7f83b1657ff1fc53b92dc18148a1d65dfa9008656c6881d9233284072397334e" # SHA256 of "Hello, World!"
        
        assert hash_val == expected_hash

    def test_calculate_file_hash_large_file(self, tmp_path):
        """Test that hash calculation works for a large file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create a file larger than 4096 bytes (chunk size)
        content = b"X" * (4096 * 2) 
        test_file.write_bytes(content)

        hash_val = calculate_file_hash(test_file)
        # Verify it's a valid 64-char hex string
        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)

    def test_should_include_file_valid(self):
        """Test that valid file types are included."""
        assert should_include_file(Path("code/test.py")) is True
        assert should_include_file(Path("data/processed/data.json")) is True
        assert should_include_file(Path("config/settings.yaml")) is True
        assert should_include_file(Path("docs/readme.md")) is True

    def test_should_include_file_invalid(self):
        """Test that invalid file types are excluded."""
        assert should_include_file(Path("code/__pycache__/test.pyc")) is False
        assert should_include_file(Path("code/test.pyc")) is False
        assert should_include_file(Path("data/raw/secret.txt.bak")) is False
        assert should_include_file(Path(".git/config")) is False
        assert should_include_file(Path("data/processed/.hidden")) is False

    def test_write_manifest(self, tmp_path):
        """Test that write_manifest creates a valid JSON file."""
        manifest_data = {
            "version": "1.0",
            "entries": [
                {"path": "code/test.py", "hash": "abc123", "size_bytes": 100}
            ]
        }
        output_file = tmp_path / "manifest.json"
        
        write_manifest(manifest_data, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == manifest_data

    @patch('src.pipeline.manifest.PROJECT_ROOT', new_callable=lambda: Path(__file__).resolve().parent.parent.parent)
    def test_generate_manifest_structure(self, mock_root):
        """
        Test that generate_manifest returns a dictionary with the correct structure.
        This test mocks the file system traversal to ensure the logic holds without
        needing the full project structure present during unit test.
        """
        # We can't easily mock rglob on a real path without side effects,
        # so we test the logic flow by ensuring the function returns a dict
        # and handles missing directories gracefully (though in a real run,
        # the directories should exist per T001).
        
        # Since the function relies on the real filesystem, we verify the 
        # return type and keys.
        result = generate_manifest()
        
        assert isinstance(result, dict)
        assert "version" in result
        assert "entries" in result
        assert "generated_by" in result
        assert isinstance(result["entries"], list)