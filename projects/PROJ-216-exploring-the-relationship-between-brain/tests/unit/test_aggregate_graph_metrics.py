import os
import sys
import csv
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregate_graph_metrics import aggregate_metrics_to_csv

class TestAggregateGraphMetrics:
    
    def test_csv_structure_and_headers(self, tmp_path):
        """
        Test that the aggregate function creates a CSV with the correct headers
        and structure.
        """
        # Mock data
        mock_subjects = [
            {"subject_id": "sub-001", "path": "/fake/path.nii.gz"},
            {"subject_id": "sub-002", "path": "/fake/path2.nii.gz"}
        ]
        
        # We need to mock the compute_graph_metrics function to avoid real processing
        # Since we can't easily mock inside the function without import hacking,
        # we will test the file writing logic assuming the function returns data.
        # However, the function aggregate_metrics_to_csv calls compute_graph_metrics.
        # To test this unit, we need to patch compute_graph_metrics.
        
        # Alternative: Test the file I/O logic by creating a version that accepts metrics
        # But the task requires implementing the script that calls compute_graph_metrics.
        # Let's test the file format generation by mocking the dependency.
        
        from unittest.mock import patch, MagicMock
        
        output_file = tmp_path / "test_metrics.csv"
        
        mock_metrics_1 = {
            "global_efficiency": 0.45,
            "clustering_coefficient": 0.32,
            "modularity": 0.65
        }
        mock_metrics_2 = {
            "global_efficiency": 0.48,
            "clustering_coefficient": 0.35,
            "modularity": 0.68
        }
        
        with patch("aggregate_graph_metrics.compute_graph_metrics") as mock_compute:
            mock_compute.side_effect = [mock_metrics_1, mock_metrics_2]
            
            aggregate_metrics_to_csv(mock_subjects, str(output_file))
            
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 6 # 2 subjects * 3 metrics
            
            # Check headers
            assert "subject_id" in reader.fieldnames
            assert "metric_name" in reader.fieldnames
            assert "value" in reader.fieldnames
            
            # Check content for first subject
            sub1_rows = [r for r in rows if r["subject_id"] == "sub-001"]
            assert len(sub1_rows) == 3
            assert sub1_rows[0]["metric_name"] in mock_metrics_1
            assert float(sub1_rows[0]["value"]) > 0

    def test_empty_subject_list(self, tmp_path):
        """Test that an empty subject list produces a valid CSV with headers only."""
        output_file = tmp_path / "empty_metrics.csv"
        
        aggregate_metrics_to_csv([], str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ["subject_id", "metric_name", "value"]
            # Should be no more rows
            assert len(list(reader)) == 0