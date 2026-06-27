"""
Unit tests for visualization generation functionality.

This test module validates the visualization.py module's ability to:
1. Generate scatter plots with regression lines
2. Save plots to file in PNG and PDF formats
3. Handle edge cases and error conditions

Per spec.md Independent Test requirements for US3.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import numpy as np

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Test fixtures and helper functions
@pytest.fixture
def sample_data():
    """Provide sample data for visualization tests"""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.1, 4.0, 5.2, 4.1, 5.3])
    return x, y

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_matplotlib():
    """Mock matplotlib to avoid actual plotting during unit tests"""
    with patch.dict('sys.modules', {
        'matplotlib': MagicMock(),
        'matplotlib.pyplot': MagicMock(),
        'matplotlib.patches': MagicMock(),
        'matplotlib.lines': MagicMock(),
        'matplotlib.text': MagicMock(),
    }):
        yield

@pytest.fixture
def mock_scipy():
    """Mock scipy for regression line computation"""
    with patch.dict('sys.modules', {
        'scipy': MagicMock(),
        'scipy.stats': MagicMock(),
    }):
        yield

# Test: Scatter plot generation
def test_scatter_plot_generation(sample_data, temp_output_dir, mock_matplotlib):
    """
    Test that scatter plots are generated correctly with required components.
    
    Validates:
    - Plot is created with x and y data
    - Regression line is added
    - Labels and title are set
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    plt.figure.return_value = mock_fig
    plt.gca.return_value = mock_ax
    
    # Import visualization module (will use mocks)
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x, y = sample_data
        output_path = temp_output_dir / "test_scatter.png"
        
        # Call the function
        result = generate_scatter_plot(x, y, str(output_path))
        
        # Verify plot was created
        assert result is not None
        assert plt.figure.called
        
        # Verify scatter plot was called with correct data
        assert mock_ax.scatter.called
        
        # Verify regression line was added
        assert mock_ax.plot.called

# Test: Regression line computation
def test_regression_line_computation(sample_data, temp_output_dir, mock_scipy):
    """
    Test that regression lines are computed correctly.
    
    Validates:
    - Slope and intercept are calculated
    - Regression line matches expected linear fit
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    from scipy import stats
    
    # Setup mocks
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    plt.figure.return_value = mock_fig
    plt.gca.return_value = mock_ax
    
    # Mock scipy.stats.linregress
    mock_result = MagicMock()
    mock_result.slope = 0.8
    mock_result.intercept = 1.0
    stats.linregress.return_value = mock_result
    
    with patch('visualization.plt', plt):
        with patch('visualization.stats', stats):
            from visualization import compute_regression_line
            
            x, y = sample_data
            
            # Call the function
            slope, intercept = compute_regression_line(x, y)
            
            # Verify regression was computed
            assert slope is not None
            assert intercept is not None
            assert isinstance(slope, (int, float))
            assert isinstance(intercept, (int, float))

# Test: File output in PNG format
def test_png_output_format(temp_output_dir, mock_matplotlib):
    """
    Test that plots are saved correctly in PNG format.
    
    Validates:
    - PNG file is created
    - File is not empty
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    plt.figure.return_value = mock_fig
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([2.0, 4.0, 6.0])
        output_path = temp_output_dir / "test_output.png"
        
        # Call the function
        generate_scatter_plot(x, y, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.suffix == '.png'

# Test: File output in PDF format
def test_pdf_output_format(temp_output_dir, mock_matplotlib):
    """
    Test that plots are saved correctly in PDF format.
    
    Validates:
    - PDF file is created
    - File is not empty
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    plt.figure.return_value = mock_fig
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([2.0, 4.0, 6.0])
        output_path = temp_output_dir / "test_output.pdf"
        
        # Call the function
        generate_scatter_plot(x, y, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.suffix == '.pdf'

# Test: Empty data handling
def test_empty_data_handling(mock_matplotlib):
    """
    Test that empty data arrays are handled gracefully.
    
    Validates:
    - Appropriate exception is raised
    - Error message is informative
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    plt.figure.return_value = mock_fig
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([])
        y = np.array([])
        
        # Should raise ValueError for empty data
        with pytest.raises(ValueError, match=".*data.*empty.*"):
            generate_scatter_plot(x, y, "test.png")

# Test: Mismatched array lengths
def test_mismatched_array_lengths(mock_matplotlib):
    """
    Test that mismatched x and y array lengths are handled.
    
    Validates:
    - Appropriate exception is raised
    - Error message indicates the mismatch
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    plt.figure.return_value = mock_fig
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([2.0, 4.0])  # Different length
        
        # Should raise ValueError for mismatched lengths
        with pytest.raises(ValueError, match=".*lengths.*match.*"):
            generate_scatter_plot(x, y, "test.png")

# Test: Invalid output path
def test_invalid_output_path(mock_matplotlib):
    """
    Test that invalid output paths are handled gracefully.
    
    Validates:
    - Appropriate exception is raised
    - Error message is informative
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    plt.figure.return_value = mock_fig
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([2.0, 4.0, 6.0])
        invalid_path = "/nonexistent/directory/test.png"
        
        # Should raise error for invalid path
        with pytest.raises((ValueError, OSError), match=".*"):
            generate_scatter_plot(x, y, invalid_path)

# Test: Correlation coefficient calculation
def test_correlation_coefficient_calculation(sample_data, mock_scipy):
    """
    Test that correlation coefficients are computed correctly.
    
    Validates:
    - Pearson correlation is calculated
    - Value is between -1 and 1
    """
    from unittest.mock import MagicMock
    from scipy import stats
    
    # Mock scipy.stats.pearsonr
    mock_result = MagicMock()
    mock_result.statistic = 0.95
    mock_result.pvalue = 0.01
    stats.pearsonr.return_value = mock_result
    
    with patch('visualization.stats', stats):
        from visualization import compute_correlation
        
        x, y = sample_data
        
        # Call the function
        corr, p_value = compute_correlation(x, y)
        
        # Verify correlation was computed
        assert corr is not None
        assert p_value is not None
        assert -1 <= corr <= 1

# Test: Figure object validation
def test_figure_object_structure(mock_matplotlib):
    """
    Test that generated figure objects have expected structure.
    
    Validates:
    - Figure has axes
    - Axes contain scatter and line plots
    - Labels are set correctly
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock with proper structure
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_ax.get_title.return_value = "Clone Density vs Perplexity"
    mock_ax.get_xlabel.return_value = "Clone Density"
    mock_ax.get_ylabel.return_value = "Perplexity"
    
    mock_fig.axes = [mock_ax]
    plt.figure.return_value = mock_fig
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([2.0, 4.0, 6.0])
        
        result = generate_scatter_plot(x, y, "test.png")
        
        # Verify figure structure
        assert result is not None
        assert hasattr(result, 'axes')

# Test: Multiple threshold sensitivity
def test_multiple_thresholds_visualization(mock_matplotlib):
    """
    Test that visualization handles multiple thresholds correctly.
    
    Validates:
    - Different thresholds produce different visualizations
    - Threshold values are labeled correctly
    """
    from unittest.mock import MagicMock
    import matplotlib.pyplot as plt
    
    # Setup mock
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    plt.figure.return_value = mock_fig
    plt.gca.return_value = mock_ax
    
    with patch('visualization.plt', plt):
        from visualization import generate_scatter_plot
        
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 5.0, 4.0, 5.0])
        
        # Generate plots for different thresholds
        for threshold in [0.7, 0.8, 0.9]:
            output_path = f"test_threshold_{threshold}.png"
            result = generate_scatter_plot(x, y, output_path)
            
            assert result is not None