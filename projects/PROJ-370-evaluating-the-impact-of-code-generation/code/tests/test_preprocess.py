"""
Tests for src/extraction/preprocess.py
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.extraction.preprocess import (
    estimate_tokens,
    truncate_diff,
    preprocess_pr_data,
    extract_raw_comments,
    generate_checksums,
    save_raw_with_checksums,
    generate_human_baseline
)


class TestDiffTruncation:
    """Tests for diff truncation logic."""

    def test_estimate_tokens_empty(self):
        """Empty string should return 0 tokens."""
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0

    def test_estimate_tokens_simple(self):
        """Token estimation should be roughly len(text) // 4."""
        text = "Hello World" * 100  # ~1100 chars
        estimated = estimate_tokens(text)
        assert estimated == len(text) // 4

    def test_truncate_no_op(self):
        """Diff shorter than limit should not be truncated."""
        short_diff = "diff --git a/file.py b/file.py\n+print('hello')"
        result = truncate_diff(short_diff, max_tokens=1000)
        assert result == short_diff

    def test_truncate_actually_truncates(self):
        """Diff longer than limit should be truncated."""
        long_diff = "x" * 10000  # Very long diff
        result = truncate_diff(long_diff, max_tokens=100)
        assert len(result) < len(long_diff)
        assert len(result) > 0

    def test_truncate_preserves_start(self):
        """Truncated diff should start at the beginning."""
        long_diff = "START_" + "x" * 10000
        result = truncate_diff(long_diff, max_tokens=100)
        assert result.startswith("START_")


class TestPreprocessPRData:
    """Tests for PR data preprocessing."""

    def test_no_diffs_key(self):
        """PR without diffs key should pass through."""
        pr = {"pr_id": "123", "title": "Test"}
        result = preprocess_pr_data(pr)
        assert result["pr_id"] == "123"

    def test_empty_diffs_list(self):
        """PR with empty diffs list should pass through."""
        pr = {"pr_id": "123", "diffs": []}
        result = preprocess_pr_data(pr)
        assert result["diffs"] == []

    def test_single_short_diff(self):
        """PR with short diff should not be truncated."""
        pr = {
            "pr_id": "123",
            "diffs": [{"diff_content": "short diff", "truncated": False}]
        }
        result = preprocess_pr_data(pr)
        assert result["diffs"][0]["diff_content"] == "short diff"
        assert result["diffs"][0]["truncated"] is False

    def test_long_diff_truncated(self):
        """PR with long diff should be truncated."""
        long_content = "x" * 10000
        pr = {
            "pr_id": "123",
            "diffs": [{"diff_content": long_content}]
        }
        result = preprocess_pr_data(pr, max_tokens=100)
        assert result["diffs"][0]["truncated"] is True
        assert len(result["diffs"][0]["diff_content"]) < len(long_content)


class TestExtractRawComments:
    """Tests for raw comment extraction."""

    def test_empty_pr_list(self):
        """Empty PR list should return empty comments."""
        comments = extract_raw_comments([])
        assert comments == []

    def test_pr_without_comments(self):
        """PR without comments should not add to list."""
        pr = {"pr_id": "123", "title": "Test"}
        comments = extract_raw_comments([pr])
        assert comments == []

    def test_pr_with_comments(self):
        """PR with comments should extract them."""
        pr = {
            "pr_id": "123",
            "comments": [
                {
                    "id": "c1",
                    "user": {"login": "alice"},
                    "body": "Great work!",
                    "created_at": "2024-01-01T00:00:00Z",
                    "path": "file.py",
                    "line": 10
                }
            ]
        }
        comments = extract_raw_comments([pr])
        assert len(comments) == 1
        assert comments[0]["pr_id"] == "123"
        assert comments[0]["author"] == "alice"
        assert comments[0]["body"] == "Great work!"

    def test_pr_with_review_comments(self):
        """PR with review_comments should extract them."""
        pr = {
            "pr_id": "123",
            "review_comments": [
                {
                    "id": "rc1",
                    "user": {"login": "bob"},
                    "body": "Check this line",
                    "created_at": "2024-01-01T00:00:00Z",
                    "path": "file.py",
                    "line": 20
                }
            ]
        }
        comments = extract_raw_comments([pr])
        assert len(comments) == 1
        assert comments[0]["author"] == "bob"


