"""
Unit tests for the preprocessing module (T015).

Tests cover:
- Token estimation
- Diff truncation
- Raw comment extraction
- Checksum generation
- Saving raw data with checksums
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.extraction.preprocess import (
    estimate_tokens,
    truncate_diff,
    preprocess_pr_data,
    extract_raw_comments,
    generate_checksums,
    save_raw_with_checksums
)

class TestDiffTruncation:
    """Tests for diff truncation functionality."""

    def test_estimate_tokens_empty_string(self):
        """Test token estimation with empty string."""
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0

    def test_estimate_tokens_simple(self):
        """Test token estimation with simple text."""
        text = "print('hello')"
        estimated = estimate_tokens(text)
        # Should be approximately len / 4
        assert estimated > 0
        assert estimated <= len(text)

    def test_truncate_diff_no_truncation_needed(self):
        """Test that short diffs are not truncated."""
        short_diff = "diff --git a/file.py b/file.py\n@@ -1,2 +1,2 @@\n-old\n+new\n"
        truncated, was_truncated = truncate_diff(short_diff, token_limit=1000)
        
        assert not was_truncated
        assert truncated == short_diff

    def test_truncate_diff_exceeds_limit(self):
        """Test that long diffs are truncated."""
        # Create a long diff
        long_diff = "diff --git a/file.py b/file.py\n" + "\n".join([f"+line{i}" for i in range(1000)])
        
        truncated, was_truncated = truncate_diff(long_diff, token_limit=100)
        
        assert was_truncated
        assert "[TRUNCATED" in truncated
        assert len(truncated) < len(long_diff)

    def test_truncate_diff_empty(self):
        """Test truncation with empty diff."""
        truncated, was_truncated = truncate_diff("", token_limit=100)
        
        assert not was_truncated
        assert truncated == ""

class TestPreprocessPRData:
    """Tests for PR data preprocessing."""

    def test_preprocess_pr_data_no_diff(self):
        """Test preprocessing PR without diff."""
        pr_data = {"number": 1, "title": "Test"}
        result = preprocess_pr_data(pr_data)
        
        assert result['truncation_flag'] == False
        assert result['number'] == 1

    def test_preprocess_pr_data_with_short_diff(self):
        """Test preprocessing PR with short diff."""
        pr_data = {
            "number": 1,
            "diff": "diff --git a/file.py b/file.py\n@@ -1 +1 @@\n-old\n+new\n"
        }
        result = preprocess_pr_data(pr_data)
        
        assert result['truncation_flag'] == False
        assert 'original_diff_length' not in result

    def test_preprocess_pr_data_with_long_diff(self):
        """Test preprocessing PR with long diff that needs truncation."""
        long_diff = "diff --git a/file.py b/file.py\n" + "\n".join([f"+line{i}" for i in range(1000)])
        pr_data = {
            "number": 1,
            "diff": long_diff
        }
        result = preprocess_pr_data(pr_data, token_limit=100)
        
        assert result['truncation_flag'] == True
        assert 'original_diff_length' in result
        assert 'truncated_diff_length' in result
        assert "[TRUNCATED" in result['diff']

class TestExtractRawComments:
    """Tests for raw comment extraction."""

    def test_extract_raw_comments_no_comments(self):
        """Test extraction when no comments exist."""
        pr_data = {"number": 1}
        comments = extract_raw_comments(pr_data)
        
        assert comments == []

    def test_extract_raw_comments_with_review_comments(self):
        """Test extraction of review comments."""
        pr_data = {
            "number": 123,
            "review_comments": [
                {
                    "user": {"login": "reviewer1"},
                    "body": "LGTM",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
        comments = extract_raw_comments(pr_data)
        
        assert len(comments) == 1
        assert comments[0]['reviewer_id'] == 'reviewer1'
        assert comments[0]['comment_body'] == 'LGTM'
        assert comments[0]['linked_pr_id'] == 123
        assert comments[0]['is_confirmed'] == False

    def test_extract_raw_comments_mixed_types(self):
        """Test extraction of both review and general comments."""
        pr_data = {
            "number": 456,
            "review_comments": [
                {
                    "user": {"login": "reviewer1"},
                    "body": "Review comment",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "comments": [
                {
                    "user": {"login": "commenter1"},
                    "body": "General comment",
                    "created_at": "2024-01-02T00:00:00Z"
                }
            ]
        }
        comments = extract_raw_comments(pr_data)
        
        assert len(comments) == 2
        types = [c['comment_type'] for c in comments]
        assert 'review' in types
        assert 'comment' in types

class TestGenerateChecksums:
    """Tests for checksum generation."""

    def test_generate_checksums_known_file(self):
        """Test checksum generation with known content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            checksum = generate_checksums(temp_path)
            # SHA-256 of "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_generate_checksums_empty_file(self):
        """Test checksum generation with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            checksum = generate_checksums(temp_path)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_generate_checksums_large_file(self):
        """Test checksum generation with larger file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("x" * 1000000)  # 1MB
            temp_path = Path(f.name)
        
        try:
            checksum = generate_checksums(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
        finally:
            os.unlink(temp_path)

class TestSaveRawWithChecksums:
    """Tests for saving raw data with checksums."""

    def test_save_raw_with_checksums_creates_files(self):
        """Test that both data and checksum files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            raw_data = [
                {"number": 1, "title": "PR 1"},
                {"number": 2, "title": "PR 2"}
            ]
            
            checksums_path = save_raw_with_checksums(raw_data, output_dir)
            
            # Check files exist
            assert checksums_path.exists()
            assert (output_dir / "pr_data_raw.json").exists()
            
            # Verify checksums content
            with open(checksums_path, 'r') as f:
                checksums_data = json.load(f)
            
            assert 'files' in checksums_data
            assert len(checksums_data['files']) == 1
            assert checksums_data['files'][0]['filename'] == 'pr_data_raw.json'
            assert 'checksum' in checksums_data['files'][0]
            assert checksums_data['files'][0]['record_count'] == 2

    def test_save_raw_with_checksums_validates_data(self):
        """Test that saved data matches input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            raw_data = [
                {"number": 1, "title": "PR 1", "diff": "test diff"},
                {"number": 2, "title": "PR 2", "diff": "another diff"}
            ]
            
            save_raw_with_checksums(raw_data, output_dir)
            
            # Load saved data
            with open(output_dir / "pr_data_raw.json", 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == raw_data

class TestMainFunction:
    """Tests for the main function."""

    @patch('code.src.extraction.preprocess.get_paths')
    @patch('code.src.extraction.preprocess.setup_pipeline_logging')
    @patch('code.src.extraction.preprocess.get_logger')
    def test_main_missing_raw_file(
        self, 
        mock_logger, 
        mock_setup_logging, 
        mock_get_paths
    ):
        """Test main function when raw data file is missing."""
        from code.src.utils.logger import get_logger
        
        mock_logger.return_value = MagicMock()
        mock_get_paths.return_value = {
            'data_raw': Path("/tmp/nonexistent")
        }
        
        # This should log an error and return
        from code.src.extraction.preprocess import main
        main()
        
        mock_logger.return_value.error.assert_called()

    @patch('code.src.extraction.preprocess.get_paths')
    @patch('code.src.extraction.preprocess.setup_pipeline_logging')
    @patch('code.src.extraction.preprocess.get_logger')
    @patch('builtins.open')
    @patch('code.src.extraction.preprocess.json.load')
    @patch('code.src.extraction.preprocess.save_raw_with_checksums')
    def test_main_success(
        self,
        mock_save,
        mock_json_load,
        mock_open,
        mock_logger,
        mock_setup_logging,
        mock_get_paths
    ):
        """Test main function with valid data."""
        from code.src.utils.logger import get_logger
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        mock_get_paths.return_value = {
            'data_raw': Path("/tmp/test")
        }
        mock_json_load.return_value = [{"number": 1}]
        mock_save.return_value = Path("/tmp/checksums.json")
        
        from code.src.extraction.preprocess import main
        main()
        
        mock_logger_instance.info.assert_called()
        mock_save.assert_called_once()