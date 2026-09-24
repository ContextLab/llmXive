import pytest
import os
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from pipeline.handle_dropouts import (
    load_merged_data,
    identify_dropouts,
    extract_baseline_for_descriptive,
    generate_exclusions_json,
    write_exclusions_json,
    write_baseline_csv,
    run_dropout_handling
)

class TestLoadMergedData:
    def test_load_merged_data_success(self, tmp_path):
        """Test successful loading of merged data."""
        # Create test data
        test_data = [
            {"participant_id": "P001", "post_intervention_value": "10.5", "baseline_value": "8.2"},
            {"participant_id": "P002", "post_intervention_value": "", "baseline_value": "9.1"}
        ]
        
        file_path = tmp_path / "merged_data.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_data[0].keys())
            writer.writeheader()
            writer.writerows(test_data)
        
        result = load_merged_data(file_path)
        assert len(result) == 2
        assert result[0]["participant_id"] == "P001"
        
    def test_load_merged_data_not_found(self, tmp_path):
        """Test error when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_merged_data(tmp_path / "nonexistent.csv")
            
    def test_load_merged_data_empty(self, tmp_path):
        """Test handling of empty file."""
        file_path = tmp_path / "empty.csv"
        file_path.touch()
        
        result = load_merged_data(file_path)
        assert result == []

class TestIdentifyDropouts:
    def test_identify_dropouts_with_missing_data(self):
        """Test identification of dropouts with various missing data formats."""
        test_data = [
            {"participant_id": "P001", "post_intervention_value": "10.5", "baseline_value": "8.2"},
            {"participant_id": "P002", "post_intervention_value": "", "baseline_value": "9.1"},
            {"participant_id": "P003", "post_intervention_value": None, "baseline_value": "7.5"},
            {"participant_id": "P004", "post_intervention_value": "NaN", "baseline_value": "6.8"},
            {"participant_id": "P005", "post_intervention_value": "null", "baseline_value": "5.2"}
        ]
        
        dropouts = identify_dropouts(test_data)
        
        assert len(dropouts) == 4
        dropout_ids = [d["participant_id"] for d in dropouts]
        assert "P001" not in dropout_ids
        assert "P002" in dropout_ids
        assert "P003" in dropout_ids
        assert "P004" in dropout_ids
        assert "P005" in dropout_ids
        
        # Check reason
        for dropout in dropouts:
            assert dropout["reason"] == "missing_post_data"

    def test_identify_dropouts_empty(self):
        """Test with empty input."""
        dropouts = identify_dropouts([])
        assert dropouts == []

class TestExtractBaselineForDescriptive:
    def test_extract_baseline_all_participants(self):
        """Test extraction of baseline data for all participants."""
        test_data = [
            {"participant_id": "P001", "post_intervention_value": "10.5", "baseline_value": "8.2", "age": 25},
            {"participant_id": "P002", "post_intervention_value": "", "baseline_value": "9.1", "age": 30},
            {"participant_id": "P003", "post_intervention_value": "12.0", "baseline_value": "7.5", "age": 28}
        ]
        
        baseline = extract_baseline_for_descriptive(test_data)
        
        assert len(baseline) == 3
        participant_ids = [b["participant_id"] for b in baseline]
        assert "P001" in participant_ids
        assert "P002" in participant_ids
        assert "P003" in participant_ids
        
        # Verify post values are not included
        for record in baseline:
            assert "post_intervention_value" not in record

    def test_extract_baseline_duplicates(self):
        """Test that duplicate participant IDs are handled."""
        test_data = [
            {"participant_id": "P001", "post_intervention_value": "10.5", "baseline_value": "8.2"},
            {"participant_id": "P001", "post_intervention_value": "11.0", "baseline_value": "8.5"},
            {"participant_id": "P002", "post_intervention_value": "12.0", "baseline_value": "9.0"}
        ]
        
        baseline = extract_baseline_for_descriptive(test_data)
        
        # Should only have unique IDs
        assert len(baseline) == 2

class TestGenerateExclusionsJson:
    def test_generate_exclusions_structure(self):
        """Test the structure of generated exclusions JSON."""
        dropouts = [
            {"participant_id": "P001", "reason": "missing_post_data"},
            {"participant_id": "P002", "reason": "missing_post_data"}
        ]
        
        exclusions = generate_exclusions_json(dropouts)
        
        assert "excluded_participants" in exclusions
        assert "summary" in exclusions
        assert exclusions["summary"]["total_excluded"] == 2
        assert "missing_post_data" in exclusions["summary"]["reasons"]
        assert exclusions["summary"]["reasons"]["missing_post_data"] == 2

    def test_generate_exclusions_empty(self):
        """Test with empty dropouts list."""
        exclusions = generate_exclusions_json([])
        assert exclusions["summary"]["total_excluded"] == 0

class TestWriteExclusionsJson:
    def test_write_exclusions_file(self, tmp_path):
        """Test writing exclusions to JSON file."""
        exclusions = {
            "excluded_participants": [
                {"participant_id": "P001", "reason": "missing_post_data"}
            ],
            "summary": {"total_excluded": 1, "reasons": {"missing_post_data": 1}}
        }
        
        file_path = tmp_path / "exclusions.json"
        result_path = write_exclusions_json(exclusions, file_path)
        
        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
            assert data["summary"]["total_excluded"] == 1

class TestWriteBaselineCsv:
    def test_write_baseline_file(self, tmp_path):
        """Test writing baseline data to CSV file."""
        baseline_data = [
            {"participant_id": "P001", "baseline_value": "8.2", "age": 25},
            {"participant_id": "P002", "baseline_value": "9.1", "age": 30}
        ]
        
        file_path = tmp_path / "descriptive_baseline.csv"
        result_path = write_baseline_csv(baseline_data, file_path)
        
        assert result_path.exists()
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["participant_id"] == "P001"

    def test_write_baseline_empty(self, tmp_path):
        """Test writing empty baseline data."""
        file_path = tmp_path / "empty_baseline.csv"
        result_path = write_baseline_csv([], file_path)
        
        assert result_path.exists()

class TestRunDropoutHandling:
    def test_full_pipeline(self, tmp_path):
        """Test the complete dropout handling pipeline."""
        # Create test merged data
        merged_data = [
            {"participant_id": "P001", "post_intervention_value": "10.5", "baseline_value": "8.2", "age": 25},
            {"participant_id": "P002", "post_intervention_value": "", "baseline_value": "9.1", "age": 30},
            {"participant_id": "P003", "post_intervention_value": "12.0", "baseline_value": "7.5", "age": 28}
        ]
        
        merged_file = tmp_path / "merged_data.csv"
        with open(merged_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=merged_data[0].keys())
            writer.writeheader()
            writer.writerows(merged_data)
        
        exclusions_file = tmp_path / "exclusions.json"
        baseline_file = tmp_path / "descriptive_baseline.csv"
        
        exclusions, excl_path, base_path = run_dropout_handling(
            merged_data_path=merged_file,
            exclusions_path=exclusions_file,
            baseline_path=baseline_file
        )
        
        # Verify outputs
        assert excl_path.exists()
        assert base_path.exists()
        assert exclusions["summary"]["total_excluded"] == 1
        assert len(exclusions["excluded_participants"]) == 1
        assert exclusions["excluded_participants"][0]["participant_id"] == "P002"
        
        # Verify baseline contains all participants
        with open(base_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3

    def test_pipeline_with_no_dropouts(self, tmp_path):
        """Test pipeline when there are no dropouts."""
        merged_data = [
            {"participant_id": "P001", "post_intervention_value": "10.5", "baseline_value": "8.2"},
            {"participant_id": "P002", "post_intervention_value": "11.0", "baseline_value": "9.0"}
        ]
        
        merged_file = tmp_path / "merged_data.csv"
        with open(merged_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=merged_data[0].keys())
            writer.writeheader()
            writer.writerows(merged_data)
        
        exclusions_file = tmp_path / "exclusions.json"
        baseline_file = tmp_path / "descriptive_baseline.csv"
        
        exclusions, _, _ = run_dropout_handling(
            merged_data_path=merged_file,
            exclusions_path=exclusions_file,
            baseline_path=baseline_file
        )
        
        assert exclusions["summary"]["total_excluded"] == 0
