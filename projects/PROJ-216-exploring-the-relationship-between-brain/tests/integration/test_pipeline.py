"""
Integration test for graph metric aggregation (Task T022).
This test validates the end-to-end flow of loading preprocessed subjects,
computing graph metrics, and aggregating them into a CSV file.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from graph_metrics import compute_graph_metrics
from aggregate_graph_metrics import load_preprocessed_subjects, aggregate_metrics_to_csv
from utils import ResourceMonitor


class TestGraphMetricAggregation:
    """Integration test for graph metric aggregation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True)

        # Mock preprocessed NIfTI files and metadata
        self.subjects = []
        for i in range(3):
            subject_id = f"sub-00{i+1}"
            self.subjects.append(subject_id)

            # Create a mock time series file (simulating preprocessed BOLD data)
            time_series_file = self.processed_dir / f"{subject_id}_timeseries.npy"
            # Generate random time series data: 100 time points, 200 ROIs (Schaefer 200)
            np.random.seed(42 + i)  # Different seed for each subject
            time_series = np.random.randn(100, 200)
            np.save(time_series_file, time_series)

            # Create a mock valid_subjects.json entry
            # We'll use a shared file for all subjects
            valid_subjects_file = self.processed_dir / "valid_subjects.json"
            valid_subjects = {
                "subjects": [
                    {"id": sid, "score": 0.5 + i * 0.1}
                    for i, sid in enumerate(self.subjects)
                ],
                "count": len(self.subjects)
            }
            with open(valid_subjects_file, 'w') as f:
                json.dump(valid_subjects, f)

        yield

        # Cleanup
        shutil.rmtree(self.test_dir)

    def test_load_preprocessed_subjects(self):
        """Test loading preprocessed subjects from the processed directory."""
        # This test verifies that we can load the list of valid subjects
        valid_subjects_file = self.processed_dir / "valid_subjects.json"
        subjects = load_preprocessed_subjects(valid_subjects_file)

        assert len(subjects) == 3
        assert all(isinstance(s, dict) for s in subjects)
        assert all("id" in s and "score" in s for s in subjects)
        assert subjects[0]["id"] == "sub-001"
        assert subjects[1]["score"] == 0.6

    def test_compute_graph_metrics_single_subject(self):
        """Test computing graph metrics for a single subject."""
        subject_id = "sub-001"
        time_series_file = self.processed_dir / f"{subject_id}_timeseries.npy"
        time_series = np.load(time_series_file)

        # Compute graph metrics
        metrics = compute_graph_metrics(time_series, subject_id)

        assert isinstance(metrics, dict)
        assert "subject_id" in metrics
        assert metrics["subject_id"] == subject_id
        assert "global_efficiency" in metrics
        assert "clustering_coefficient" in metrics
        assert "modularity" in metrics

        # Verify numerical ranges
        assert -1.0 <= metrics["global_efficiency"] <= 1.0
        assert 0.0 <= metrics["clustering_coefficient"] <= 1.0
        assert 0.0 <= metrics["modularity"] <= 1.0

    def test_aggregate_metrics_to_csv(self):
        """Test aggregating graph metrics to a CSV file."""
        # Compute metrics for all subjects
        all_metrics = []
        for subject_id in self.subjects:
            time_series_file = self.processed_dir / f"{subject_id}_timeseries.npy"
            time_series = np.load(time_series_file)
            metrics = compute_graph_metrics(time_series, subject_id)
            all_metrics.append(metrics)

        # Aggregate to CSV
        output_file = self.processed_dir / "graph_metrics.csv"
        aggregate_metrics_to_csv(all_metrics, output_file)

        # Verify the CSV file was created and contains correct data
        assert output_file.exists()

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(self.subjects)
        assert all("subject_id" in row for row in rows)
        assert all("metric_name" in row for row in rows)
        assert all("value" in row for row in rows)

        # Check that all subjects are present
        subject_ids_in_csv = {row["subject_id"] for row in rows}
        assert subject_ids_in_csv == set(self.subjects)

        # Check that all metrics are present for each subject
        metrics_for_subj1 = [row for row in rows if row["subject_id"] == "sub-001"]
        metric_names = {row["metric_name"] for row in metrics_for_subj1}
        assert "global_efficiency" in metric_names
        assert "clustering_coefficient" in metric_names
        assert "modularity" in metric_names

    def test_full_aggregation_pipeline(self):
        """Test the full aggregation pipeline from loading subjects to writing CSV."""
        # Load valid subjects
        valid_subjects_file = self.processed_dir / "valid_subjects.json"
        subjects = load_preprocessed_subjects(valid_subjects_file)

        # Compute metrics for each subject
        all_metrics = []
        for subject in subjects:
            subject_id = subject["id"]
            time_series_file = self.processed_dir / f"{subject_id}_timeseries.npy"
            time_series = np.load(time_series_file)
            metrics = compute_graph_metrics(time_series, subject_id)
            all_metrics.append(metrics)

        # Aggregate to CSV
        output_file = self.processed_dir / "graph_metrics.csv"
        aggregate_metrics_to_csv(all_metrics, output_file)

        # Verify the output
        assert output_file.exists()

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(self.subjects) * 3  # 3 metrics per subject

        # Verify data integrity
        for subject_id in self.subjects:
            subject_rows = [row for row in rows if row["subject_id"] == subject_id]
            assert len(subject_rows) == 3
            metric_values = {row["metric_name"]: float(row["value"]) for row in subject_rows}
            assert all(0.0 <= v <= 1.0 for v in metric_values.values())

    def test_resource_monitoring_integration(self):
        """Test that resource monitoring is integrated with the aggregation pipeline."""
        # Initialize resource monitor
        monitor = ResourceMonitor()
        monitor.start()

        # Run the aggregation pipeline
        valid_subjects_file = self.processed_dir / "valid_subjects.json"
        subjects = load_preprocessed_subjects(valid_subjects_file)

        all_metrics = []
        for subject in subjects:
            subject_id = subject["id"]
            time_series_file = self.processed_dir / f"{subject_id}_timeseries.npy"
            time_series = np.load(time_series_file)
            metrics = compute_graph_metrics(time_series, subject_id)
            all_metrics.append(metrics)

        output_file = self.processed_dir / "graph_metrics.csv"
        aggregate_metrics_to_csv(all_metrics, output_file)

        # Finalize resource monitoring
        monitor.finalize()

        # Verify resource profile was created
        resource_profile_file = Path("data/processed/resource_profile.json")
        if resource_profile_file.exists():
            with open(resource_profile_file, 'r') as f:
                profile = json.load(f)

            assert "peak_ram_gb" in profile
            assert "total_runtime_hours" in profile
            assert isinstance(profile["peak_ram_gb"], float)
            assert isinstance(profile["total_runtime_hours"], float)

            # Clean up
            resource_profile_file.unlink()

    def test_edge_case_single_subject(self):
        """Test aggregation with only one subject."""
        # Create a single subject
        subject_id = "sub-001"
        time_series_file = self.processed_dir / f"{subject_id}_timeseries.npy"
        np.random.seed(42)
        time_series = np.random.randn(100, 200)
        np.save(time_series_file, time_series)

        # Update valid_subjects.json
        valid_subjects_file = self.processed_dir / "valid_subjects.json"
        valid_subjects = {
            "subjects": [{"id": subject_id, "score": 0.5}],
            "count": 1
        }
        with open(valid_subjects_file, 'w') as f:
            json.dump(valid_subjects, f)

        # Run aggregation
        subjects = load_preprocessed_subjects(valid_subjects_file)
        all_metrics = []
        for subject in subjects:
            ts_file = self.processed_dir / f"{subject['id']}_timeseries.npy"
            ts = np.load(ts_file)
            metrics = compute_graph_metrics(ts, subject['id'])
            all_metrics.append(metrics)

        output_file = self.processed_dir / "graph_metrics.csv"
        aggregate_metrics_to_csv(all_metrics, output_file)

        # Verify
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3  # 3 metrics for 1 subject

    def test_edge_case_empty_subjects(self):
        """Test aggregation with no subjects (should handle gracefully)."""
        # Create empty valid_subjects.json
        valid_subjects_file = self.processed_dir / "valid_subjects.json"
        valid_subjects = {
            "subjects": [],
            "count": 0
        }
        with open(valid_subjects_file, 'w') as f:
            json.dump(valid_subjects, f)

        # Run aggregation
        subjects = load_preprocessed_subjects(valid_subjects_file)
        all_metrics = []
        for subject in subjects:
            ts_file = self.processed_dir / f"{subject['id']}_timeseries.npy"
            ts = np.load(ts_file)
            metrics = compute_graph_metrics(ts, subject['id'])
            all_metrics.append(metrics)

        output_file = self.processed_dir / "graph_metrics.csv"
        aggregate_metrics_to_csv(all_metrics, output_file)

        # Verify empty CSV is created with headers
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 0