"""
Unit tests for Sensitivity Analysis (T020).
"""
import os
import csv
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
# Note: We need to adjust the import path to match the project structure
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from analysis.sensitivity_analysis import (
    load_results_from_csv,
    compute_aggregate_stats,
    run_sensitivity_analysis,
    THRESHOLD_RANGE
)

class TestLoadResultsFromCsv:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_file = tmp_path / "test.csv"
        data = [
            {"task_id": "1", "accuracy": "0.8", "nodes_visited": "10", "latency_ms": "100.0", "evidence_threshold": "0.7"},
            {"task_id": "2", "accuracy": "0.9", "nodes_visited": "12", "latency_ms": "110.0", "evidence_threshold": "0.7"}
        ]
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        results = load_results_from_csv(csv_file)
        
        assert len(results) == 2
        assert results[0]['accuracy'] == 0.8
        assert results[0]['evidence_threshold'] == 0.7
        assert results[0]['task_id'] == "1"

    def test_load_missing_file(self, tmp_path):
        """Test that loading a missing file returns empty list."""
        results = load_results_from_csv(tmp_path / "nonexistent.csv")
        assert results == []

    def test_load_invalid_numeric(self, tmp_path):
        """Test handling of invalid numeric values."""
        csv_file = tmp_path / "test.csv"
        data = [
            {"task_id": "1", "accuracy": "invalid", "nodes_visited": "10", "latency_ms": "100.0", "evidence_threshold": "0.7"}
        ]
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        results = load_results_from_csv(csv_file)
        assert len(results) == 1
        assert results[0]['accuracy'] is None
        assert results[0]['nodes_visited'] == 10.0

class TestComputeAggregateStats:
    def test_compute_stats_basic(self):
        """Test basic aggregation logic."""
        results = [
            {"accuracy": 0.8, "nodes_visited": 10, "latency_ms": 100.0, "evidence_threshold": 0.7},
            {"accuracy": 0.9, "nodes_visited": 12, "latency_ms": 110.0, "evidence_threshold": 0.7},
            {"accuracy": 0.5, "nodes_visited": 5, "latency_ms": 50.0, "evidence_threshold": 0.3} # Should not match 0.7
        ]
        
        stats = compute_aggregate_stats(results, 0.7)
        
        assert stats['threshold'] == 0.7
        assert stats['count'] == 2
        assert abs(stats['mean_accuracy'] - 0.85) < 0.001
        assert abs(stats['mean_nodes_visited'] - 11.0) < 0.001
        assert abs(stats['mean_latency_ms'] - 105.0) < 0.001

    def test_compute_stats_no_matches(self):
        """Test aggregation when no results match the threshold."""
        results = [
            {"accuracy": 0.8, "nodes_visited": 10, "latency_ms": 100.0, "evidence_threshold": 0.5}
        ]
        
        stats = compute_aggregate_stats(results, 0.7)
        
        assert stats['count'] == 0
        assert stats['mean_accuracy'] is None
        assert stats['mean_nodes_visited'] is None
        assert stats['completion_rate'] == 0.0

    def test_compute_stats_tolerance(self):
        """Test that tolerance works for floating point thresholds."""
        results = [
            {"accuracy": 0.8, "nodes_visited": 10, "latency_ms": 100.0, "evidence_threshold": 0.71} # Within 0.05 of 0.7
        ]
        
        stats = compute_aggregate_stats(results, 0.7)
        
        assert stats['count'] == 1
        assert stats['mean_accuracy'] == 0.8

    def test_compute_stats_with_nulls(self):
        """Test handling of null values in aggregation."""
        results = [
            {"accuracy": 0.8, "nodes_visited": 10, "latency_ms": 100.0, "evidence_threshold": 0.7},
            {"accuracy": None, "nodes_visited": 12, "latency_ms": 110.0, "evidence_threshold": 0.7},
            {"accuracy": 0.9, "nodes_visited": None, "latency_ms": 110.0, "evidence_threshold": 0.7}
        ]
        
        stats = compute_aggregate_stats(results, 0.7)
        
        assert stats['count'] == 3
        # Mean accuracy should only consider non-null: (0.8 + 0.9) / 2 = 0.85
        assert abs(stats['mean_accuracy'] - 0.85) < 0.001
        # Mean nodes should only consider non-null: 10 / 1 = 10.0
        assert abs(stats['mean_nodes_visited'] - 10.0) < 0.001
        assert stats['completion_rate'] == 2.0 / 3.0

