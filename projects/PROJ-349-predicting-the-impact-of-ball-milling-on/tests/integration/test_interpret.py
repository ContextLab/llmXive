import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.cli.interpret import validate_plot_size, main
from src.interpret.partial_dependence import generate_partial_dependence_plots
from src.interpret.feature_importance import export_feature_importance

class TestPlotSizeLimitEnforced:
    """
    Integration test to verify that plot size validation is enforced.
    """

    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary results directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_plot_size_under_limit(self, temp_results_dir):
        """Test that validation passes when total size is under 10MB."""
        # Create a small plot file (1KB)
        small_plot = Path(temp_results_dir) / "partial_dependence_test.png"
        with open(small_plot, "wb") as f:
            f.write(b"x" * 1024)  # 1KB of data

        # Validation should pass without raising
        validate_plot_size(temp_results_dir)

    def test_plot_size_over_limit(self, temp_results_dir):
        """Test that validation fails when total size exceeds 10MB."""
        # Create a large plot file (11MB)
        large_plot = Path(temp_results_dir) / "partial_dependence_large.png"
        with open(large_plot, "wb") as f:
            f.write(b"x" * (11 * 1024 * 1024))  # 11MB of data

        # Validation should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            validate_plot_size(temp_results_dir)
        
        assert exc_info.value.code == 1

    def test_multiple_small_plots_exceed_limit(self, temp_results_dir):
        """Test that multiple small plots exceeding limit are caught."""
        # Create 20 plot files of 600KB each (total ~12MB)
        for i in range(20):
            plot_file = Path(temp_results_dir) / f"partial_dependence_{i}.png"
            with open(plot_file, "wb") as f:
                f.write(b"x" * (600 * 1024))  # 600KB

        # Validation should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            validate_plot_size(temp_results_dir)
        
        assert exc_info.value.code == 1

    def test_no_plots_directory(self, temp_results_dir):
        """Test behavior when no plots exist."""
        # Validation should pass (no plots to check)
        validate_plot_size(temp_results_dir)

    def test_nonexistent_directory(self):
        """Test behavior when results directory does not exist."""
        # Should log warning and return without raising
        with patch("src.cli.interpret.logger") as mock_logger:
            validate_plot_size("/nonexistent/path")
            mock_logger.warning.assert_called()

class TestInterpretPipeline:
    """
    Integration test for the full interpret pipeline.
    """

    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary results directory for testing."""
        temp_dir = tempfile.mkdtemp()
        # Create the directory structure
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        yield temp_dir
        shutil.rmtree(temp_dir)

    @patch("src.cli.interpret.generate_partial_dependence_plots")
    @patch("src.cli.interpret.export_feature_importance")
    @patch("src.cli.interpret.validate_plot_size")
    def test_main_pipeline_success(
        self, 
        mock_validate, 
        mock_export, 
        mock_generate,
        temp_results_dir
    ):
        """Test that main pipeline executes all steps successfully."""
        with patch("src.cli.interpret.logger") as mock_logger:
            # Mock the functions to do nothing
            mock_generate.return_value = None
            mock_export.return_value = None
            mock_validate.return_value = None

            # Run main
            with patch("src.cli.interpret.validate_plot_size", return_value=None):
                main()

            # Verify all steps were called
            mock_generate.assert_called_once()
            mock_export.assert_called_once()
            mock_validate.assert_called_once()
            mock_logger.info.assert_any_call("Interpret pipeline completed successfully.")

    @patch("src.cli.interpret.generate_partial_dependence_plots")
    def test_main_pipeline_failure_on_generation(self, mock_generate, temp_results_dir):
        """Test that main pipeline handles generation failure."""
        mock_generate.side_effect = Exception("Generation failed")

        with pytest.raises(Exception) as exc_info:
            with patch("src.cli.interpret.logger"):
                main()
        
        assert "Generation failed" in str(exc_info.value)

    @patch("src.cli.interpret.generate_partial_dependence_plots")
    @patch("src.cli.interpret.export_feature_importance")
    def test_main_pipeline_failure_on_export(self, mock_export, mock_generate, temp_results_dir):
        """Test that main pipeline handles export failure."""
        mock_generate.return_value = None
        mock_export.side_effect = Exception("Export failed")

        with pytest.raises(Exception) as exc_info:
            with patch("src.cli.interpret.logger"):
                main()
        
        assert "Export failed" in str(exc_info.value)

    @patch("src.cli.interpret.generate_partial_dependence_plots")
    @patch("src.cli.interpret.export_feature_importance")
    def test_main_pipeline_failure_on_validation(self, mock_export, mock_generate, temp_results_dir):
        """Test that main pipeline handles validation failure (SystemExit)."""
        mock_generate.return_value = None
        mock_export.return_value = None

        with pytest.raises(SystemExit):
            with patch("src.cli.interpret.validate_plot_size", side_effect=SystemExit(1)):
                main()