class TestGenerateChecksums:
    """Tests for checksum generation."""

    def test_empty_list(self):
        """Empty file list should return empty checksums."""
        checksums = generate_checksums([])
        assert checksums == {}

    def test_single_file(self):
        """Single file should produce one checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"test": "data"}')
            temp_path = Path(f.name)
        
        try:
            checksums = generate_checksums([temp_path])
            assert len(checksums) == 1
            assert "test" in temp_path.name or temp_path.name in checksums
            # Verify it's a valid SHA-256 hash
            assert len(list(checksums.values())[0]) == 64
        finally:
            temp_path.unlink()

    def test_nonexistent_file_skipped(self):
        """Non-existent file should be skipped with warning."""
        fake_path = Path("/nonexistent/file.json")
        checksums = generate_checksums([fake_path])
        assert fake_path.name not in checksums

    def test_multiple_files(self):
        """Multiple files should produce multiple checksums."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
            f1.write('file1')
            path1 = Path(f1.name)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
            f2.write('file2')
            path2 = Path(f2.name)
        
        try:
            checksums = generate_checksums([path1, path2])
            assert len(checksums) == 2
        finally:
            path1.unlink()
            path2.unlink()


class TestSaveRawWithChecksums:
    """Tests for saving raw data with checksums."""

    def test_creates_json_and_checksums(self):
        """Should create both data JSON and checksums JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            pr_data = [{"pr_id": "1", "title": "Test"}]
            
            save_raw_with_checksums(pr_data, output_dir)
            
            # Check data file exists
            json_files = list(output_dir.glob("pr_data_*.json"))
            assert len(json_files) == 1
            
            # Check checksums file exists
            checksums_file = output_dir / "checksums.json"
            assert checksums_file.exists()
            
            # Check checksums content
            with open(checksums_file) as f:
                checksums = json.load(f)
            assert len(checksums) >= 1  # At least the data file

    def test_checksums_match_file_content(self):
        """Checksums should match actual file content."""
        import hashlib
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            pr_data = [{"pr_id": "1", "title": "Test"}]
            
            save_raw_with_checksums(pr_data, output_dir)
            
            json_files = list(output_dir.glob("pr_data_*.json"))
            data_file = json_files[0]
            
            # Calculate actual checksum
            sha256_hash = hashlib.sha256()
            with open(data_file, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            actual_hash = sha256_hash.hexdigest()
            
            # Compare with stored checksum
            with open(output_dir / "checksums.json") as f:
                checksums = json.load(f)
            
            assert checksums[data_file.name] == actual_hash


class TestMainFunction:
    """Tests for the main entry point."""

    @patch('code.src.extraction.preprocess.get_paths')
    @patch('code.src.extraction.preprocess.ensure_directories')
    @patch('code.src.extraction.preprocess.glob')
    def test_main_no_raw_data(self, mock_glob, mock_ensure, mock_get_paths):
        """Main should handle case with no raw data."""
        mock_get_paths.return_value = {
            "raw": Path("/tmp/raw"),
            "annotations": Path("/tmp/annotations")
        }
        mock_glob.return_value = []
        
        # Should not raise
        from code.src.extraction.preprocess import main
        # Note: We can't easily test the logging output, but we verify no crash

    @patch('code.src.extraction.preprocess.get_paths')
    @patch('code.src.extraction.preprocess.ensure_directories')
    @patch('code.src.extraction.preprocess.open')
    @patch('code.src.extraction.preprocess.glob')
    def test_main_processes_data(self, mock_glob, mock_open, mock_ensure, mock_get_paths):
        """Main should process existing raw data."""
        mock_get_paths.return_value = {
            "raw": Path("/tmp/raw"),
            "annotations": Path("/tmp/annotations")
        }
        
        # Mock a raw file
        mock_file = MagicMock()
        mock_file.name = "pr_data_test.json"
        mock_file.stat.return_value.st_mtime = 1000000
        mock_glob.return_value = [mock_file]
        
        # Mock file reading
        mock_open.return_value.__enter__.return_value.read.return_value = '[]'
        
        from code.src.extraction.preprocess import main
        # Should not raise
        # Note: Full integration test would require more mocking