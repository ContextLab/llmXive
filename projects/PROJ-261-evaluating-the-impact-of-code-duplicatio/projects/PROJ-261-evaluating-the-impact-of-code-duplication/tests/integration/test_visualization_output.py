"""
Integration test for scatter-plot output format validation.

This test validates that the visualization module produces correct scatter plot
outputs with proper format, structure, and content as specified in the research
requirements for User Story 3.

Test validates:
- Output files exist in correct location
- Files are valid image format (PNG/PDF)
- Files have expected naming convention
- Scatter plots contain regression lines
- Files have minimum size threshold (not empty/corrupted)
"""
import os
import pytest
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import numpy as np

# Project imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from visualization import (
    setup_logging,
    load_correlation_data,
    compute_regression,
    create_scatter_plot_with_regression,
    create_clone_density_vs_perplexity_plot,
    create_clone_density_vs_accuracy_plot,
    create_sensitivity_analysis_plot,
    generate_all_visualizations
)
from config import (
    get_figure_format,
    get_figure_dpi,
    get_clone_thresholds
)


class TestVisualizationOutputFormat:
    """Integration tests for scatter-plot output format validation."""

    @pytest.fixture
    def sample_correlation_data(self, tmp_path):
        """Create sample correlation data for testing."""
        # Create sample data that mimics real correlation results
        data = {
            'threshold': [0.7, 0.7, 0.7, 0.8, 0.8, 0.8, 0.9, 0.9, 0.9],
            'clone_density': [0.15, 0.25, 0.35, 0.18, 0.28, 0.38, 0.22, 0.32, 0.42],
            'perplexity': [12.5, 11.2, 10.8, 12.3, 11.0, 10.5, 12.1, 10.8, 10.2],
            'accuracy': [0.75, 0.78, 0.80, 0.74, 0.77, 0.79, 0.73, 0.76, 0.78]
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / 'correlation_results.csv'
        df.to_csv(output_path, index=False)
        return output_path

    @pytest.fixture
    def figures_output_dir(self, tmp_path):
        """Create figures output directory."""
        output_dir = tmp_path / 'figures'
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def test_scatter_plot_file_exists(self, sample_correlation_data, figures_output_dir):
        """Test that scatter plot output file is created."""
        # Load and validate correlation data
        correlation_data = load_correlation_data(sample_correlation_data)
        assert correlation_data is not None
        assert len(correlation_data) > 0

        # Create scatter plot
        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        # Save figure
        output_path = figures_output_dir / 'clone_density_vs_perplexity.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Validate file exists
        assert output_path.exists(), f"Output file not created: {output_path}"

    def test_scatter_plot_valid_png_format(self, sample_correlation_data, figures_output_dir):
        """Test that scatter plot is valid PNG format."""
        correlation_data = load_correlation_data(sample_correlation_data)

        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        output_path = figures_output_dir / 'clone_density_vs_perplexity.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Check file size (should be > 0 for valid image)
        file_size = output_path.stat().st_size
        assert file_size > 1000, f"File too small (possible corruption): {file_size} bytes"

        # Validate PNG header magic bytes
        with open(output_path, 'rb') as f:
            header = f.read(8)
            # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
            expected_header = b'\x89PNG\r\n\x1a\n'
            assert header == expected_header, f"Invalid PNG header: {header.hex()}"

    def test_scatter_plot_contains_regression_line(self, sample_correlation_data, figures_output_dir):
        """Test that scatter plot contains regression line."""
        correlation_data = load_correlation_data(sample_correlation_data)

        # Compute regression to verify it works
        x_values = correlation_data['clone_density'].values
        y_values = correlation_data['perplexity'].values

        slope, intercept, r_value, p_value, std_err = compute_regression(x_values, y_values)

        # Regression should produce valid coefficients
        assert not np.isnan(slope), "Regression slope is NaN"
        assert not np.isnan(intercept), "Regression intercept is NaN"
        assert -np.inf < slope < np.inf, "Regression slope is infinite"
        assert -np.inf < intercept < np.inf, "Regression intercept is infinite"

        # Create plot and verify regression line is added
        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        # Check that regression line was added to axes
        lines = ax.get_lines()
        assert len(lines) >= 1, "No regression line found in plot"

        plt.close(fig)

    def test_scatter_plot_naming_convention(self, sample_correlation_data, figures_output_dir):
        """Test that scatter plot follows expected naming convention."""
        correlation_data = load_correlation_data(sample_correlation_data)

        # Test all expected output file names
        expected_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_accuracy.png',
            'sensitivity_analysis.png'
        ]

        for filename in expected_files:
            output_path = figures_output_dir / filename
            assert output_path.name == filename, f"Unexpected filename: {output_path.name}"

            # Verify naming follows pattern: {metric1}_vs_{metric2}.{format}
            assert '_vs_' in filename, f"Filename should contain '_vs_' separator: {filename}"
            assert filename.endswith('.png'), f"Filename should end with .png: {filename}"

    def test_scatter_plot_minimum_size(self, sample_correlation_data, figures_output_dir):
        """Test that scatter plot has minimum file size (not empty)."""
        correlation_data = load_correlation_data(sample_correlation_data)

        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        output_path = figures_output_dir / 'clone_density_vs_perplexity.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        file_size = output_path.stat().st_size
        # Minimum 1KB for valid scatter plot with data points and regression line
        assert file_size >= 1024, f"File too small: {file_size} bytes (minimum 1KB expected)"

    def test_scatter_plot_labels_present(self, sample_correlation_data, figures_output_dir):
        """Test that scatter plot has required labels."""
        correlation_data = load_correlation_data(sample_correlation_data)

        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        # Check title
        title = ax.get_title()
        assert title == 'Clone Density vs Perplexity', f"Unexpected title: {title}"

        # Check x-label
        xlabel = ax.get_xlabel()
        assert xlabel == 'Clone Density', f"Unexpected x-label: {xlabel}"

        # Check y-label
        ylabel = ax.get_ylabel()
        assert ylabel == 'Perplexity', f"Unexpected y-label: {ylabel}"

        plt.close(fig)

    def test_sensitivity_analysis_plot_format(self, sample_correlation_data, figures_output_dir):
        """Test sensitivity analysis plot output format."""
        correlation_data = load_correlation_data(sample_correlation_data)

        thresholds = get_clone_thresholds()
        assert len(thresholds) >= 3, f"Expected at least 3 thresholds, got {len(thresholds)}"

        # Create sensitivity analysis plot
        fig, ax = create_sensitivity_analysis_plot(
            correlation_data,
            thresholds=thresholds,
            figure_format='png',
            figure_dpi=300
        )

        output_path = figures_output_dir / 'sensitivity_analysis.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        assert output_path.exists(), f"Sensitivity analysis plot not created: {output_path}"
        assert output_path.stat().st_size >= 1024, f"Sensitivity analysis plot too small"

    def test_multiple_thresholds_in_output(self, sample_correlation_data, figures_output_dir):
        """Test that output includes data for all configured thresholds."""
        correlation_data = load_correlation_data(sample_correlation_data)
        thresholds = get_clone_thresholds()

        # Verify correlation data contains all thresholds
        data_thresholds = set(correlation_data['threshold'].unique())
        expected_thresholds = set(thresholds)

        # At minimum, the data should contain the configured thresholds
        assert len(data_thresholds) >= len(expected_thresholds), \
            f"Expected {len(expected_thresholds)} thresholds, got {len(data_thresholds)}"

        # Create plot with all thresholds
        fig, ax = create_sensitivity_analysis_plot(
            correlation_data,
            thresholds=thresholds,
            figure_format='png',
            figure_dpi=300
        )

        output_path = figures_output_dir / 'sensitivity_analysis.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        assert output_path.exists()

    def test_pdf_format_output(self, sample_correlation_data, figures_output_dir):
        """Test that PDF format output is generated correctly."""
        correlation_data = load_correlation_data(sample_correlation_data)

        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='pdf',
            figure_dpi=300
        )

        output_path = figures_output_dir / 'clone_density_vs_perplexity.pdf'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        assert output_path.exists(), f"PDF output not created: {output_path}"

        # Check PDF magic bytes
        with open(output_path, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF', f"Invalid PDF header: {header}"

    def test_dpi_configuration_respected(self, sample_correlation_data, figures_output_dir):
        """Test that configured DPI is applied to output."""
        correlation_data = load_correlation_data(sample_correlation_data)
        expected_dpi = get_figure_dpi()

        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=expected_dpi
        )

        # Verify figure DPI setting
        assert fig.dpi == expected_dpi, f"Expected DPI {expected_dpi}, got {fig.dpi}"

        output_path = figures_output_dir / 'clone_density_vs_perplexity.png'
        fig.savefig(output_path, dpi=expected_dpi, bbox_inches='tight')
        plt.close(fig)

        assert output_path.exists()

    def test_correlation_data_validation(self, tmp_path):
        """Test that correlation data is properly validated before plotting."""
        # Test with valid data
        valid_data = {
            'threshold': [0.7, 0.8, 0.9],
            'clone_density': [0.15, 0.25, 0.35],
            'perplexity': [12.5, 11.2, 10.8],
            'accuracy': [0.75, 0.78, 0.80]
        }
        df = pd.DataFrame(valid_data)
        output_path = tmp_path / 'valid_correlation_results.csv'
        df.to_csv(output_path, index=False)

        loaded_data = load_correlation_data(output_path)
        assert loaded_data is not None
        assert len(loaded_data) == 3

        # Test with empty data
        empty_df = pd.DataFrame()
        empty_path = tmp_path / 'empty_correlation_results.csv'
        empty_df.to_csv(empty_path, index=False)

        loaded_empty = load_correlation_data(empty_path)
        assert loaded_empty is None or len(loaded_empty) == 0

    def test_regression_r_squared_value(self, sample_correlation_data, figures_output_dir):
        """Test that regression produces valid R-squared value."""
        correlation_data = load_correlation_data(sample_correlation_data)

        x_values = correlation_data['clone_density'].values
        y_values = correlation_data['perplexity'].values

        slope, intercept, r_value, p_value, std_err = compute_regression(x_values, y_values)

        # R-squared should be between 0 and 1
        r_squared = r_value ** 2
        assert 0 <= r_squared <= 1, f"R-squared out of range: {r_squared}"

        # R-value should be between -1 and 1
        assert -1 <= r_value <= 1, f"R-value out of range: {r_value}"

    def test_outlier_handling_in_scatter_plot(self, tmp_path, figures_output_dir):
        """Test that scatter plot handles outliers gracefully."""
        # Create data with potential outliers
        data = {
            'threshold': [0.7, 0.7, 0.7, 0.7, 0.7],
            'clone_density': [0.15, 0.25, 0.35, 0.45, 1.5],  # 1.5 is an outlier
            'perplexity': [12.5, 11.2, 10.8, 10.5, 5.0],  # 5.0 is an outlier
            'accuracy': [0.75, 0.78, 0.80, 0.82, 0.95]
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / 'outlier_correlation_results.csv'
        df.to_csv(output_path, index=False)

        correlation_data = load_correlation_data(output_path)
        assert correlation_data is not None

        # Plot should still be created with outliers
        fig, ax = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity (with outliers)',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        output_path_fig = figures_output_dir / 'outlier_test.png'
        fig.savefig(output_path_fig, dpi=300, bbox_inches='tight')
        plt.close(fig)

        assert output_path_fig.exists()

    def test_empty_dataframe_handling(self, tmp_path, figures_output_dir):
        """Test that empty correlation data is handled gracefully."""
        empty_df = pd.DataFrame(columns=['threshold', 'clone_density', 'perplexity', 'accuracy'])
        output_path = tmp_path / 'empty_correlation_results.csv'
        empty_df.to_csv(output_path, index=False)

        loaded_data = load_correlation_data(output_path)
        assert loaded_data is None or len(loaded_data) == 0

        # Should not raise exception when trying to plot
        try:
            if loaded_data is not None and len(loaded_data) > 0:
                fig, ax = create_scatter_plot_with_regression(
                    loaded_data,
                    x_col='clone_density',
                    y_col='perplexity',
                    title='Test',
                    x_label='Clone Density',
                    y_label='Perplexity',
                    figure_format='png',
                    figure_dpi=300
                )
                plt.close(fig)
        except Exception as e:
            # Empty data should either be handled or raise a clear error
            assert "empty" in str(e).lower() or "no data" in str(e).lower(), \
                f"Unexpected error for empty data: {e}"

    def test_generated_visualizations_completeness(self, sample_correlation_data, figures_output_dir):
        """Test that all expected visualizations are generated."""
        correlation_data = load_correlation_data(sample_correlation_data)

        # Generate all visualizations
        generated_files = generate_all_visualizations(
            correlation_data,
            output_dir=figures_output_dir,
            figure_format='png',
            figure_dpi=300
        )

        # Check all expected files were generated
        expected_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_accuracy.png',
            'sensitivity_analysis.png'
        ]

        for expected in expected_files:
            assert expected in generated_files, f"Missing expected file: {expected}"
            assert (figures_output_dir / expected).exists(), \
                f"File not created: {figures_output_dir / expected}"

    def test_visualization_reproducibility(self, sample_correlation_data, figures_output_dir):
        """Test that visualization output is reproducible with same inputs."""
        import hashlib

        correlation_data = load_correlation_data(sample_correlation_data)

        # Generate first plot
        fig1, ax1 = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        output_path1 = figures_output_dir / 'repro_test_1.png'
        fig1.savefig(output_path1, dpi=300, bbox_inches='tight')
        plt.close(fig1)

        # Generate second plot with same inputs
        fig2, ax2 = create_scatter_plot_with_regression(
            correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            title='Clone Density vs Perplexity',
            x_label='Clone Density',
            y_label='Perplexity',
            figure_format='png',
            figure_dpi=300
        )

        output_path2 = figures_output_dir / 'repro_test_2.png'
        fig2.savefig(output_path2, dpi=300, bbox_inches='tight')
        plt.close(fig2)

        # Note: Due to matplotlib rendering variations, exact byte-for-byte
        # reproducibility is not guaranteed, but file sizes should be similar
        size1 = output_path1.stat().st_size
        size2 = output_path2.stat().st_size

        # Allow 10% variance in file size
        assert abs(size1 - size2) / max(size1, size2) < 0.1, \
            f"File sizes differ too much: {size1} vs {size2}"
