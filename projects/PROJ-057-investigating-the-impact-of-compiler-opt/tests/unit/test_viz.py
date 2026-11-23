"""
Unit tests for visualization module.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from analysis.viz import (
    load_stability_metrics,
    parse_optimization_level,
    plot_pareto_frontier,
    generate_pareto_exploration,
    generate_pareto_final
)

class TestLoadStabilityMetrics:
    def test_load_existing_csv(self, tmp_path):
        """Test loading an existing CSV file."""
        csv_path = tmp_path / "stability_metrics.csv"
        data = {
            'config_id': ['O2_512', 'O3_512', 'O2_768'],
            'kernel_type': ['matmul', 'softmax', 'layernorm'],
            'l2_error': [1e-6, 1e-5, 1e-4],
            'max_abs_diff': [1e-6, 1e-5, 1e-4],
            'status': ['stable', 'stable', 'unstable']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        result = load_stability_metrics(str(csv_path))
        
        assert len(result) == 3
        assert 'config_id' in result.columns
        assert 'max_abs_diff' in result.columns

    def test_load_nonexistent_csv(self, tmp_path):
        """Test loading a non-existent CSV file raises error."""
        with pytest.raises(FileNotFoundError):
            load_stability_metrics(str(tmp_path / "nonexistent.csv"))

class TestParseOptimizationLevel:
    def test_extract_O2(self):
        """Test extracting O2 from config_id."""
        assert parse_optimization_level("matmul_O2_512") == "O2"
    
    def test_extract_O3(self):
        """Test extracting O3 from config_id."""
        assert parse_optimization_level("softmax_O3_768") == "O3"
    
    def test_extract_O0(self):
        """Test extracting O0 from config_id."""
        assert parse_optimization_level("layernorm_O0_512") == "O0"
    
    def test_unknown_format(self):
        """Test unknown format returns 'unknown'."""
        assert parse_optimization_level("unknown_config") == "unknown"

class TestParetoFrontierPlot:
    def test_plot_with_stable_data(self, tmp_path):
        """Test plotting with stable data."""
        data = {
            'config_id': ['O2_512', 'O3_512', 'O2_768'],
            'median_latency': [10.5, 8.2, 15.3],
            'max_abs_diff': [1e-6, 1e-5, 1e-4]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "test_pareto.png"
        
        fig = plot_pareto_frontier(
            df=df,
            x_col='median_latency',
            y_col='max_abs_diff',
            title='Test Pareto',
            output_path=str(output_path),
            exclude_threshold=1e-5
        )
        
        assert os.path.exists(output_path)
        assert fig is not None
        plt.close(fig)

    def test_plot_with_downsampled_data(self, tmp_path):
        """Test plotting with downsampled configurations."""
        data = {
            'config_id': ['O2_512', 'O3_512_downsampled', 'O2_768_downsampled'],
            'median_latency': [10.5, 8.2, 15.3],
            'max_abs_diff': [1e-6, 1e-5, 1e-6]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "test_pareto_downsampled.png"
        
        fig = plot_pareto_frontier(
            df=df,
            x_col='median_latency',
            y_col='max_abs_diff',
            title='Test Pareto Downsampled',
            output_path=str(output_path),
            exclude_threshold=1e-5,
            show_downsampled=True
        )
        
        assert os.path.exists(output_path)
        assert fig is not None
        plt.close(fig)

    def test_plot_with_no_stable_data(self, tmp_path):
        """Test plotting when no data is stable."""
        data = {
            'config_id': ['O2_512', 'O3_512'],
            'median_latency': [10.5, 8.2],
            'max_abs_diff': [1e-4, 1e-4]  # Both above threshold
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "test_pareto_no_stable.png"
        
        fig = plot_pareto_frontier(
            df=df,
            x_col='median_latency',
            y_col='max_abs_diff',
            title='Test No Stable',
            output_path=str(output_path),
            exclude_threshold=1e-5
        )
        
        assert os.path.exists(output_path)
        assert fig is not None
        plt.close(fig)

class TestGenerateParetoExploration:
    def test_generate_exploration_plot(self, tmp_path):
        """Test generating exploration plot."""
        csv_path = tmp_path / "stability_metrics.csv"
        data = {
            'config_id': ['O2_512', 'O3_512', 'O2_768_downsampled'],
            'kernel_type': ['matmul', 'softmax', 'layernorm'],
            'l2_error': [1e-6, 1e-5, 1e-6],
            'max_abs_diff': [1e-6, 1e-5, 1e-6],
            'status': ['stable', 'stable', 'stable']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        output_path = tmp_path / "pareto_frontier_exploration.png"
        
        generate_pareto_exploration(
            stability_metrics_path=str(csv_path),
            output_path=str(output_path),
            exclude_threshold=1e-5
        )
        
        assert os.path.exists(output_path)

class TestGenerateParetoFinal:
    def test_generate_final_plot(self, tmp_path):
        """Test generating final plot."""
        csv_path = tmp_path / "stability_metrics.csv"
        data = {
            'config_id': ['O2_512', 'O3_512'],
            'kernel_type': ['matmul', 'softmax'],
            'l2_error': [1e-6, 1e-5],
            'max_abs_diff': [1e-6, 1e-5],
            'status': ['stable', 'stable']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        output_path = tmp_path / "pareto_frontier_final.png"
        
        generate_pareto_final(
            stability_metrics_path=str(csv_path),
            output_path=str(output_path),
            exclude_threshold=1e-5
        )
        
        assert os.path.exists(output_path)

class TestParetoFrontierIntegration:
    def test_pareto_frontier_excludes_unstable(self, tmp_path):
        """Test that unstable configurations are excluded from the plot."""
        csv_path = tmp_path / "stability_metrics.csv"
        data = {
            'config_id': ['O2_512', 'O3_512', 'O2_768'],
            'median_latency': [10.5, 8.2, 15.3],
            'max_abs_diff': [1e-6, 1e-5, 1e-4],  # Third is unstable
            'status': ['stable', 'stable', 'unstable']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        output_path = tmp_path / "test_pareto_exclusion.png"
        
        fig = plot_pareto_frontier(
            df=pd.read_csv(csv_path),
            x_col='median_latency',
            y_col='max_abs_diff',
            title='Test Exclusion',
            output_path=str(output_path),
            exclude_threshold=1e-5
        )
        
        # Verify the file was created
        assert os.path.exists(output_path)
        plt.close(fig)

    def test_pareto_frontier_includes_downsampled(self, tmp_path):
        """Test that downsampled configurations are included with distinct markers."""
        csv_path = tmp_path / "stability_metrics.csv"
        data = {
            'config_id': ['O2_512', 'O3_512_downsampled'],
            'median_latency': [10.5, 8.2],
            'max_abs_diff': [1e-6, 1e-6],
            'status': ['stable', 'stable']
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        output_path = tmp_path / "test_pareto_downsampled.png"
        
        fig = plot_pareto_frontier(
            df=pd.read_csv(csv_path),
            x_col='median_latency',
            y_col='max_abs_diff',
            title='Test Downsampled',
            output_path=str(output_path),
            exclude_threshold=1e-5,
            show_downsampled=True,
            downsampled_marker='X',
            downsampled_color='red'
        )
        
        assert os.path.exists(output_path)
        plt.close(fig)
