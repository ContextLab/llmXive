"""
Unit tests for centrality metric calculation logic.
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Import the functions to test
try:
    from code.centrality.metrics import (
        load_connectivity_matrix,
        load_roi_labels,
        calculate_centrality_metrics,
        process_participant_centrality,
        run_centrality_pipeline
    )
except ImportError:
    from centrality.metrics import (
        load_connectivity_matrix,
        load_roi_labels,
        calculate_centrality_metrics,
        process_participant_centrality,
        run_centrality_pipeline
    )


class TestLoadConnectivityMatrix:
    def test_load_valid_matrix(self):
        """Test loading a valid connectivity matrix."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow([1.0, 0.5, 0.2])
            writer.writerow([0.5, 1.0, 0.3])
            writer.writerow([0.2, 0.3, 1.0])
            temp_path = f.name

        try:
            matrix = load_connectivity_matrix(temp_path)
            assert matrix.shape == (3, 3)
            assert np.allclose(matrix[0, 1], 0.5)
            assert np.allclose(matrix[1, 1], 1.0)
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_connectivity_matrix('nonexistent_file.csv')

    def test_load_empty_file(self):
        """Test that loading an empty file raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_connectivity_matrix(temp_path)
        finally:
            os.unlink(temp_path)


class TestLoadROILabels:
    def test_load_json_labels(self):
        """Test loading ROI labels from a JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(["ROI1", "ROI2", "ROI3"], f)
            temp_path = f.name

        try:
            labels = load_roi_labels(temp_path)
            assert labels == ["ROI1", "ROI2", "ROI3"]
        finally:
            os.unlink(temp_path)

    def test_load_json_labels_dict(self):
        """Test loading ROI labels from a JSON file with a 'labels' key."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"labels": ["ROI1", "ROI2", "ROI3"]}, f)
            temp_path = f.name

        try:
            labels = load_roi_labels(temp_path)
            assert labels == ["ROI1", "ROI2", "ROI3"]
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_labels(self):
        """Test that loading a nonexistent labels file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_roi_labels('nonexistent_labels.json')


class TestCalculateCentralityMetrics:
    def test_calculate_metrics_simple(self):
        """Test centrality calculation on a simple 3x3 matrix."""
        matrix = np.array([
            [1.0, 0.8, 0.2],
            [0.8, 1.0, 0.5],
            [0.2, 0.5, 1.0]
        ])

        metrics = calculate_centrality_metrics(matrix)

        assert 'degree' in metrics
        assert 'betweenness' in metrics
        assert 'closeness' in metrics

        assert len(metrics['degree']) == 3
        assert len(metrics['betweenness']) == 3
        assert len(metrics['closeness']) == 3

        # Check that values are non-negative and normalized (roughly)
        assert all(0 <= v <= 1 for v in metrics['degree'])
        assert all(0 <= v <= 1 for v in metrics['betweenness'])
        # Closeness can be >1 if not normalized, but in our implementation it should be <=1
        assert all(0 <= v for v in metrics['closeness'])

    def test_calculate_metrics_non_square(self):
        """Test that a non-square matrix raises ValueError."""
        matrix = np.array([[1.0, 0.5], [0.5, 1.0], [0.2, 0.3]])
        with pytest.raises(ValueError):
            calculate_centrality_metrics(matrix)


class TestProcessParticipantCentrality:
    def test_process_single_participant(self):
        """Test processing a single participant's centrality."""
        # Create temporary directory and files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create connectivity matrix
            matrix_path = tmpdir / "corr_matrix_P001.csv"
            with open(matrix_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([1.0, 0.8, 0.2])
                writer.writerow([0.8, 1.0, 0.5])
                writer.writerow([0.2, 0.5, 1.0])

            # Create ROI labels
            labels_path = tmpdir / "roi_labels.json"
            with open(labels_path, 'w') as f:
                json.dump(["ROI1", "ROI2", "ROI3"], f)

            # Output path
            output_path = tmpdir / "centrality_P001.csv"

            # Process
            result = process_participant_centrality(
                matrix_path=str(matrix_path),
                labels_path=str(labels_path),
                output_path=str(output_path),
                participant_id="P001"
            )

            # Check result
            assert result['participant_id'] == "P001"
            assert result['num_rois'] == 3
            assert os.path.exists(output_path)

            # Check output file content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3
                assert rows[0]['participant_id'] == "P001"
                assert rows[0]['roi_label'] == "ROI1"
                assert 'degree' in rows[0]
                assert 'betweenness' in rows[0]
                assert 'closeness' in rows[0]

class TestRunCentralityPipeline:
    def test_run_pipeline(self):
        """Test running the full centrality pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "input"
            output_dir = tmpdir / "output"
            input_dir.mkdir()

            # Create connectivity matrices for two participants
            for i in range(2):
                matrix_path = input_dir / f"corr_matrix_P00{i+1}.csv"
                with open(matrix_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([1.0, 0.8, 0.2])
                    writer.writerow([0.8, 1.0, 0.5])
                    writer.writerow([0.2, 0.5, 1.0])

            # Create ROI labels
            labels_path = tmpdir / "roi_labels.json"
            with open(labels_path, 'w') as f:
                json.dump(["ROI1", "ROI2", "ROI3"], f)

            # Run pipeline
            results = run_centrality_pipeline(
                input_dir=str(input_dir),
                labels_path=str(labels_path),
                output_dir=str(output_dir)
            )

            # Check results
            assert len(results) == 2
            for res in results:
                assert 'participant_id' in res
                assert 'num_rois' in res
                assert res['num_rois'] == 3
                assert os.path.exists(res['output_file'])