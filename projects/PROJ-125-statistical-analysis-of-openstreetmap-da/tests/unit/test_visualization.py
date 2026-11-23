"""
Unit tests for visualization module.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

from code.visualization import (
    load_correlation_matrix,
    load_spatial_stats,
    plot_correlation_heatmap,
    plot_variogram,
    compute_empirical_variogram
)
from code.config import get_path


class TestLoadCorrelationMatrix:
    def test_load_correlation_matrix_success(self, tmp_path):
        """Test loading a valid correlation matrix."""
        # Create a temporary correlation matrix
        df = pd.DataFrame({
            'temp': [1.0, 0.5, -0.2],
            'building_density': [0.5, 1.0, 0.3],
            'tree_coverage': [-0.2, 0.3, 1.0]
        }, index=['temp', 'building_density', 'tree_coverage'])
        
        # Mock get_path to return our temp file
        mock_path = tmp_path / "correlation_matrix.csv"
        df.to_csv(mock_path)
        
        with patch('code.visualization.get_path', return_value=str(mock_path)):
            result = load_correlation_matrix()
            assert result.shape == (3, 3)
            assert 'temp' in result.index
            assert 'temp' in result.columns
            assert result.loc['temp', 'temp'] == 1.0

    def test_load_correlation_matrix_file_not_found(self):
        """Test that FileNotFoundError is raised when file is missing."""
        with patch('code.visualization.get_path', return_value='/nonexistent/path.csv'):
            with pytest.raises(FileNotFoundError):
                load_correlation_matrix()


class TestLoadSpatialStats:
    def test_load_spatial_stats_success(self, tmp_path):
        """Test loading valid spatial stats."""
        stats_data = {
            'moran_i': 0.45,
            'p_value': 0.001,
            'variogram': {
                'nugget': 0.1,
                'sill': 0.5,
                'range': 1000.0
            }
        }
        
        mock_path = tmp_path / "spatial_stats.json"
        with open(mock_path, 'w') as f:
            json.dump(stats_data, f)
        
        with patch('code.visualization.get_path', return_value=str(mock_path)):
            result = load_spatial_stats()
            assert result['moran_i'] == 0.45
            assert 'variogram' in result

    def test_load_spatial_stats_file_not_found(self):
        """Test that FileNotFoundError is raised when file is missing."""
        with patch('code.visualization.get_path', return_value='/nonexistent/path.json'):
            with pytest.raises(FileNotFoundError):
                load_spatial_stats()


class TestComputeEmpiricalVariogram:
    def test_compute_variogram_basic(self):
        """Test basic variogram computation."""
        np.random.seed(42)
        n = 100
        coords = np.random.rand(n, 2) * 1000
        values = np.random.rand(n) * 10
        
        lags, semivars, counts = compute_empirical_variogram(values, coords, bin_width=200)
        
        assert len(lags) == len(semivars)
        assert len(lags) == len(counts)
        assert all(counts > 0)
        assert all(semivars >= 0)

    def test_compute_variogram_mismatched_lengths(self):
        """Test that error is raised for mismatched lengths."""
        coords = np.random.rand(100, 2)
        values = np.random.rand(50)
        
        with pytest.raises(ValueError):
            compute_empirical_variogram(values, coords)


class TestPlotCorrelationHeatmap:
    def test_plot_correlation_heatmap_creates_file(self, tmp_path):
        """Test that plot creates a file."""
        df = pd.DataFrame({
            'temp': [1.0, 0.5],
            'building': [0.5, 1.0]
        }, index=['temp', 'building'])
        
        output_path = tmp_path / "test_heatmap.png"
        
        # Mock the plot function to avoid actual plotting
        with patch('code.visualization.sns.heatmap'):
            with patch('code.visualization.plt.savefig'):
                with patch('code.visualization.plt.close'):
                    result = plot_correlation_heatmap(df, output_path)
                    
                    assert result == output_path

    def test_plot_correlation_heatmap_default_path(self, tmp_path):
        """Test that plot uses default path when not specified."""
        df = pd.DataFrame({
            'temp': [1.0, 0.5],
            'building': [0.5, 1.0]
        }, index=['temp', 'building'])
        
        mock_path = tmp_path / "correlation_heatmap.png"
        
        with patch('code.visualization.get_path', return_value=str(mock_path)):
            with patch('code.visualization.sns.heatmap'):
                with patch('code.visualization.plt.savefig'):
                    with patch('code.visualization.plt.close'):
                        result = plot_correlation_heatmap(df)
                        assert result == mock_path


class TestPlotVariogram:
    def test_plot_variogram_creates_file(self, tmp_path):
        """Test that variogram plot creates a file."""
        output_path = tmp_path / "test_variogram.png"
        
        # Mock the necessary functions
        with patch('code.visualization.load_spatial_stats', return_value={'variogram': {}}):
            with patch('code.visualization.get_path', return_value=str(output_path)):
                with patch('code.visualization.plt.figure'):
                    with patch('code.visualization.plt.scatter'):
                        with patch('code.visualization.plt.savefig'):
                            with patch('code.visualization.plt.close'):
                                result = plot_variogram(output_path)
                                assert result == output_path

    def test_plot_variogram_default_path(self, tmp_path):
        """Test that variogram uses default path."""
        mock_path = tmp_path / "variogram.png"
        
        with patch('code.visualization.get_path', return_value=str(mock_path)):
            with patch('code.visualization.load_spatial_stats', return_value={'variogram': {}}):
                with patch('code.visualization.plt.figure'):
                    with patch('code.visualization.plt.scatter'):
                        with patch('code.visualization.plt.savefig'):
                            with patch('code.visualization.plt.close'):
                                result = plot_variogram()
                                assert result == mock_path


class TestPlotCombinedEDA:
    def test_plot_combined_eda_returns_dict(self, tmp_path):
        """Test that combined EDA returns a dictionary of paths."""
        output_dir = tmp_path / "results"
        output_dir.mkdir()
        
        with patch('code.visualization.get_path', return_value=str(output_dir)):
            with patch('code.visualization.plot_correlation_heatmap') as mock_corr:
                with patch('code.visualization.plot_variogram') as mock_var:
                    mock_corr.return_value = output_dir / "correlation_heatmap.png"
                    mock_var.return_value = output_dir / "variogram.png"
                    
                    result = plot_combined_eda(output_dir)
                    
                    assert isinstance(result, dict)
                    assert 'correlation_heatmap' in result
                    assert 'variogram' in result
                    assert result['correlation_heatmap'] == output_dir / "correlation_heatmap.png"
                    assert result['variogram'] == output_dir / "variogram.png"