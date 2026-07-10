import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Import the module under test
# Note: We need to add the project root to sys.path to import 'viz'
sys_path_backup = list(__import__('sys').path)
project_root = Path(__file__).resolve().parent.parent.parent
__import__('sys').path.insert(0, str(project_root))

from viz.plots import (
    load_variance_matrix,
    filter_by_condition,
    create_scatter_plot,
    run_viz_analysis
)

from config import set_seed

set_seed(42)

class TestVizPlots:
    
    @pytest.fixture
    def sample_variance_df(self):
        """Create a sample variance matrix DataFrame."""
        data = {
            'gene_id': [f'gene_{i}' for i in range(100)],
            'gene_epigenetic_variance': np.random.rand(100) * 10,
            'gene_expression_variance': np.random.rand(100) * 5,
            'condition': np.random.choice(['fluctuating', 'constant'], 100)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_filter_by_condition(self, sample_variance_df):
        """Test filtering by specific condition."""
        filtered = filter_by_condition(sample_variance_df, ['fluctuating'])
        assert all(filtered['condition'] == 'fluctuating')
        assert len(filtered) < len(sample_variance_df)
        
        # Test with non-existent condition
        filtered_none = filter_by_condition(sample_variance_df, ['nonexistent'])
        assert len(filtered_none) == 0

    def test_create_scatter_plot(self, sample_variance_df, temp_output_dir):
        """Test that a scatter plot is created and saved correctly."""
        output_path = temp_output_dir / "test_plot.png"
        
        result_path = create_scatter_plot(
            df=sample_variance_df,
            output_path=output_path,
            title="Test Plot"
        )
        
        assert Path(result_path).exists()
        assert Path(result_path).suffix == '.png'
        assert Path(result_path).stat().st_size > 0

    def test_create_scatter_plot_empty_df(self, temp_output_dir):
        """Test that an empty DataFrame raises an error."""
        empty_df = pd.DataFrame(columns=['gene_epigenetic_variance', 'gene_expression_variance', 'condition'])
        output_path = temp_output_dir / "empty_plot.png"
        
        with pytest.raises(ValueError, match="Cannot create plot: input DataFrame is empty"):
            create_scatter_plot(df=empty_df, output_path=output_path)

    def test_run_viz_analysis(self, sample_variance_df, temp_output_dir):
        """Test the full analysis pipeline."""
        # Mock the load_variance_matrix function to return our sample data
        with patch('viz.plots.load_variance_matrix', return_value=sample_variance_df):
            with patch('viz.plots.ensure_directories'):
                results = run_viz_analysis(
                    output_dir=str(temp_output_dir),
                    conditions=['fluctuating']
                )
        
        assert 'plot_path' in results
        assert 'total_genes' in results
        assert results['total_genes'] > 0
        assert Path(results['plot_path']).exists()

    def test_run_viz_analysis_with_invalid_conditions(self, sample_variance_df, temp_output_dir):
        """Test that invalid conditions are handled gracefully."""
        with patch('viz.plots.load_variance_matrix', return_value=sample_variance_df):
            with patch('viz.plots.ensure_directories'):
                # Should not crash, just filter to empty or warn
                results = run_viz_analysis(
                    output_dir=str(temp_output_dir),
                    conditions=['nonexistent_condition']
                )
        
        # If all conditions are filtered out, the plot might still be created but empty
        # or the function might handle it. The key is it doesn't crash.
        assert 'plot_path' in results
        assert Path(results['plot_path']).exists()

    def test_load_variance_matrix_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with patch('viz.plots.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                load_variance_matrix()

# Restore sys.path
__import__('sys').path[:] = sys_path_backup
