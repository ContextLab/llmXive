import os
import json
import tempfile
import pytest
import csv
from pathlib import Path
import time

from analysis.timing import (
    format_duration, 
    record_execution_time, 
    write_timing_to_results,
    get_current_timestamp
)
from config import load_config

class TestTimingUtils:
    def test_format_duration_seconds(self):
        assert format_duration(5) == "00:00:05.000"
    
    def test_format_duration_minutes(self):
        assert format_duration(65) == "00:01:05.000"
    
    def test_format_duration_hours(self):
        assert format_duration(3665) == "01:01:05.000"
    
    def test_format_duration_precision(self):
        result = format_duration(1.23456)
        assert "1.235" in result

class TestRecordExecutionTime:
    def test_record_execution_time_calculation(self):
        start = 100.0
        end = 110.5
        config = {"pipeline": {"version": "1.0.0"}}
        
        result = record_execution_time(start, end, config)
        
        assert result["total_execution_time_seconds"] == 10.5
        assert result["pipeline_version"] == "1.0.0"
        assert "start_timestamp" in result
        assert "end_timestamp" in result

class TestWriteTimingToResults:
    @pytest.fixture
    def temp_csv_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "results.csv"

    def test_write_creates_file_with_headers(self, temp_csv_path):
        timing_data = {
            "total_execution_time_seconds": 10.0,
            "total_execution_time_formatted": "00:00:10.000",
            "timestamp_recorded": "2023-01-01T00:00:00"
        }
        
        write_timing_to_results(timing_data, temp_csv_path)
        
        assert temp_csv_path.exists()
        
        with open(temp_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["metric_name"] == "SC-005_total_execution_time"
            assert float(rows[0]["metric_value"]) == 10.0

    def test_write_appends_to_existing_file(self, temp_csv_path):
        # Write first row
        timing_data_1 = {
            "total_execution_time_seconds": 10.0,
            "timestamp_recorded": "2023-01-01T00:00:00"
        }
        write_timing_to_results(timing_data_1, temp_csv_path)
        
        # Write second row
        timing_data_2 = {
            "total_execution_time_seconds": 20.0,
            "timestamp_recorded": "2023-01-01T00:00:01"
        }
        write_timing_to_results(timing_data_2, temp_csv_path)
        
        with open(temp_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert float(rows[1]["metric_value"]) == 20.0

    def test_write_includes_details_json(self, temp_csv_path):
        timing_data = {
            "total_execution_time_seconds": 15.5,
            "timestamp_recorded": "2023-01-01T00:00:00"
        }
        
        write_timing_to_results(timing_data, temp_csv_path)
        
        with open(temp_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            details = json.loads(rows[0]["details"])
            assert details["total_execution_time_seconds"] == 15.5