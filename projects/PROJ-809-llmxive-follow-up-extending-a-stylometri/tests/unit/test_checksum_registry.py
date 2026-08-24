"""
Unit tests for T016: Checksum Registry.

Tests that the checksum registry logic correctly identifies files
and computes hashes without actually running the full pipeline.
"""
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import compute_sha256

class TestChecksumLogic:
    
    def test_compute_sha256_string(self):
        """Test that SHA-256 computation is deterministic."""
        test_string = "test data for hashing"
        h1 = compute_sha256_string(test_string)
        h2 = compute_sha256_string(test_string)
        assert h1 == h2
        assert len(h1) == 64  # Hex length

    def test_compute_sha256_file(self, tmp_path):
        """Test file hashing logic."""
        test_file = tmp_path / "test.txt"
        content = "hello world"
        test_file.write_text(content)
        
        h = compute_sha256(str(test_file))
        assert h is not None
        assert len(h) == 64

    def test_file_discovery_raw(self, tmp_path):
        """Test discovery of raw parquet files."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create a fake parquet file
        fake_parquet = raw_dir / "arxiv_subset.parquet"
        fake_parquet.write_text("fake parquet data")
        
        # Simulate logic from get_raw_artifact_path
        parquet_files = list(raw_dir.glob("*.parquet"))
        assert len(parquet_files) == 1
        assert parquet_files[0].name == "arxiv_subset.parquet"

    def test_file_discovery_processed(self, tmp_path):
        """Test discovery of processed artifacts."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create author folder with files
        author_dir = processed_dir / "author_001"
        author_dir.mkdir()
        (author_dir / "text_1.txt").write_text("text 1")
        (author_dir / "text_2.txt").write_text("text 2")
        
        # Create collision report
        (processed_dir / "collision_report.json").write_text("{}")
        
        # Simulate logic from get_processed_artifact_paths
        artifacts = []
        collision_report = processed_dir / "collision_report.json"
        if collision_report.exists():
            artifacts.append(collision_report)
        
        for item in processed_dir.iterdir():
            if item.is_dir():
                for file_path in item.rglob("*"):
                    if file_path.is_file():
                        artifacts.append(file_path)
            elif item.is_file() and item != collision_report:
                artifacts.append(item)
        
        # Should find collision report + 2 text files
        assert len(artifacts) == 3
        assert any("collision_report.json" in str(a) for a in artifacts)
        assert any("text_1.txt" in str(a) for a in artifacts)
        assert any("text_2.txt" in str(a) for a in artifacts)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
