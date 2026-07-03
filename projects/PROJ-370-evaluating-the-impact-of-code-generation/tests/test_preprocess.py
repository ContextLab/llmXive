import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Ensure we can import from code
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.extraction.preprocess import (
    estimate_tokens, 
    truncate_diff, 
    extract_raw_comments,
    generate_checksums,
    generate_human_baseline
)

class TestDiffTruncation:
    def test_no_truncation_needed(self):
        short_text = "print('hello')"
        result = truncate_diff(short_text, max_tokens=1000)
        assert result == short_text

    def test_truncation_happens(self):
        long_text = "x = 1\n" * 5000  # ~20000 chars, likely > 8000 tokens
        result = truncate_diff(long_text, max_tokens=100)
        assert "TRUNCATED" in result
        assert len(result) < len(long_text)

class TestExtractRawComments:
    def test_extract_basic_comment(self):
        pr_data = [{
            "number": 101,
            "title": "Fix bug",
            "review_comments": [
                {
                    "user": {"login": "alice"},
                    "body": "Looks good",
                    "created_at": "2023-01-01T00:00:00Z",
                    "path": "src/main.py",
                    "position": 10
                }
            ]
        }]
        comments = extract_raw_comments(pr_data)
        assert len(comments) == 1
        assert comments[0]["pr_id"] == 101
        assert comments[0]["author"] == "alice"
        assert comments[0]["body"] == "Looks good"
        assert comments[0]["is_raw"] is True

    def test_missing_fields(self):
        pr_data = [{
            "number": 102,
            "review_comments": [
                {
                    "user": {},
                    "body": None,
                    "path": None
                }
            ]
        }]
        comments = extract_raw_comments(pr_data)
        assert len(comments) == 1
        assert comments[0]["author"] == "unknown"
        assert comments[0]["body"] == ""

class TestGenerateChecksums:
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("test")
            temp_path = f.name
        
        try:
            checksums = generate_checksums([temp_path])
            assert len(checksums) == 1
            # Check it's a valid sha256 hex string
            assert len(list(checksums.values())[0]) == 64
        finally:
            import os
            os.remove(temp_path)

class TestGenerateHumanBaseline:
    def test_empty_input(self):
        result = generate_human_baseline([])
        assert result == []
    
    def test_non_strict_mode_placeholder(self):
        # T017 handles the logic, T014 just needs the function to exist and run
        pr_data = [{"number": 1, "review_comments": []}]
        result = generate_human_baseline(pr_data, strict=False)
        assert isinstance(result, list)