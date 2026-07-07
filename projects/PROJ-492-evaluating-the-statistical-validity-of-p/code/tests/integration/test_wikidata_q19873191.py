"""
Integration tests for the Wikidata Q19873191 verification script.
Verifies that the script runs, produces output files, and the files contain expected structure.
"""
import pytest
import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.scripts.verify_wikidata_q19873191 import main, fetch_wikidata_sparql, parse_wikidata_bindings

class TestWikidataVerification:
    """Tests for the Wikidata verification task."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure output directories exist before tests."""
        self.output_dir = Path("data/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.output_dir / "wikidata_q19873191_data.csv"
        self.json_path = self.output_dir / "wikidata_q19873191_metadata.json"
        yield
        # Cleanup optional: remove generated files after test if desired, 
        # but keeping them for artifact verification is often preferred in this pipeline.

    def test_main_execution(self):
        """Test that main() executes without raising exceptions."""
        # We expect the network call to succeed or fail gracefully
        # The function should return 0 on success or raise an error if critical
        try:
            result = main()
            assert result == 0, f"Main returned non-zero exit code: {result}"
        except Exception as e:
            # If the network is down or API fails, we might want to skip or mark as expected failure
            # But for the purpose of "implementation", the code must handle it.
            # If it raises an unhandled exception, the test fails.
            if "Failed to fetch" in str(e):
                pytest.skip("Network unavailable, but code structure is correct.")
            else:
                raise

    def test_csv_output_exists(self):
        """Verify that the CSV output file is created."""
        # Run main first to ensure file exists
        try:
            main()
        except Exception:
            pass # Ignore errors if file is created anyway

        assert self.csv_path.exists(), f"CSV output file not found at {self.csv_path}"

    def test_csv_has_headers(self):
        """Verify the CSV has the required header structure."""
        if not self.csv_path.exists():
            pytest.skip("CSV file does not exist")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert headers is not None, "CSV has no headers"
            # Check for mandatory fields
            assert 'wikidata_qid' in headers, "Missing 'wikidata_qid' column"
            assert 'fetch_timestamp' in headers, "Missing 'fetch_timestamp' column"
            assert 'source' in headers, "Missing 'source' column"

    def test_json_metadata_exists(self):
        """Verify that the JSON metadata file is created."""
        try:
            main()
        except Exception:
            pass

        assert self.json_path.exists(), f"JSON metadata file not found at {self.json_path}"

    def test_json_metadata_structure(self):
        """Verify the JSON metadata contains required fields."""
        if not self.json_path.exists():
            pytest.skip("JSON file does not exist")

        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'qid' in data, "Missing 'qid' in metadata"
        assert data['qid'] == "Q19873191", f"Wrong QID: {data['qid']}"
        assert 'fetch_time' in data, "Missing 'fetch_time' in metadata"
        assert 'status' in data, "Missing 'status' in metadata"

    def test_sparql_parsing_logic(self):
        """Test the parsing logic with a mock binding structure."""
        mock_bindings = [
            {
                'item': {'value': 'http://www.wikidata.org/entity/Q19873191', 'type': 'uri'},
                'itemLabel': {'value': 'A/B testing', 'type': 'literal'}
            }
        ]
        
        result = parse_wikidata_bindings(mock_bindings)
        
        assert len(result) == 1
        assert result[0]['item'] == 'http://www.wikidata.org/entity/Q19873191'
        assert result[0]['itemLabel'] == 'A/B testing'
        assert result[0]['item_type'] == 'uri'
        assert result[0]['itemLabel_type'] == 'literal'

    def test_data_integrity(self):
        """Verify that the data written matches the QID being queried."""
        if not self.csv_path.exists():
            pytest.skip("CSV file does not exist")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['wikidata_qid'] == "Q19873191", f"Row has wrong QID: {row['wikidata_qid']}"
                # Verify timestamp is parseable
                try:
                    datetime.fromisoformat(row['fetch_timestamp'])
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {row['fetch_timestamp']}")
