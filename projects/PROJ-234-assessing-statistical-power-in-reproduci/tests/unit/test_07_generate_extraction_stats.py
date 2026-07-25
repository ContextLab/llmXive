"""
Unit tests for code/07_generate_extraction_stats.py (Task T027).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from code import (
    load_extracted_params,
    generate_extraction_stats
)

class TestLoadExtractedParams:
    def test_load_valid_json(self):
        """Test loading a valid JSON file with records."""
        test_data = [
            {"dataset_id": 1, "status": "success"},
            {"dataset_id": 2, "status": "paywalled"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            result = load_extracted_params(temp_path)
            assert result == test_data
            assert len(result) == 2
        finally:
            os.unlink(temp_path)

    def test_load_empty_list(self):
        """Test loading an empty list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = f.name
        
        try:
            result = load_extracted_params(temp_path)
            assert result == []
            assert len(result) == 0
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_extracted_params("nonexistent_file.json")

    def test_load_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_extracted_params(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_non_list_json(self):
        """Test that ValueError is raised if JSON is not a list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_extracted_params(temp_path)
        finally:
            os.unlink(temp_path)

class TestGenerateExtractionStats:
    def test_all_success(self):
        """Test calculation when all records are successful."""
        records = [
            {"dataset_id": 1, "status": "success"},
            {"dataset_id": 2, "status": "success"},
            {"dataset_id": 3, "status": "success"}
        ]
        
        stats = generate_extraction_stats(records)
        
        assert stats["success_rate"] == 1.0
        assert stats["failure_reasons"]["paywalled"] == 0
        assert stats["failure_reasons"]["unparseable"] == 0
        assert stats["failure_reasons"]["insufficient data"] == 0

    def test_all_failures(self):
        """Test calculation when all records have failures."""
        records = [
            {"dataset_id": 1, "status": "paywalled"},
            {"dataset_id": 2, "status": "unparseable"},
            {"dataset_id": 3, "status": "insufficient data"}
        ]
        
        stats = generate_extraction_stats(records)
        
        assert stats["success_rate"] == 0.0
        assert stats["failure_reasons"]["paywalled"] == 1
        assert stats["failure_reasons"]["unparseable"] == 1
        assert stats["failure_reasons"]["insufficient data"] == 1

    def test_mixed_results(self):
        """Test calculation with mixed success and failure statuses."""
        records = [
            {"dataset_id": 1, "status": "success"},
            {"dataset_id": 2, "status": "success"},
            {"dataset_id": 3, "status": "paywalled"},
            {"dataset_id": 4, "status": "unparseable"},
            {"dataset_id": 5, "status": "success"},
            {"dataset_id": 6, "status": "insufficient data"},
            {"dataset_id": 7, "status": "paywalled"}
        ]
        
        stats = generate_extraction_stats(records)
        
        # 3 success out of 7
        assert abs(stats["success_rate"] - (3/7)) < 0.0001
        assert stats["failure_reasons"]["paywalled"] == 2
        assert stats["failure_reasons"]["unparseable"] == 1
        assert stats["failure_reasons"]["insufficient data"] == 1

    def test_empty_records(self):
        """Test calculation with empty list."""
        stats = generate_extraction_stats([])
        
        assert stats["success_rate"] == 0.0
        assert stats["failure_reasons"]["paywalled"] == 0
        assert stats["failure_reasons"]["unparseable"] == 0
        assert stats["failure_reasons"]["insufficient data"] == 0

    def test_unknown_status_treated_as_failure(self):
        """Test that unknown statuses are not counted as success."""
        records = [
            {"dataset_id": 1, "status": "success"},
            {"dataset_id": 2, "status": "unknown_status"},
            {"dataset_id": 3, "status": "another_unknown"}
        ]
        
        stats = generate_extraction_stats(records)
        
        # Only 1 success out of 3
        assert abs(stats["success_rate"] - (1/3)) < 0.0001
        # Unknown statuses are not counted in any specific failure reason
        assert stats["failure_reasons"]["paywalled"] == 0
        assert stats["failure_reasons"]["unparseable"] == 0
        assert stats["failure_reasons"]["insufficient data"] == 0

    def test_missing_status_field(self):
        """Test handling of records missing the status field."""
        records = [
            {"dataset_id": 1, "status": "success"},
            {"dataset_id": 2},  # No status
            {"dataset_id": 3, "status": "paywalled"}
        ]
        
        stats = generate_extraction_stats(records)
        
        # Only 1 success out of 3 (missing status is not success)
        assert abs(stats["success_rate"] - (1/3)) < 0.0001
        assert stats["failure_reasons"]["paywalled"] == 1