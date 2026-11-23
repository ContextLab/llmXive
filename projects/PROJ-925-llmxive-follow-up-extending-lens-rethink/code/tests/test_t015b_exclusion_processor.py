"""
Unit tests for exclusion log processing (T015b)
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.utils.exclusion_processor import (
    parse_exclusion_log,
    aggregate_exclusions,
    write_summary,
    main
)


class TestExclusionProcessor:
    """Tests for T015b exclusion log processing functionality."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary exclusion log file for testing."""
        log_file = tmp_path / "exclusions.log"
        log_content = """INFO:caption_id=cap_001;reason=TIMEOUT_EXCEEDED;message=Calculation exceeded 5s timeout
INFO:caption_id=cap_002;reason=TIMEOUT_EXCEEDED;message=Calculation exceeded 5s timeout
INFO:caption_id=cap_003;reason=BERT_FAILURE;message=Model inference failed
INFO:caption_id=cap_004;reason=TOO_SHORT;message=Caption too short for dependency tree
INFO:caption_id=cap_005;reason=TIMEOUT_EXCEEDED;message=Calculation exceeded 5s timeout
INFO:caption_id=cap_006;reason=BERT_FAILURE;message=Model not found
INFO:caption_id=cap_007;reason=TOO_SHORT;message=Single word caption
"""
        log_file.write_text(log_content)
        return log_file

    @pytest.fixture
    def empty_log_file(self, tmp_path):
        """Create an empty temporary log file."""
        log_file = tmp_path / "empty_exclusions.log"
        log_file.write_text("")
        return log_file

    @pytest.fixture
    def malformed_log_file(self, tmp_path):
        """Create a log file with some malformed lines."""
        log_file = tmp_path / "malformed_exclusions.log"
        log_content = """INFO:caption_id=cap_001;reason=TIMEOUT_EXCEEDED;message=Valid line
This is a malformed line without key=value pairs
INFO:caption_id=cap_002;reason=BERT_FAILURE;message=Another valid line
Incomplete line without semicolons
"""
        log_file.write_text(log_content)
        return log_file

    def test_parse_exclusion_log_valid(self, temp_log_file):
        """Test parsing a valid exclusion log file."""
        records = parse_exclusion_log(temp_log_file)

        assert len(records) == 7
        assert records[0]['caption_id'] == 'cap_001'
        assert records[0]['reason'] == 'TIMEOUT_EXCEEDED'
        assert 'message' in records[0]

        # Check reason distribution
        reasons = [r['reason'] for r in records]
        assert reasons.count('TIMEOUT_EXCEEDED') == 3
        assert reasons.count('BERT_FAILURE') == 2
        assert reasons.count('TOO_SHORT') == 2

    def test_parse_exclusion_log_empty(self, empty_log_file):
        """Test parsing an empty log file returns empty list."""
        records = parse_exclusion_log(empty_log_file)
        assert records == []

    def test_parse_exclusion_log_malformed(self, malformed_log_file):
        """Test that malformed lines are skipped but valid lines are parsed."""
        records = parse_exclusion_log(malformed_log_file)

        # Should only get the 2 valid lines
        assert len(records) == 2
        assert records[0]['caption_id'] == 'cap_001'
        assert records[1]['caption_id'] == 'cap_002'

    def test_parse_exclusion_log_nonexistent(self, tmp_path):
        """Test that a nonexistent log file returns empty list."""
        fake_path = tmp_path / "nonexistent.log"
        records = parse_exclusion_log(fake_path)
        assert records == []

    def test_aggregate_exclusions(self, temp_log_file):
        """Test aggregation of exclusion records."""
        records = parse_exclusion_log(temp_log_file)
        summary = aggregate_exclusions(records)

        assert summary['total_excluded'] == 7
        assert summary['by_reason']['TIMEOUT_EXCEEDED'] == 3
        assert summary['by_reason']['BERT_FAILURE'] == 2
        assert summary['by_reason']['TOO_SHORT'] == 2
        assert set(summary['reasons_found']) == {'TIMEOUT_EXCEEDED', 'BERT_FAILURE', 'TOO_SHORT'}

    def test_aggregate_exclusions_empty(self):
        """Test aggregation with empty records."""
        summary = aggregate_exclusions([])
        assert summary['total_excluded'] == 0
        assert summary['by_reason'] == {}
        assert summary['reasons_found'] == []

    def test_write_summary(self, tmp_path):
        """Test writing summary to JSON file."""
        summary = {
            'total_excluded': 5,
            'by_reason': {'TIMEOUT_EXCEEDED': 3, 'BERT_FAILURE': 2},
            'reasons_found': ['TIMEOUT_EXCEEDED', 'BERT_FAILURE'],
            'processed_at': None
        }

        output_path = tmp_path / "test_summary.json"
        write_summary(summary, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            written = json.load(f)

        assert written['total_excluded'] == 5
        assert 'processed_at' in written  # Should have timestamp added

    def test_main_function(self, temp_log_file, tmp_path):
        """Test the main function end-to-end."""
        # Mock get_paths and get_project_root to use temp directories
        with patch('code.utils.exclusion_processor.get_paths') as mock_paths, \
             patch('code.utils.exclusion_processor.get_project_root') as mock_root:

            mock_root.return_value = tmp_path
            # Create data/logs directory
            (tmp_path / "data" / "logs").mkdir(parents=True)
            (tmp_path / "data" / "processed").mkdir(parents=True)

            # Copy temp log to expected location
            import shutil
            shutil.copy(temp_log_file, tmp_path / "data" / "logs" / "exclusions.log")

            # Run main
            result = main()

            # Verify output file was created
            output_path = tmp_path / "data" / "processed" / "exclusion_summary.json"
            assert output_path.exists()

            # Verify result structure
            assert 'total_excluded' in result
            assert 'by_reason' in result
            assert 'processed_at' in result
            assert result['total_excluded'] == 7

    def test_main_with_empty_log(self, empty_log_file, tmp_path):
        """Test main function with empty log file."""
        with patch('code.utils.exclusion_processor.get_paths') as mock_paths, \
             patch('code.utils.exclusion_processor.get_project_root') as mock_root:

            mock_root.return_value = tmp_path
            (tmp_path / "data" / "logs").mkdir(parents=True)
            (tmp_path / "data" / "processed").mkdir(parents=True)

            import shutil
            shutil.copy(empty_log_file, tmp_path / "data" / "logs" / "exclusions.log")

            result = main()

            assert result['total_excluded'] == 0
            assert result['by_reason'] == {}