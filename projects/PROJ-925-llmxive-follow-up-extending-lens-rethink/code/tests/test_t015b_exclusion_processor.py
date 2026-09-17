import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.exclusion_processor import parse_exclusion_log, write_summary


class TestExclusionProcessor:
    """Tests for the exclusion log processing functionality."""

    def test_parse_exclusion_log_valid(self, tmp_path):
        """Test parsing a valid exclusion log file."""
        log_content = """
        caption_001 | TIMEOUT_EXCEEDED
        caption_002 | BERT_FAILURE
        caption_003 | TIMEOUT_EXCEEDED
        caption_004 | SHORT_CAPTION
        caption_005 | TIMEOUT_EXCEEDED
        """
        
        log_file = tmp_path / "exclusions.log"
        log_file.write_text(log_content.strip())
        
        result = parse_exclusion_log(log_file)
        
        assert result == {
            "TIMEOUT_EXCEEDED": 3,
            "BERT_FAILURE": 1,
            "SHORT_CAPTION": 1
        }

    def test_parse_exclusion_log_empty_file(self, tmp_path):
        """Test that an empty log file raises ValueError."""
        log_file = tmp_path / "exclusions.log"
        log_file.write_text("")
        
        with pytest.raises(ValueError, match="empty or contains no valid entries"):
            parse_exclusion_log(log_file)

    def test_parse_exclusion_log_missing_file(self, tmp_path):
        """Test that a missing log file raises FileNotFoundError."""
        missing_path = tmp_path / "nonexistent.log"
        
        with pytest.raises(FileNotFoundError):
            parse_exclusion_log(missing_path)

    def test_parse_exclusion_log_malformed_lines(self, tmp_path):
        """Test that malformed lines are skipped with warnings."""
        log_content = """
        caption_001 | TIMEOUT_EXCEEDED
        malformed_line_without_pipe
        caption_002 | BERT_FAILURE
        another_bad_line
        """
        
        log_file = tmp_path / "exclusions.log"
        log_file.write_text(log_content.strip())
        
        result = parse_exclusion_log(log_file)
        
        # Should only count valid entries
        assert result == {
            "TIMEOUT_EXCEEDED": 1,
            "BERT_FAILURE": 1
        }

    def test_parse_exclusion_log_empty_fields(self, tmp_path):
        """Test that entries with empty caption_id or reason are skipped."""
        log_content = """
        | TIMEOUT_EXCEEDED
        caption_001 | 
        caption_002 | BERT_FAILURE
        """
        
        log_file = tmp_path / "exclusions.log"
        log_file.write_text(log_content.strip())
        
        result = parse_exclusion_log(log_file)
        
        assert result == {
            "BERT_FAILURE": 1
        }

    def test_write_summary_creates_json(self, tmp_path):
        """Test that write_summary creates a properly formatted JSON file."""
        reason_counts = {
            "TIMEOUT_EXCEEDED": 10,
            "BERT_FAILURE": 5,
            "SHORT_CAPTION": 3
        }
        
        output_file = tmp_path / "exclusion_summary.json"
        write_summary(reason_counts, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            summary = json.load(f)
        
        assert summary["total_excluded"] == 18
        assert summary["exclusion_counts"] == reason_counts
        assert len(summary["reasons"]) == 3
        assert "TIMEOUT_EXCEEDED" in summary["reasons"]

    def test_write_summary_creates_parent_dirs(self, tmp_path):
        """Test that write_summary creates parent directories if needed."""
        reason_counts = {"TEST": 1}
        output_file = tmp_path / "subdir" / "nested" / "summary.json"
        
        write_summary(reason_counts, output_file)
        
        assert output_file.exists()

    def test_write_summary_sorted_reasons(self, tmp_path):
        """Test that reasons are sorted in the output."""
        reason_counts = {
            "Z_REASON": 1,
            "A_REASON": 1,
            "M_REASON": 1
        }
        
        output_file = tmp_path / "summary.json"
        write_summary(reason_counts, output_file)
        
        with open(output_file, 'r') as f:
            summary = json.load(f)
        
        assert summary["reasons"] == ["A_REASON", "M_REASON", "Z_REASON"]
