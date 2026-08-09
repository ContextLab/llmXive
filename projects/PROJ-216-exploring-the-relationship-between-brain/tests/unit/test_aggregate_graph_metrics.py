import os
import sys
import csv
import json
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from aggregate_graph_metrics import load_preprocessed_subjects, aggregate_metrics_to_csv, main

class TestAggregateGraphMetrics:
    def test_aggregate_metrics_to_csv_creates_file(self, tmp_path):
        """Test that aggregate_metrics_to_csv creates a valid CSV file."""
        metrics = [
            {"subject_id": "sub-001", "metric_name": "global_efficiency", "value": 0.45},
            {"subject_id": "sub-001", "metric_name": "clustering_coefficient", "value": 0.32},
            {"subject_id": "sub-002", "metric_name": "global_efficiency", "value": 0.48},
        ]
        
        output_path = tmp_path / "test_metrics.csv"
        aggregate_metrics_to_csv(metrics, output_path)
        
        assert output_path.exists(), "CSV file was not created"
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"
        assert rows[0]['subject_id'] == 'sub-001'
        assert rows[0]['metric_name'] == 'global_efficiency'
        assert float(rows[0]['value']) == 0.45
        
        assert rows[1]['metric_name'] == 'clustering_coefficient'
        assert rows[2]['subject_id'] == 'sub-002'

    def test_aggregate_metrics_empty_list(self, tmp_path):
        """Test handling of empty metrics list."""
        output_path = tmp_path / "empty_metrics.csv"
        aggregate_metrics_to_csv([], output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert "subject_id,metric_name,value" in content
        assert len(content.strip().split('\n')) == 1  # Only header

    def test_load_preprocessed_subjects_no_directory(self, tmp_path):
        """Test loading when processed directory does not exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        subjects = load_preprocessed_subjects(nonexistent_dir)
        assert subjects == []

    def test_load_preprocessed_subjects_filters_correctly(self, tmp_path):
        """Test that load_preprocessed_subjects correctly identifies subject directories."""
        # Create mock subject directories
        sub1 = tmp_path / "sub-001"
        sub1.mkdir()
        (sub1 / "sub-001_desc-preproc_bold.nii.gz").touch()
        
        sub2 = tmp_path / "sub-002"
        sub2.mkdir()
        (sub2 / "sub-002_desc-preproc_bold.nii.gz").touch()
        
        # Create a non-subject directory
        other = tmp_path / "logs"
        other.mkdir()
        
        subjects = load_preprocessed_subjects(tmp_path, max_subjects=10)
        
        assert len(subjects) == 2
        assert subjects[0]['subject_id'] == 'sub-001'
        assert subjects[1]['subject_id'] == 'sub-002'
        
        # Verify file paths exist
        assert Path(subjects[0]['file_path']).exists()
        assert Path(subjects[1]['file_path']).exists()

    def test_load_preprocessed_subjects_respects_limit(self, tmp_path):
        """Test that max_subjects limit is respected."""
        for i in range(1, 6):
            sub_dir = tmp_path / f"sub-{i:03d}"
            sub_dir.mkdir()
            (sub_dir / f"sub-{i:03d}_desc-preproc_bold.nii.gz").touch()
        
        # Request only 3 subjects
        subjects = load_preprocessed_subjects(tmp_path, max_subjects=3)
        assert len(subjects) == 3
        assert subjects[2]['subject_id'] == 'sub-003'
        
        # Request all
        subjects = load_preprocessed_subjects(tmp_path, max_subjects=10)
        assert len(subjects) == 5