class TestRunSensitivityAnalysis:
    @pytest.fixture
    def mock_csv_files(self, tmp_path):
        """Create mock CSV files for testing."""
        clean_file = tmp_path / "lazy_results.csv"
        noisy_file = tmp_path / "noisy_lazy_results.csv"
        
        # Write mock clean data
        with open(clean_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "accuracy", "nodes_visited", "latency_ms", "evidence_threshold"])
            writer.writeheader()
            writer.writerows([
                {"task_id": "1", "accuracy": "0.8", "nodes_visited": "10", "latency_ms": "100.0", "evidence_threshold": "0.7"},
                {"task_id": "2", "accuracy": "0.9", "nodes_visited": "12", "latency_ms": "110.0", "evidence_threshold": "0.7"},
                {"task_id": "3", "accuracy": "0.6", "nodes_visited": "8", "latency_ms": "80.0", "evidence_threshold": "0.3"}
            ])
        
        # Write mock noisy data
        with open(noisy_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "accuracy", "nodes_visited", "latency_ms", "evidence_threshold"])
            writer.writeheader()
            writer.writerows([
                {"task_id": "1", "accuracy": "0.7", "nodes_visited": "15", "latency_ms": "120.0", "evidence_threshold": "0.7"},
                {"task_id": "2", "accuracy": "0.8", "nodes_visited": "14", "latency_ms": "130.0", "evidence_threshold": "0.7"}
            ])
        
        return tmp_path

    def test_run_analysis_creates_output(self, mock_csv_files, tmp_path):
        """Test that the analysis function creates the output CSV."""
        # Temporarily override the DATA_DIR
        import analysis.sensitivity_analysis as sens_module
        original_data_dir = sens_module.DATA_DIR
        
        try:
            # Point to our temp directory
            sens_module.DATA_DIR = mock_csv_files
            output_file = mock_csv_files / "sensitivity_analysis.csv"
            sens_module.OUTPUT_FILE = output_file
            
            success = sens_module.run_sensitivity_analysis()
            
            assert success is True
            assert output_file.exists()
            
            # Verify content
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have entries for each threshold in both datasets
            # THRESHOLD_RANGE has 5 items, 2 datasets = 10 rows
            assert len(rows) == 10
            
            # Check for expected columns
            expected_cols = ['dataset', 'threshold', 'count', 'mean_accuracy', 'std_accuracy', 'mean_nodes_visited', 'mean_latency_ms', 'completion_rate']
            assert all(col in rows[0].keys() for col in expected_cols)
            
        finally:
            # Restore original
            sens_module.DATA_DIR = original_data_dir
            sens_module.OUTPUT_FILE = original_data_dir / "sensitivity_analysis.csv"

    def test_run_analysis_empty_input(self, tmp_path):
        """Test handling when input files are missing."""
        import analysis.sensitivity_analysis as sens_module
        original_data_dir = sens_module.DATA_DIR
        
        try:
            sens_module.DATA_DIR = tmp_path
            output_file = tmp_path / "sensitivity_analysis.csv"
            sens_module.OUTPUT_FILE = output_file
            
            success = sens_module.run_sensitivity_analysis()
            
            # Should still succeed but produce empty/zero rows
            assert success is True
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have rows for each threshold, but count=0
            assert len(rows) == 10 # 5 thresholds * 2 datasets
            for row in rows:
                assert int(row['count']) == 0
                assert row['mean_accuracy'] == '' # None becomes empty string in CSV
            
        finally:
            sens_module.DATA_DIR = original_data_dir
            sens_module.OUTPUT_FILE = original_data_dir / "sensitivity_analysis.csv"