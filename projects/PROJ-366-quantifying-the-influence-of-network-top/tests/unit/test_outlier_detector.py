"""
Unit tests for outlier detection logic.
"""
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from analysis.outlier_detector import (
    calculate_defect_ratio,
    extract_node_degrees,
    detect_outliers,
    write_excluded_samples,
    COORD_MIN_THRESHOLD,
    COORD_MAX_THRESHOLD,
    DEFECT_RATIO_THRESHOLD
)


class TestExtractNodeDegrees:
    """Tests for node degree extraction."""

    def test_extract_from_node_degrees_field(self):
        """Should extract degrees from 'node_degrees' field."""
        graph_data = {
            'node_degrees': [3, 4, 5, 2, 7]
        }
        degrees = extract_node_degrees(graph_data)
        assert degrees == [3, 4, 5, 2, 7]

    def test_extract_from_adjacency_field(self):
        """Should derive degrees from adjacency list."""
        graph_data = {
            'adjacency': [
                [1, 2],      # node 0: degree 2
                [0, 2, 3],   # node 1: degree 3
                [0, 1],      # node 2: degree 2
                [1]          # node 3: degree 1
            ]
        }
        degrees = extract_node_degrees(graph_data)
        assert degrees == [2, 3, 2, 1]

    def test_empty_graph_data(self):
        """Should return empty list for missing fields."""
        graph_data = {}
        degrees = extract_node_degrees(graph_data)
        assert degrees == []


class TestCalculateDefectRatio:
    """Tests for defect ratio calculation."""

    def test_no_defects(self):
        """All atoms within normal range -> ratio 0."""
        degrees = [3, 4, 5, 4, 3]  # All between 3 and 6
        ratio = calculate_defect_ratio(degrees)
        assert ratio == 0.0

    def test_all_defects(self):
        """All atoms are defects -> ratio 1.0."""
        degrees = [2, 2, 7, 7, 2]  # All < 3 or > 6
        ratio = calculate_defect_ratio(degrees)
        assert ratio == 1.0

    def test_mixed_case(self):
        """Mixed normal and defect atoms."""
        # 5 atoms: 2 are defects (2 and 7), 3 are normal (3,4,5)
        degrees = [2, 3, 4, 5, 7]
        ratio = calculate_defect_ratio(degrees)
        assert ratio == 0.4  # 2/5

    def test_empty_list(self):
        """Empty degrees list -> ratio 0."""
        ratio = calculate_defect_ratio([])
        assert ratio == 0.0


class TestDetectOutliers:
    """Integration tests for outlier detection."""

    @pytest.fixture
    def temp_graphs_dir(self, tmp_path):
        """Create temporary directory with test graph files."""
        graphs_dir = tmp_path / "graphs"
        graphs_dir.mkdir()

        # Create test graph files
        # Normal sample (no defects)
        normal_graph = {
            'node_degrees': [3, 4, 5, 4, 3, 4, 5, 4]
        }
        with open(graphs_dir / "normal_sample.pkl", 'wb') as f:
            pickle.dump(normal_graph, f)

        # Outlier sample (>15% defects)
        # 10 atoms: 2 defects (20% > 15%)
        outlier_graph = {
            'node_degrees': [3, 4, 2, 4, 5, 4, 7, 4, 3, 4]
        }
        with open(graphs_dir / "outlier_sample.pkl", 'wb') as f:
            pickle.dump(outlier_graph, f)

        # Another normal sample
        another_normal = {
            'node_degrees': [3, 4, 5, 4, 3]
        }
        with open(graphs_dir / "another_normal.pkl", 'wb') as f:
            pickle.dump(another_normal, f)

        return graphs_dir

    @patch('analysis.outlier_detector.get_config')
    def test_detect_outliers_with_enforcement(self, mock_get_config, temp_graphs_dir):
        """Should detect and exclude outliers when enforce_exclusion=True."""
        mock_get_config.return_value = {
            'paths': {
                'processed_graphs': str(temp_graphs_dir),
                'excluded_samples': str(temp_graphs_dir.parent / "excluded.json")
            },
            'enforce_exclusion': True
        }

        excluded_ids = detect_outliers(temp_graphs_dir, temp_graphs_dir.parent / "excluded.json")
        
        assert "outlier_sample" in excluded_ids
        assert "normal_sample" not in excluded_ids
        assert "another_normal" not in excluded_ids

    @patch('analysis.outlier_detector.get_config')
    def test_detect_outliers_without_enforcement(self, mock_get_config, temp_graphs_dir):
        """Should not exclude outliers when enforce_exclusion=False."""
        mock_get_config.return_value = {
            'paths': {
                'processed_graphs': str(temp_graphs_dir),
                'excluded_samples': str(temp_graphs_dir.parent / "excluded.json")
            },
            'enforce_exclusion': False
        }

        excluded_ids = detect_outliers(temp_graphs_dir, temp_graphs_dir.parent / "excluded.json")
        
        # Should return empty set when enforcement is disabled
        assert len(excluded_ids) == 0


class TestWriteExcludedSamples:
    """Tests for writing excluded samples to file."""

    def test_write_excluded_samples(self, tmp_path):
        """Should write excluded IDs to JSON file."""
        exclude_file = tmp_path / "excluded_samples.json"
        excluded_ids = {"sample1", "sample2", "sample3"}

        write_excluded_samples(excluded_ids, exclude_file)

        assert exclude_file.exists()
        
        with open(exclude_file, 'r') as f:
            data = json.load(f)
        
        assert set(data['excluded_samples']) == excluded_ids
        assert data['count'] == 3
        assert 'reason' in data

    def test_write_empty_excluded(self, tmp_path):
        """Should write empty list when no exclusions."""
        exclude_file = tmp_path / "excluded_samples.json"
        
        write_excluded_samples(set(), exclude_file)

        assert exclude_file.exists()
        
        with open(exclude_file, 'r') as f:
            data = json.load(f)
        
        assert data['excluded_samples'] == []
        assert data['count'] == 0
