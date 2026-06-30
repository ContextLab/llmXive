"""
Unit tests for visualization module (T032).
Tests saving visualization and updating ResultReport.json.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import numpy as np

# Test imports
from code.modeling.visualization import (
    load_interpreted_edges,
    save_visualization,
    update_result_report,
    run_visualization_pipeline
)
from code.config import get_paths


class TestVisualization:
    """Test cases for visualization module."""

    @patch('code.modeling.visualization.load_interpreted_edges')
    @patch('code.modeling.visualization.plotting.plot_connectome')
    @patch('code.modeling.visualization.plt')
    def test_save_visualization_creates_file(self, mock_plt, mock_plot_connectome, mock_load_edges):
        """Test that save_visualization creates the output file."""
        # Mock the interpreted edges
        mock_load_edges.return_value = {
            'edges': [
                {
                    'source_coords': [0.0, 0.0, 0.0],
                    'target_coords': [1.0, 1.0, 1.0],
                    'weight': 0.5
                }
            ]
        }
        
        # Mock the plot object
        mock_fig = MagicMock()
        mock_plot_connectome.return_value = mock_fig
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch get_paths to use temp directory
            with patch('code.modeling.visualization.get_paths') as mock_get_paths:
                mock_paths = {
                    'data_processed': Path(tmpdir) / 'processed',
                    'data_results': Path(tmpdir) / 'results'
                }
                mock_get_paths.return_value = mock_paths
                
                # Ensure directories exist
                mock_paths['data_processed'].mkdir(parents=True)
                mock_paths['data_results'].mkdir(parents=True)
                
                # Call the function
                result_path = save_visualization(top_n=50, output_format='png')
                
                # Verify the file was created
                assert os.path.exists(result_path)
                assert result_path.endswith('.png')
                
                # Verify plot_connectome was called
                mock_plot_connectome.assert_called_once()
                
                # Verify savefig was called
                mock_fig.savefig.assert_called_once()

    @patch('code.modeling.visualization.load_result_report')
    @patch('code.modeling.visualization.save_result_report')
    def test_update_result_report(self, mock_save, mock_load):
        """Test that update_result_report correctly updates the JSON."""
        # Mock existing report
        mock_report = {
            'metadata': {'version': '1.0'},
            'model_metrics': {'r_squared': 0.45}
        }
        mock_load.return_value = mock_report
        
        # Call the function
        update_result_report('/path/to/visualization.png')
        
        # Verify the report was updated correctly
        updated_report = mock_save.call_args[0][0]
        assert 'visualization' in updated_report
        assert updated_report['visualization']['file_path'] == '/path/to/visualization.png'
        assert 'generated_at' in updated_report['visualization']

    @patch('code.modeling.visualization.save_visualization')
    @patch('code.modeling.visualization.update_result_report')
    def test_run_visualization_pipeline(self, mock_update, mock_save):
        """Test the full visualization pipeline."""
        mock_save.return_value = '/path/to/visualization.png'
        
        result = run_visualization_pipeline(top_n=50, output_format='png')
        
        assert result['visualization_path'] == '/path/to/visualization.png'
        assert result['report_updated'] is True
        mock_save.assert_called_once_with(top_n=50, output_format='png')
        mock_update.assert_called_once_with('/path/to/visualization.png')

    @patch('code.modeling.visualization.load_interpreted_edges')
    def test_save_visualization_fewer_edges(self, mock_load_edges):
        """Test handling when fewer than top_n edges exist."""
        # Mock with only 10 edges
        mock_load_edges.return_value = {
            'edges': [
                {
                    'source_coords': [i, i, i],
                    'target_coords': [i+1, i+1, i+1],
                    'weight': 0.5 - i * 0.01
                }
                for i in range(10)
            ]
        }
        
        with patch('code.modeling.visualization.plotting.plot_connectome') as mock_plot:
            mock_fig = MagicMock()
            mock_plot.return_value = mock_fig
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('code.modeling.visualization.get_paths') as mock_get_paths:
                    mock_paths = {
                        'data_processed': Path(tmpdir) / 'processed',
                        'data_results': Path(tmpdir) / 'results'
                    }
                    mock_get_paths.return_value = mock_paths
                    mock_paths['data_processed'].mkdir(parents=True)
                    mock_paths['data_results'].mkdir(parents=True)
                    
                    # Should not raise an error even with fewer edges
                    result_path = save_visualization(top_n=50, output_format='png')
                    
                    assert result_path.endswith('.png')
                    # Verify it used all 10 edges
                    call_args = mock_plot.call_args
                    edge_tuples = call_args[0][1]  # Second argument is edge_tuples
                    assert len(edge_tuples) == 10

    @patch('code.modeling.visualization.load_interpreted_edges')
    def test_save_visualization_no_edges(self, mock_load_edges):
        """Test error handling when no edges exist."""
        mock_load_edges.return_value = {'edges': []}
        
        with pytest.raises(ValueError, match="No edges found"):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('code.modeling.visualization.get_paths') as mock_get_paths:
                    mock_paths = {
                        'data_processed': Path(tmpdir) / 'processed',
                        'data_results': Path(tmpdir) / 'results'
                    }
                    mock_get_paths.return_value = mock_paths
                    mock_paths['data_processed'].mkdir(parents=True)
                    mock_paths['data_results'].mkdir(parents=True)
                    
                    save_visualization(top_n=50, output_format='png')

    @patch('code.modeling.visualization.load_interpreted_edges')
    def test_save_visualization_svg_format(self, mock_load_edges):
        """Test saving as SVG format."""
        mock_load_edges.return_value = {
            'edges': [
                {
                    'source_coords': [0.0, 0.0, 0.0],
                    'target_coords': [1.0, 1.0, 1.0],
                    'weight': 0.5
                }
            ]
        }
        
        with patch('code.modeling.visualization.plotting.plot_connectome') as mock_plot:
            mock_fig = MagicMock()
            mock_plot.return_value = mock_fig
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('code.modeling.visualization.get_paths') as mock_get_paths:
                    mock_paths = {
                        'data_processed': Path(tmpdir) / 'processed',
                        'data_results': Path(tmpdir) / 'results'
                    }
                    mock_get_paths.return_value = mock_paths
                    mock_paths['data_processed'].mkdir(parents=True)
                    mock_paths['data_results'].mkdir(parents=True)
                    
                    result_path = save_visualization(top_n=50, output_format='svg')
                    
                    assert result_path.endswith('.svg')