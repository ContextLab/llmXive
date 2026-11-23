"""
Unit tests for code/analysis/output_metrics.py
"""
import os
import json
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.output_metrics import (
    load_subject_metrics_from_cache,
    aggregate_metrics,
    write_metrics_csv,
    validate_schema
)

class TestLoadSubjectMetricsFromCache:
    def test_load_existing_metrics(self, tmp_path):
        """Test loading valid JSON files from cache."""
        # Create mock JSON files
        data1 = {"subject_id": "sub-01", "flexibility_DMN": 0.5}
        data2 = {"subject_id": "sub-02", "flexibility_DMN": 0.6}
        
        (tmp_path / "subject_sub-01.json").write_text(json.dumps(data1))
        (tmp_path / "subject_sub-02.json").write_text(json.dumps(data2))
        
        result = load_subject_metrics_from_cache(str(tmp_path))
        
        assert len(result) == 2
        assert result[0]['subject_id'] == 'sub-01'
        assert result[1]['subject_id'] == 'sub-02'
    
    def test_load_missing_directory(self, tmp_path):
        """Test behavior when cache directory does not exist."""
        result = load_subject_metrics_from_cache(str(tmp_path / "nonexistent"))
        assert result == []
    
    def test_load_invalid_json(self, tmp_path):
        """Test handling of invalid JSON files."""
        (tmp_path / "subject_bad.json").write_text("not json")
        (tmp_path / "subject_good.json").write_text(json.dumps({"subject_id": "sub-01"}))
        
        result = load_subject_metrics_from_cache(str(tmp_path))
        # Should log error but continue
        assert len(result) == 1
        assert result[0]['subject_id'] == 'sub-01'
    
    def test_missing_subject_id(self, tmp_path):
        """Test skipping files without subject_id."""
        (tmp_path / "subject_no_id.json").write_text(json.dumps({"value": 10}))
        
        result = load_subject_metrics_from_cache(str(tmp_path))
        assert len(result) == 0

class TestAggregateMetrics:
    def test_aggregate_with_missing_fields(self):
        """Test that aggregate_metrics fills in missing expected keys."""
        input_data = [
            {"subject_id": "sub-01", "flexibility_DMN": 0.5}
        ]
        
        result = aggregate_metrics(input_data)
        
        assert len(result) == 1
        assert result[0]['subject_id'] == 'sub-01'
        assert result[0]['flexibility_DMN'] == 0.5
        # Check that other expected keys are present (likely None)
        assert 'stability_DMN' in result[0]
        assert 'flexibility_Salience' in result[0]
    
    def test_aggregate_sorting(self):
        """Test that results are sorted by subject_id."""
        input_data = [
            {"subject_id": "sub-03"},
            {"subject_id": "sub-01"},
            {"subject_id": "sub-02"}
        ]
        
        result = aggregate_metrics(input_data)
        
        assert result[0]['subject_id'] == 'sub-01'
        assert result[1]['subject_id'] == 'sub-02'
        assert result[2]['subject_id'] == 'sub-03'

class TestWriteMetricsCsv:
    def test_write_valid_csv(self, tmp_path):
        """Test writing a valid CSV file."""
        data = [
            {"subject_id": "sub-01", "flexibility_DMN": 0.5, "stability_DMN": 10.0},
            {"subject_id": "sub-02", "flexibility_DMN": 0.6, "stability_DMN": 12.0}
        ]
        output_file = tmp_path / "metrics.csv"
        
        write_metrics_csv(data, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['subject_id'] == 'sub-01'
    
    def test_write_empty_list(self, tmp_path):
        """Test writing an empty list creates headers."""
        output_file = tmp_path / "metrics_empty.csv"
        
        write_metrics_csv([], str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert 'subject_id' in headers

class TestValidateSchema:
    def test_validate_pass(self, tmp_path):
        """Test successful validation against a mock schema."""
        # Create a mock schema
        schema = {
            "properties": {
                "subject_id": {"type": "string"},
                "flexibility_DMN": {"type": "number"}
            }
        }
        schema_file = tmp_path / "schema.yaml"
        import yaml
        schema_file.write_text(yaml.dump(schema))
        
        # Create a matching CSV
        csv_file = tmp_path / "metrics.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "flexibility_DMN"])
            writer.writeheader()
            writer.writerow({"subject_id": "s1", "flexibility_DMN": 0.5})
        
        assert validate_schema(str(csv_file), str(schema_file)) is True
    
    def test_validate_fail_missing_field(self, tmp_path):
        """Test validation failure when CSV is missing a required schema field."""
        schema = {
            "properties": {
                "subject_id": {"type": "string"},
                "missing_field": {"type": "number"}
            }
        }
        schema_file = tmp_path / "schema.yaml"
        import yaml
        schema_file.write_text(yaml.dump(schema))
        
        csv_file = tmp_path / "metrics.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id"])
            writer.writeheader()
            writer.writerow({"subject_id": "s1"})
        
        assert validate_schema(str(csv_file), str(schema_file)) is False
    
    def test_validate_missing_schema_file(self, tmp_path):
        """Test behavior when schema file is missing."""
        csv_file = tmp_path / "metrics.csv"
        csv_file.write_text("subject_id\ns1\n")
        
        # Should return True (skip validation) with a warning
        assert validate_schema(str(csv_file), str(tmp_path / "nonexistent.yaml")) is True