"""
Integration tests for the interpret CLI (T034, T050).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.cli.interpret import validate_plot_size, main
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

class TestPlotSizeLimitEnforced:
    """Tests for T050: Hardening - Plot Size Validation."""

    def test_plot_size_limit_enforced(self, tmp_path):
        """
        Integration test: test_plot_size_limit_enforced.
        Verifies that if total plot size > 10MB, a SystemExit is raised.
        """
        # Setup: Create a temporary directory and simulate large plots
        plot_dir = tmp_path / "results"
        plot_dir.mkdir()

        # Create a fake large file (simulate a 12MB plot)
        # We create a file of exactly 12MB to exceed the 10MB limit
        large_file = plot_dir / "partial_dependence_mock.png"
        with open(large_file, "wb") as f:
            # Write 12 * 1024 * 1024 bytes of zeros
            f.write(b'\x00' * (12 * 1024 * 1024))

        # Verify file size
        assert large_file.stat().st_size == 12 * 1024 * 1024

        # Execute: Call validate_plot_size
        # We expect SystemExit to be raised
        with pytest.raises(SystemExit) as excinfo:
            validate_plot_size(str(plot_dir), "partial_dependence_*.png")

        # Verify: Check that the error message contains relevant info
        assert "Total plot size" in str(excinfo.value)
        assert "12.00" in str(excinfo.value) # 12 MB
        assert "10" in str(excinfo.value) # 10 MB limit
        assert "partial_dependence_mock.png" in str(excinfo.value)

    def test_plot_size_limit_passed(self, tmp_path):
        """
        Integration test: Verify that if total plot size <= 10MB, no error is raised.
        """
        # Setup: Create a temporary directory with small plots
        plot_dir = tmp_path / "results"
        plot_dir.mkdir()

        # Create a small file (1MB)
        small_file = plot_dir / "partial_dependence_small.png"
        with open(small_file, "wb") as f:
            f.write(b'\x00' * (1 * 1024 * 1024))

        # Execute: Call validate_plot_size
        # Should return True and not raise
        result = validate_plot_size(str(plot_dir), "partial_dependence_*.png")
        assert result is True

    def test_plot_size_limit_exactly_at_boundary(self, tmp_path):
        """
        Integration test: Verify behavior exactly at 10MB limit.
        """
        plot_dir = tmp_path / "results"
        plot_dir.mkdir()

        # Create a file exactly 10MB
        boundary_file = plot_dir / "partial_dependence_boundary.png"
        with open(boundary_file, "wb") as f:
            f.write(b'\x00' * (10 * 1024 * 1024))

        # Execute: Should pass (limit is > 10MB, so 10MB is ok)
        result = validate_plot_size(str(plot_dir), "partial_dependence_*.png")
        assert result is True

    def test_no_plots_found(self, tmp_path):
        """
        Integration test: Verify behavior when no plots are found.
        """
        plot_dir = tmp_path / "results"
        plot_dir.mkdir()

        # Execute: Should return True and log a warning
        result = validate_plot_size(str(plot_dir), "partial_dependence_*.png")
        assert result is True

    def test_directory_not_exists(self, tmp_path):
        """
        Integration test: Verify behavior when directory does not exist.
        """
        # Execute: Should return True and log a warning
        result = validate_plot_size(str(tmp_path / "nonexistent"), "partial_dependence_*.png")
        assert result is True

class TestInterpretPipeline:
    """Integration tests for the full main() flow (mocked)."""

    def test_main_success_with_mocked_generation(self, tmp_path, monkeypatch):
        """
        Test that main() runs successfully when plot generation is mocked
        and the resulting plots (if any) are within limits.
        """
        # Setup: Mock the generation functions to create a small file
        plot_dir = tmp_path / "results"
        plot_dir.mkdir()
        small_plot = plot_dir / "partial_dependence_test.png"
        with open(small_plot, "wb") as f:
            f.write(b'\x00' * (1 * 1024 * 1024)) # 1MB

        # Mock the generation functions to do nothing but ensure the file exists
        # (The file is already created above for the test)
        def mock_gen_plots():
            pass

        def mock_export_importance():
            pass

        monkeypatch.setattr("src.cli.interpret.generate_partial_dependence_plots", mock_gen_plots)
        monkeypatch.setattr("src.cli.interpret.export_feature_importance", mock_export_importance)

        # Change PLOT_DIR to our temp path for this test
        with patch("src.cli.interpret.PLOT_DIR", str(plot_dir)):
            # Execute
            try:
                main()
            except SystemExit as e:
                # Should not raise SystemExit in success case
                pytest.fail(f"main() raised SystemExit unexpectedly: {e}")

    def test_main_fails_on_large_plots(self, tmp_path, monkeypatch):
        """
        Test that main() raises SystemExit when generated plots exceed 10MB.
        """
        plot_dir = tmp_path / "results"
        plot_dir.mkdir()
        large_plot = plot_dir / "partial_dependence_large.png"
        with open(large_plot, "wb") as f:
            f.write(b'\x00' * (15 * 1024 * 1024)) # 15MB

        def mock_gen_plots():
            pass

        def mock_export_importance():
            pass

        monkeypatch.setattr("src.cli.interpret.generate_partial_dependence_plots", mock_gen_plots)
        monkeypatch.setattr("src.cli.interpret.export_feature_importance", mock_export_importance)

        with patch("src.cli.interpret.PLOT_DIR", str(plot_dir)):
            with pytest.raises(SystemExit) as excinfo:
                main()
            
            assert "Total plot size" in str(excinfo.value)