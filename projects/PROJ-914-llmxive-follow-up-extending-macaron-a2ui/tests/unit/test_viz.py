"""
Unit tests for code/analysis/viz.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.viz import calculate_pareto_frontier, plot_pareto_frontier, plot_alignment_by_density, load_metrics_data

class TestParetoFrontier:
    """Tests for Pareto frontier calculation logic."""

    def test_pareto_frontier_simple(self):
        """
        Test basic Pareto frontier calculation.
        Points: (1, 0.5), (2, 0.8), (3, 0.7)
        Frontier should be: (1, 0.5) -> (2, 0.8)
        (3, 0.7) is dominated by (2, 0.8) because 3 > 2 and 0.7 < 0.8.
        """
        data = {
            'density': [1, 2, 3],
            'avg_latency': [1.0, 2.0, 3.0],
            'avg_alignment_score': [0.5, 0.8, 0.7]
        }
        df = pd.DataFrame(data)
        frontier = calculate_pareto_frontier(df)
        
        assert len(frontier) == 2
        # Should contain (1, 0.5) and (2, 0.8)
        assert (frontier['avg_latency'] == 1.0).any()
        assert (frontier['avg_alignment_score'] == 0.5).any()
        assert (frontier['avg_latency'] == 2.0).any()
        assert (frontier['avg_alignment_score'] == 0.8).any()
        # (3, 0.7) should NOT be in frontier
        assert not ((frontier['avg_latency'] == 3.0) & (frontier['avg_alignment_score'] == 0.7)).any()

    def test_pareto_frontier_all_dominated(self):
        """Test case where one point dominates all others."""
        data = {
            'density': [1, 2, 3],
            'avg_latency': [1.0, 2.0, 3.0],
            'avg_alignment_score': [0.9, 0.5, 0.4]
        }
        df = pd.DataFrame(data)
        frontier = calculate_pareto_frontier(df)
        
        # Only (1, 0.9) should be in frontier
        assert len(frontier) == 1
        assert frontier.iloc[0]['avg_latency'] == 1.0
        assert frontier.iloc[0]['avg_alignment_score'] == 0.9

    def test_pareto_frontier_increasing(self):
        """Test case where alignment increases with latency (no domination)."""
        data = {
            'density': [1, 2, 3],
            'avg_latency': [1.0, 2.0, 3.0],
            'avg_alignment_score': [0.3, 0.6, 0.9]
        }
        df = pd.DataFrame(data)
        frontier = calculate_pareto_frontier(df)
        
        # All points should be on frontier
        assert len(frontier) == 3

class TestLoadMetricsData:
    """Tests for loading metrics data."""

    def test_load_from_json(self, tmp_path):
        """Test loading metrics from a JSON file."""
        data = [
            {'density': 1, 'avg_latency': 1.0, 'avg_alignment_score': 0.5},
            {'density': 3, 'avg_latency': 2.0, 'avg_alignment_score': 0.8}
        ]
        json_file = tmp_path / "metrics.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        df = load_metrics_data(str(json_file))
        assert len(df) == 2
        assert 'density' in df.columns
        assert 'avg_latency' in df.columns
        assert 'avg_alignment_score' in df.columns

    def test_load_missing_columns(self, tmp_path):
        """Test that loading fails if required columns are missing."""
        data = [
            {'density': 1, 'latency': 1.0}  # Missing avg_alignment_score
        ]
        json_file = tmp_path / "metrics.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError, match="missing required columns"):
            load_metrics_data(str(json_file))

class TestPlotting:
    """Tests for plotting functions (mocked to avoid actual file I/O issues in CI)."""

    @patch('analysis.viz.plt.savefig')
    @patch('analysis.viz.plt.close')
    @patch('analysis.viz.ensure_dirs')
    def test_plot_pareto_frontier(self, mock_ensure, mock_close, mock_save):
        """Test that plot_pareto_frontier calls savefig correctly."""
        data = {
            'density': [1, 2],
            'avg_latency': [1.0, 2.0],
            'avg_alignment_score': [0.5, 0.8]
        }
        df = pd.DataFrame(data)
        pareto_df = calculate_pareto_frontier(df)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            plot_pareto_frontier(df, pareto_df, output_path)
            
            mock_save.assert_called_once()
            mock_ensure.assert_called_once()

    @patch('analysis.viz.plt.savefig')
    @patch('analysis.viz.plt.close')
    @patch('analysis.viz.ensure_dirs')
    def test_plot_alignment_by_density(self, mock_ensure, mock_close, mock_save):
        """Test that plot_alignment_by_density calls savefig correctly."""
        data = {
            'density': [1, 3, 5, 10],
            'avg_latency': [1.0, 2.0, 3.0, 4.0],
            'avg_alignment_score': [0.5, 0.6, 0.7, 0.8]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            plot_alignment_by_density(df, output_path)
            
            mock_save.assert_called_once()
            mock_ensure.assert_called_once()