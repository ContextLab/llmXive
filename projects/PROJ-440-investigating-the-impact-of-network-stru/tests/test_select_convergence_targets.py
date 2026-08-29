"""
Tests for select_convergence_targets module.
"""

import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the module functions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from select_convergence_targets import (
    load_network_metrics,
    select_representative_graphs,
    save_convergence_targets
)


class TestLoadNetworkMetrics:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file"""
        csv_path = tmp_path / "networks.csv"
        data = {
            'id': [1, 2, 3],
            'class': ['random', 'scale_free', 'small_world'],
            'avg_degree': [5.0, 6.0, 4.5]
        }
        df_input = pd.DataFrame(data)
        df_input.to_csv(csv_path, index=False)

        df_output = load_network_metrics(str(csv_path))

        assert len(df_output) == 3
        assert list(df_output.columns) == ['id', 'class', 'avg_degree']

    def test_file_not_found(self, tmp_path):
        """Test error handling for missing file"""
        with pytest.raises(FileNotFoundError):
            load_network_metrics(str(tmp_path / "nonexistent.csv"))


class TestSelectRepresentativeGraphs:
    def test_select_one_per_class(self):
        """Test that exactly one graph is selected per class"""
        data = {
            'id': [1, 2, 3, 4, 5, 6],
            'class': ['random', 'random', 'scale_free', 'scale_free', 'small_world', 'small_world'],
            'avg_degree': [5.0, 5.0, 6.0, 6.0, 4.5, 4.5]
        }
        df = pd.DataFrame(data)

        selected = select_representative_graphs(df)

        assert len(selected) == 3  # One per class
        assert set(selected) == {1, 3, 5}  # Should pick lowest ID on ties

    def test_select_closest_to_median(self):
        """Test selection based on proximity to median"""
        # Create data where one value is clearly closer to median
        data = {
            'id': [1, 2, 3],
            'class': ['random', 'random', 'random'],
            'avg_degree': [4.0, 5.0, 10.0]  # Median is 5.0
        }
        df = pd.DataFrame(data)

        selected = select_representative_graphs(df)

        assert len(selected) == 1
        assert selected[0] == 2  # ID 2 has avg_degree=5.0, closest to median 5.0

    def test_tie_breaking_by_id(self):
        """Test that ties are broken by lowest ID"""
        data = {
            'id': [10, 20, 30],
            'class': ['random', 'random', 'random'],
            'avg_degree': [5.0, 5.0, 5.0]  # All same distance to median
        }
        df = pd.DataFrame(data)

        selected = select_representative_graphs(df)

        assert len(selected) == 1
        assert selected[0] == 10  # Lowest ID

    def test_empty_dataframe(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame(columns=['id', 'class', 'avg_degree'])
        selected = select_representative_graphs(df)
        assert len(selected) == 0


class TestSaveConvergenceTargets:
    def test_save_and_load(self, tmp_path):
        """Test saving and reading back the JSON file"""
        selected_ids = [1, 3, 5]
        output_path = tmp_path / "targets.json"

        save_convergence_targets(selected_ids, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data['count'] == 3
        assert data['convergence_targets'] == selected_ids

    def test_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist"""
        selected_ids = [1]
        nested_path = tmp_path / "subdir" / "targets.json"

        save_convergence_targets(selected_ids, str(nested_path))

        assert nested_path.exists()


class TestIntegration:
    def test_full_pipeline(self, tmp_path):
        """Test the full pipeline from CSV to JSON"""
        # Create input CSV
        csv_path = tmp_path / "networks.csv"
        data = {
            'id': [1, 2, 3, 4, 5],
            'class': ['random', 'scale_free', 'small_world', 'random', 'scale_free'],
            'avg_degree': [5.0, 6.0, 4.5, 5.5, 6.5]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        # Load and process
        df = load_network_metrics(str(csv_path))
        selected = select_representative_graphs(df)

        # Save
        output_path = tmp_path / "targets.json"
        save_convergence_targets(selected, str(output_path))

        # Verify output
        with open(output_path, 'r') as f:
            result = json.load(f)

        assert result['count'] == 3
        assert len(result['convergence_targets']) == 3
        assert all(isinstance(x, int) for x in result['convergence_targets'])