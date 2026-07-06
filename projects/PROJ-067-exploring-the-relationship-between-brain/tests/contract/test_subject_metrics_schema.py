"""
Contract test for subject_metrics.csv schema (T031).

Verifies that the output CSV file adheres to the required schema:
- Headers: subject_id, network_name, flexibility, stability
- Types: string, string, float, float
- Non-empty rows
"""
import os
import csv
import pytest
from pathlib import Path

OUTPUT_FILE = Path("data/metrics/subject_metrics.csv")

class TestSubjectMetricsSchema:
    
    @pytest.fixture(scope="class")
    def csv_data(self):
        """Load the CSV data if it exists."""
        if not OUTPUT_FILE.exists():
            pytest.skip(f"Output file {OUTPUT_FILE} does not exist. Run T031 first.")
        
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def test_file_exists(self):
        """Ensure the output file exists."""
        assert OUTPUT_FILE.exists(), f"Output file {OUTPUT_FILE} not found."

    def test_required_headers(self, csv_data):
        """Verify the CSV contains all required headers."""
        expected_headers = {"subject_id", "network_name", "flexibility", "stability"}
        if not csv_data:
            # If file exists but is empty of rows, check headers
            with open(OUTPUT_FILE, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                assert set(headers) == expected_headers, f"Headers mismatch: {headers} vs {expected_headers}"
            return
        
        actual_headers = set(csv_data[0].keys())
        assert actual_headers == expected_headers, \
            f"Expected headers {expected_headers}, got {actual_headers}"

    def test_subject_id_type(self, csv_data):
        """Verify subject_id is a non-empty string."""
        for row in csv_data:
            sid = row["subject_id"]
            assert isinstance(sid, str), f"subject_id is not string: {type(sid)}"
            assert len(sid) > 0, "subject_id is empty"

    def test_network_name_type(self, csv_data):
        """Verify network_name is a non-empty string."""
        for row in csv_data:
            net = row["network_name"]
            assert isinstance(net, str), f"network_name is not string: {type(net)}"
            assert len(net) > 0, "network_name is empty"

    def test_flexibility_numeric(self, csv_data):
        """Verify flexibility is a valid number."""
        for row in csv_data:
            val = row["flexibility"]
            try:
                float(val)
            except ValueError:
                pytest.fail(f"flexibility value '{val}' is not numeric")

    def test_stability_numeric(self, csv_data):
        """Verify stability is a valid number."""
        for row in csv_data:
            val = row["stability"]
            try:
                float(val)
            except ValueError:
                pytest.fail(f"stability value '{val}' is not numeric")

    def test_non_empty_dataset(self, csv_data):
        """Ensure there is at least one row of data."""
        assert len(csv_data) > 0, "CSV file contains no data rows."
