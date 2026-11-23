import pytest
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
import tempfile
import os

from code.analysis.centrality import (
    compute_centrality_metrics,
    calculate_mean_fd,
    get_subject_list_from_directory,
)


class TestComputeCentralityMetrics:
    def test_returns_correct_columns(self):
        """Test that the function returns a DataFrame with expected columns."""
        # Create a simple 5x5 adjacency matrix
        adj_matrix = np.array([
            [0, 1, 1, 0, 0],
            [1, 0, 1, 1, 0],
            [1, 1, 0, 1, 1],
            [0, 1, 1, 0, 1],
            [0, 0, 1, 1, 0]
        ], dtype=float)

        subject_id = "sub-001"
        region_names = ["Region_{}".format(i) for i in range(5)]

        result = compute_centrality_metrics(subject_id, adj_matrix, region_names)

        assert isinstance(result, pd.DataFrame)
        expected_columns = ['subject_id', 'region_id', 'region_name', 'degree', 'betweenness', 'eigenvector']
        assert list(result.columns) == expected_columns
        assert len(result) == 5

    def test_degree_centrality_calculation(self):
        """Test that degree centrality is calculated correctly."""
        # Create a star graph: node 0 connected to all others
        n = 5
        adj_matrix = np.zeros((n, n))
        for i in range(1, n):
            adj_matrix[0, i] = 1
            adj_matrix[i, 0] = 1

        subject_id = "sub-001"
        region_names = ["Region_{}".format(i) for i in range(n)]

        result = compute_centrality_metrics(subject_id, adj_matrix, region_names)

        # Node 0 should have the highest degree (4)
        # Other nodes should have degree 1
        degree_values = result['degree'].values
        assert np.max(degree_values) == 4.0
        assert np.sum(degree_values == 1.0) == 4

    def test_eigenvector_centrality_positive(self):
        """Test that eigenvector centrality values are non-negative."""
        adj_matrix = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ], dtype=float)

        subject_id = "sub-001"
        region_names = ["A", "B", "C"]

        result = compute_centrality_metrics(subject_id, adj_matrix, region_names)

        # Eigenvector centrality should be non-negative for this graph
        assert all(result['eigenvector'] >= 0)

    def test_empty_matrix_raises_error(self):
        """Test that an empty matrix raises an appropriate error."""
        adj_matrix = np.zeros((0, 0))
        subject_id = "sub-001"
        region_names = []

        with pytest.raises((ValueError, IndexError)):
            compute_centrality_metrics(subject_id, adj_matrix, region_names)

    def test_mismatched_dimensions_raises_error(self):
        """Test that mismatched matrix and region names raise an error."""
        adj_matrix = np.zeros((3, 3))
        subject_id = "sub-001"
        region_names = ["A", "B"]  # Only 2 names for 3x3 matrix

        with pytest.raises((ValueError, IndexError)):
            compute_centrality_metrics(subject_id, adj_matrix, region_names)


class TestCalculateMeanFD:
    def test_calculates_mean_correctly(self):
        """Test that mean FD is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock confounds file
            confounds_path = Path(tmpdir) / "desc-confounds_timeseries.tsv"
            fd_values = [0.1, 0.2, 0.3, 0.4, 0.5]
            df = pd.DataFrame({'framewise_displacement': fd_values})
            df.to_csv(confounds_path, sep='\t', index=False)

            result = calculate_mean_fd(str(confounds_path))

            expected_mean = np.mean(fd_values)
            assert abs(result - expected_mean) < 1e-6

    def test_handles_missing_fd_column(self):
        """Test behavior when FD column is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "desc-confounds_timeseries.tsv"
            df = pd.DataFrame({'other_column': [1, 2, 3]})
            df.to_csv(confounds_path, sep='\t', index=False)

            with pytest.raises((KeyError, ValueError)):
                calculate_mean_fd(str(confounds_path))

    def test_handles_empty_file(self):
        """Test behavior with empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "desc-confounds_timeseries.tsv"
            df = pd.DataFrame()
            df.to_csv(confounds_path, sep='\t', index=False)

            with pytest.raises((ValueError, IndexError)):
                calculate_mean_fd(str(confounds_path))


class TestGetSubjectListFromDirectory:
    def test_returns_sorted_list(self):
        """Test that the function returns a sorted list of subjects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock subject directories
            subjects = ["sub-003", "sub-001", "sub-002"]
            for subj in subjects:
                os.makedirs(Path(tmpdir) / subj)

            result = get_subject_list_from_directory(tmpdir)

            assert result == sorted(subjects)
            assert len(result) == 3

    def test_returns_empty_list_for_no_subjects(self):
        """Test behavior when no subject directories exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_subject_list_from_directory(tmpdir)
            assert result == []

    def test_filters_non_subject_directories(self):
        """Test that non-subject directories are filtered out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mix of subject and non-subject directories
            os.makedirs(Path(tmpdir) / "sub-001")
            os.makedirs(Path(tmpdir) / "code")
            os.makedirs(Path(tmpdir) / "data")
            os.makedirs(Path(tmpdir) / "sub-002")

            result = get_subject_list_from_directory(tmpdir)

            assert "sub-001" in result
            assert "sub-002" in result
            assert "code" not in result
            assert "data" not in result
            assert len(result) == 2
