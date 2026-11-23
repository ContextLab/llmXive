import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
# Note: The import path assumes the test is run from the project root or with code/ in sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.utils.exclusion_processor import parse_exclusion_log, aggregate_exclusions, write_summary, main

class TestExclusionProcessor:

    def test_parse_exclusion_log_missing_file(self, tmp_path):
        """Test that parse_exclusion_log returns empty list for missing file."""
        log_path = tmp_path / "missing.log"
        records = parse_exclusion_log(log_path)
        assert records == []

    def test_parse_exclusion_log_json_format(self, tmp_path):
        """Test parsing of JSON formatted exclusion log."""
        log_path = tmp_path / "exclusions.log"
        data = [
            {"caption_id": "1", "reason": "TIMEOUT_EXCEEDED"},
            {"caption_id": "2", "reason": "BERT_FAILURE"},
            {"caption_id": "3", "reason": "TOO_SHORT"}
        ]
        with open(log_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')

        records = parse_exclusion_log(log_path)
        assert len(records) == 3
        assert records[0]['reason'] == 'TIMEOUT_EXCEEDED'
        assert records[1]['caption_id'] == '2'

    def test_parse_exclusion_log_pipe_format(self, tmp_path):
        """Test parsing of pipe-delimited exclusion log."""
        log_path = tmp_path / "exclusions.log"
        content = "1|TIMEOUT_EXCEEDED\n2|BERT_FAILURE\n3|TOO_SHORT\n"
        with open(log_path, 'w') as f:
            f.write(content)

        records = parse_exclusion_log(log_path)
        assert len(records) == 3
        assert records[0]['reason'] == 'TIMEOUT_EXCEEDED'
        assert records[1]['caption_id'] == '2'

    def test_aggregate_exclusions(self):
        """Test aggregation of exclusion records."""
        records = [
            {'caption_id': '1', 'reason': 'TIMEOUT_EXCEEDED'},
            {'caption_id': '2', 'reason': 'BERT_FAILURE'},
            {'caption_id': '3', 'reason': 'TIMEOUT_EXCEEDED'},
            {'caption_id': '4', 'reason': 'TOO_SHORT'}
        ]
        summary = aggregate_exclusions(records)

        assert summary['total_excluded'] == 4
        assert summary['by_reason']['TIMEOUT_EXCEEDED'] == 2
        assert summary['by_reason']['BERT_FAILURE'] == 1
        assert summary['by_reason']['TOO_SHORT'] == 1
        assert len(summary['details']) == 4

    def test_write_summary(self, tmp_path):
        """Test writing summary to JSON file."""
        summary = {
            'total_excluded': 5,
            'by_reason': {'A': 3, 'B': 2},
            'details': []
        }
        output_path = tmp_path / "summary.json"
        write_summary(summary, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded['total_excluded'] == 5
        assert loaded['by_reason']['A'] == 3

    @patch('code.utils.exclusion_processor.get_paths')
    @patch('code.utils.exclusion_processor.init_run')
    def test_main(self, mock_init_run, mock_get_paths, tmp_path):
        """Test the main entry point."""
        # Setup mock paths
        mock_paths = MagicMock()
        mock_paths.raw.parent = tmp_path / "data"
        (tmp_path / "data" / "logs").mkdir(parents=True, exist_ok=True)
        
        # Create a fake log file
        log_path = tmp_path / "data" / "logs" / "exclusions.log"
        with open(log_path, 'w') as f:
            f.write('{"caption_id": "1", "reason": "TEST_REASON"}\n')

        mock_get_paths.return_value = mock_paths

        # We need to patch the actual file paths used in main()
        # Since main() hardcodes "data/logs/exclusions.log", we need to ensure that file exists
        # in the current working directory or patch the path logic.
        # For this test, we'll create the file in the expected location relative to tmp_path
        # and change the working directory.
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create the expected directory structure
            (tmp_path / "data" / "logs").mkdir(parents=True, exist_ok=True)
            with open("data/logs/exclusions.log", 'w') as f:
                f.write('{"caption_id": "1", "reason": "TEST_REASON"}\n')
            
            result = main()
            
            assert result['total_excluded'] == 1
            assert result['by_reason']['TEST_REASON'] == 1
            assert Path("data/processed/exclusion_summary.json").exists()
        finally:
            os.chdir(original_cwd)
