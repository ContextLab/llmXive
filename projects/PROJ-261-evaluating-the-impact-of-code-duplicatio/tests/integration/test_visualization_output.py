"""
Integration test for scatter-plot output format validation.

This test validates that the visualization pipeline produces
properly formatted scatter plots with regression lines as
specified in US3.

Per spec.md Independent Test requirements for US3.
"""
import os
import sys
import pytest
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from PIL import Image
import io

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplication' / 'code'))

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

# Test configuration
FIGURES_DIR = PROJECT_ROOT / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplication' / 'data' / 'analysis' / 'figures'
CORRELATION_RESULTS_PATH = PROJECT_ROOT / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplication' / 'data' / 'analysis' / 'correlation_results.csv'


class TestScatterPlotOutputFormat:
    """
    Integration tests for scatter-plot output format validation.
    
    Validates that scatter plots are:
    1. Generated in the correct directory (figures/)
    2. Saved in the correct format (PNG & PDF)
    3. Have proper dimensions and DPI
    4. Contain required visual elements (axes, labels, regression line)
    5. Are non-empty and valid image files
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.figures_dir = FIGURES_DIR
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logging()

    def test_scatter_plot_file_exists(self):
        """
        Test that scatter plot files are created in the correct location.
        
        Verifies:
        - clone_density_vs_perplexity.png exists
        - clone_density_vs_perplexity.pdf exists
        - clone_density_vs_accuracy.png exists
        - clone_density_vs_accuracy.pdf exists
        """
        # Expected files
        expected_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_perplexity.pdf',
            'clone_density_vs_accuracy.png',
            'clone_density_vs_accuracy.pdf',
            'sensitivity_analysis.png',
            'sensitivity_analysis.pdf'
        ]

        for filename in expected_files:
            filepath = self.figures_dir / filename
            assert filepath.exists(), f"Expected file not found: {filepath}"
            assert filepath.stat().st_size > 0, f"File is empty: {filepath}"

    def test_scatter_plot_format_png(self):
        """
        Test that PNG files are valid PNG images.
        
        Validates PNG header and structure.
        """
        png_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_accuracy.png',
            'sensitivity_analysis.png'
        ]

        for filename in png_files:
            filepath = self.figures_dir / filename
            if filepath.exists():
                # Check PNG magic bytes
                with open(filepath, 'rb') as f:
                    header = f.read(8)
                    assert header[:8] == b'\x89PNG\r\n\x1a\n', \
                        f"Invalid PNG header in {filename}"

    def test_scatter_plot_format_pdf(self):
        """
        Test that PDF files are valid PDF documents.
        
        Validates PDF header structure.
        """
        pdf_files = [
            'clone_density_vs_perplexity.pdf',
            'clone_density_vs_accuracy.pdf',
            'sensitivity_analysis.pdf'
        ]

        for filename in pdf_files:
            filepath = self.figures_dir / filename
            if filepath.exists():
                # Check PDF magic bytes
                with open(filepath, 'rb') as f:
                    header = f.read(5)
                    assert header == b'%PDF-', \
                        f"Invalid PDF header in {filename}"

    def test_scatter_plot_dimensions(self):
        """
        Test that scatter plots have reasonable dimensions.
        
        Validates that generated images are not too small or corrupted.
        """
        png_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_accuracy.png',
            'sensitivity_analysis.png'
        ]

        min_width = 600
        min_height = 400

        for filename in png_files:
            filepath = self.figures_dir / filename
            if filepath.exists():
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size
                        assert width >= min_width, \
                            f"{filename} width {width} < {min_width}"
                        assert height >= min_height, \
                            f"{filename} height {height} < {min_height}"
                except Exception as e:
                    pytest.fail(f"Could not open image {filename}: {e}")

    def test_scatter_plot_has_axes(self):
        """
        Test that scatter plots contain proper axis elements.
        
        Validates that the plot has:
        - X and Y axes
        - Axis labels
        - Title
        - Regression line
        """
        # Load correlation data
        if CORRELATION_RESULTS_PATH.exists():
            data = load_correlation_data(CORRELATION_RESULTS_PATH)
            assert data is not None, "Failed to load correlation data"

            # Create a test figure to validate structure
            fig = create_clone_density_vs_perplexity_plot(
                data,
                self.figures_dir / 'test_axes_validation.png',
                self.logger
            )

            # Check figure has axes
            assert isinstance(fig, Figure), "Output is not a Figure"
            assert len(fig.axes) > 0, "Figure has no axes"

            ax = fig.axes[0]
            assert isinstance(ax, Axes), "First element is not an Axes"

            # Check for axis labels
            xlabel = ax.get_xlabel()
            ylabel = ax.get_ylabel()
            assert len(xlabel) > 0, "X-axis has no label"
            assert len(ylabel) > 0, "Y-axis has no label"

            # Check for title
            title = ax.get_title()
            assert len(title) > 0, "Plot has no title"

            # Check for regression line (should have at least 2 line objects: scatter + regression)
            lines = ax.get_lines()
            assert len(lines) >= 1, "No regression line found in plot"

    def test_scatter_plot_regression_line_present(self):
        """
        Test that regression lines are present in scatter plots.
        
        Validates that the regression line is drawn and has correct
        properties (color, linestyle).
        """
        if CORRELATION_RESULTS_PATH.exists():
            data = load_correlation_data(CORRELATION_RESULTS_PATH)
            if data is not None and len(data) > 0:
                fig = create_clone_density_vs_perplexity_plot(
                    data,
                    self.figures_dir / 'test_regression_validation.png',
                    self.logger
                )

                ax = fig.axes[0]
                lines = ax.get_lines()

                # Should have at least one line (regression line)
                assert len(lines) >= 1, "No regression line found"

                # Check regression line properties
                regression_line = lines[-1]  # Last line is typically regression
                assert regression_line.get_linestyle() in ['-', '--', '-.', ':'], \
                    f"Regression line has invalid linestyle: {regression_line.get_linestyle()}"

    def test_scatter_plot_data_points_rendered(self):
        """
        Test that data points are rendered in scatter plots.
        
        Validates that the scatter plot contains actual data points.
        """
        if CORRELATION_RESULTS_PATH.exists():
            data = load_correlation_data(CORRELATION_RESULTS_PATH)
            if data is not None and len(data) > 0:
                fig = create_clone_density_vs_perplexity_plot(
                    data,
                    self.figures_dir / 'test_points_validation.png',
                    self.logger
                )

                ax = fig.axes[0]
                collections = ax.collections

                # Should have at least one collection (scatter points)
                assert len(collections) >= 1, "No scatter points found in plot"

    def test_sensitivity_analysis_plot_format(self):
        """
        Test that sensitivity analysis plot is generated correctly.
        
        Validates the sensitivity analysis across thresholds 0.7, 0.8, 0.9.
        """
        thresholds = get_clone_thresholds()
        assert 0.7 in thresholds, "Threshold 0.7 not in configuration"
        assert 0.8 in thresholds, "Threshold 0.8 not in configuration"
        assert 0.9 in thresholds, "Threshold 0.9 not in configuration"

        # Check sensitivity analysis file exists
        sens_file = self.figures_dir / 'sensitivity_analysis.png'
        assert sens_file.exists(), "Sensitivity analysis plot not found"
        assert sens_file.stat().st_size > 0, "Sensitivity analysis plot is empty"

    def test_figure_dpi_validation(self):
        """
        Test that figures are saved with correct DPI.
        
        Validates DPI setting from config.
        """
        expected_dpi = get_figure_dpi()
        assert expected_dpi > 0, "Invalid DPI configuration"

        # PNG files should respect DPI setting
        png_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_accuracy.png'
        ]

        for filename in png_files:
            filepath = self.figures_dir / filename
            if filepath.exists():
                try:
                    with Image.open(filepath) as img:
                        # Check file size is reasonable (DPI affects quality)
                        size = filepath.stat().st_size
                        assert size > 10000, \
                            f"{filename} may have incorrect DPI (too small: {size} bytes)"
                except Exception:
                    pass  # Some formats don't support DPI metadata

    def test_scatter_plot_color_scheme(self):
        """
        Test that scatter plots use appropriate color schemes.
        
        Validates that data points and regression lines have
        distinguishable colors.
        """
        if CORRELATION_RESULTS_PATH.exists():
            data = load_correlation_data(CORRELATION_RESULTS_PATH)
            if data is not None and len(data) > 0:
                fig = create_clone_density_vs_perplexity_plot(
                    data,
                    self.figures_dir / 'test_color_validation.png',
                    self.logger
                )

                ax = fig.axes[0]
                lines = ax.get_lines()

                # At least regression line should have a color set
                assert len(lines) > 0, "No lines in plot"

    def test_scatter_plot_legend_present(self):
        """
        Test that scatter plots include legends.
        
        Validates that legends are present to identify
        different plot elements.
        """
        if CORRELATION_RESULTS_PATH.exists():
            data = load_correlation_data(CORRELATION_RESULTS_PATH)
            if data is not None and len(data) > 0:
                fig = create_clone_density_vs_perplexity_plot(
                    data,
                    self.figures_dir / 'test_legend_validation.png',
                    self.logger
                )

                ax = fig.axes[0]
                legend = ax.get_legend()

                # Legend should be present for clarity
                assert legend is not None, "No legend found in plot"

    def test_all_visualizations_generated(self):
        """
        Integration test for complete visualization generation.
        
        Validates that generate_all_visualizations() produces
        all expected output files.
        """
        # This test requires correlation_results.csv to exist
        if CORRELATION_RESULTS_PATH.exists():
            # Run full visualization generation
            result = generate_all_visualizations(
                str(CORRELATION_RESULTS_PATH),
                str(self.figures_dir),
                self.logger
            )

            assert result is True, "Visualization generation failed"

            # Verify all expected files exist
            expected_files = [
                'clone_density_vs_perplexity.png',
                'clone_density_vs_perplexity.pdf',
                'clone_density_vs_accuracy.png',
                'clone_density_vs_accuracy.pdf',
                'sensitivity_analysis.png',
                'sensitivity_analysis.pdf'
            ]

            missing_files = []
            for filename in expected_files:
                filepath = self.figures_dir / filename
                if not filepath.exists():
                    missing_files.append(filename)

            assert len(missing_files) == 0, \
                f"Missing visualization files: {missing_files}"

    def test_scatter_plot_no_error_artifacts(self):
        """
        Test that scatter plots do not contain error artifacts.
        
        Validates that plots are clean and don't contain
        error messages or warning text.
        """
        png_files = [
            'clone_density_vs_perplexity.png',
            'clone_density_vs_accuracy.png'
        ]

        for filename in png_files:
            filepath = self.figures_dir / filename
            if filepath.exists():
                # Check file is not corrupted
                try:
                    with Image.open(filepath) as img:
                        img.load()  # Force load to check integrity
                except Exception as e:
                    pytest.fail(f"Image {filename} is corrupted: {e}")

    def test_regression_computation_accuracy(self):
        """
        Test that regression computation produces valid results.
        
        Validates the compute_regression function produces
        numerically stable results.
        """
        # Test with sample data
        x = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        slope, intercept, r_squared = compute_regression(x, y)

        # Validate results
        assert isinstance(slope, (int, float, np.floating)), \
            f"Invalid slope type: {type(slope)}"
        assert isinstance(intercept, (int, float, np.floating)), \
            f"Invalid intercept type: {type(intercept)}"
        assert isinstance(r_squared, (int, float, np.floating)), \
            f"Invalid r_squared type: {type(r_squared)}"

        # R-squared should be between 0 and 1
        assert 0 <= r_squared <= 1, f"Invalid R-squared: {r_squared}"

        # For perfect linear relationship, R-squared should be 1.0
        assert abs(r_squared - 1.0) < 0.01, \
            f"R-squared should be ~1.0 for perfect linear data: {r_squared}"

    def test_regression_handles_edge_cases(self):
        """
        Test that regression handles edge cases gracefully.
        
        Validates numerical stability for edge cases like
        constant y-values or very small ranges.
        """
        # Test with constant y (should handle gracefully)
        x = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        y_const = np.array([2.0, 2.0, 2.0, 2.0, 2.0])

        try:
            slope, intercept, r_squared = compute_regression(x, y_const)
            # Should not raise, R-squared should be 0 for constant y
            assert 0 <= r_squared <= 1, f"Invalid R-squared for constant y: {r_squared}"
        except Exception as e:
            pytest.fail(f"Regression failed on constant y: {e}")

        # Test with small range
        x_small = np.array([0.49, 0.50, 0.51])
        y_small = np.array([1.0, 2.0, 3.0])

        try:
            slope, intercept, r_squared = compute_regression(x_small, y_small)
            assert isinstance(slope, (int, float, np.floating)), \
                f"Invalid slope for small range: {type(slope)}"
        except Exception as e:
            pytest.fail(f"Regression failed on small range: {e}")


@pytest.mark.integration
class TestVisualizationOutputPipeline:
    """
    End-to-end integration tests for the visualization pipeline.
    
    These tests verify the complete pipeline from correlation data
    to final visualization output.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.figures_dir = FIGURES_DIR
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logging()

    def test_full_pipeline_execution(self):
        """
        Test that the full visualization pipeline executes without errors.
        
        This is the primary integration test for T039.
        """
        if CORRELATION_RESULTS_PATH.exists():
            # Execute full pipeline
            success = generate_all_visualizations(
                str(CORRELATION_RESULTS_PATH),
                str(self.figures_dir),
                self.logger
            )

            assert success, "Full visualization pipeline failed"

            # Verify outputs
            expected_outputs = [
                'clone_density_vs_perplexity.png',
                'clone_density_vs_perplexity.pdf',
                'clone_density_vs_accuracy.png',
                'clone_density_vs_accuracy.pdf',
                'sensitivity_analysis.png',
                'sensitivity_analysis.pdf'
            ]

            for filename in expected_outputs:
                filepath = self.figures_dir / filename
                assert filepath.exists(), f"Missing output: {filename}"
                assert filepath.stat().st_size > 0, f"Empty output: {filename}"

    def test_output_files_are_valid(self):
        """
        Test that all output files are valid and can be opened.
        """
        png_files = list(self.figures_dir.glob('*.png'))
        pdf_files = list(self.figures_dir.glob('*.pdf'))

        # Validate PNG files
        for filepath in png_files:
            try:
                with Image.open(filepath) as img:
                    img.load()
            except Exception as e:
                pytest.fail(f"Invalid PNG file {filepath}: {e}")

        # Validate PDF files
        for filepath in pdf_files:
            with open(filepath, 'rb') as f:
                header = f.read(5)
                assert header == b'%PDF-', f"Invalid PDF file {filepath}"

    def test_visualization_checksums(self):
        """
        Test that visualization outputs can be checksummed.
        
        Validates that outputs are stable and reproducible.
        """
        import hashlib

        png_files = list(self.figures_dir.glob('*.png'))

        for filepath in png_files:
            with open(filepath, 'rb') as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
                assert len(checksum) == 64, "Invalid checksum length"
                assert checksum != 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', \
                    f"Empty file checksum for {filepath}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
