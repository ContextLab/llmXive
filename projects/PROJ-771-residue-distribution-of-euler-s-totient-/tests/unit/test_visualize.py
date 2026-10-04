"""
Unit tests for visualization module.
"""
import os
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function to test
from code.visualize import plot_residual_qq

def test_plot_residual_qq_creates_file():
    """Test that plot_residual_qq creates a PNG file."""
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the output directory to be our temp dir
        with patch('code.visualize.output_dir', tmpdir):
            # We need to patch the os.makedirs and plt.savefig to capture the path
            # Since the function hardcodes "results/plots", we patch the os module inside the function
            with patch('code.visualize.os.makedirs') as mock_makedirs, \
                 patch('code.visualize.os.path.join', side_effect=lambda a, b: os.path.join(tmpdir, b)) as mock_join, \
                 patch('code.visualize.plt') as mock_plt:
                
                    # Setup mocks
                    mock_fig = MagicMock()
                    mock_plt.figure.return_value = mock_fig
                    mock_plt.savefig = MagicMock()
                    
                    # Call the function with sample residuals
                    residuals = [0.5, -0.3, 1.2, -0.8, 0.1]
                    plot_residual_qq(residuals)
                    
                    # Verify savefig was called (meaning a file would be "saved")
                    mock_plt.savefig.assert_called_once()
                    
                    # Verify the path constructed is in our temp dir
                    call_args = mock_plt.savefig.call_args
                    assert call_args is not None
                    # The first arg to savefig is the path
                    path_arg = call_args[0][0]
                    assert tmpdir in path_arg
                    assert path_arg.endswith('.png')

def test_plot_residual_qq_empty_residuals():
    """Test that plot_residual_qq handles empty list gracefully."""
    with patch('code.visualize.logger') as mock_logger:
        plot_residual_qq([])
        # Should log a warning and return early
        mock_logger.warning.assert_called_once()

def test_plot_residual_qq_single_value():
    """Test with a single residual value."""
    with patch('code.visualize.os.makedirs'), \
         patch('code.visualize.os.path.join', return_value="/tmp/test.png"), \
         patch('code.visualize.plt') as mock_plt:
            
            mock_fig = MagicMock()
            mock_plt.figure.return_value = mock_fig
            mock_plt.savefig = MagicMock()
            
            plot_residual_qq([0.5])
            
            # Should still attempt to save
            mock_plt.savefig.assert_called_once()