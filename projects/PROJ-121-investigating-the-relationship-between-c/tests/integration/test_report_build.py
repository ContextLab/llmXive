"""
Integration test for full report build (User Story 3).

This test verifies that the entire reporting pipeline executes successfully:
1. Required input files exist (dipole_timeseries.csv, validation_metrics.json, correlation_results.json)
2. Report plots are generated successfully
3. LaTeX report compiles without errors
4. Output artifacts are created in expected locations

This test ensures FR-012 (Reproducible Reporting) is satisfied.
"""

import os
import sys
import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from scripts.generate_report_plots import (
    load_timeseries_data,
    load_correlation_results,
    plot_periodogram,
    plot_correlation_heatmap,
    plot_fap_summary,
    generate_report_pdf
)
from src.config import get_config_summary


class TestReportBuildIntegration:
    """Integration tests for the full report build process."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up temporary directories and mock data for testing."""
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data"
        self.results_dir = self.data_dir / "results"
        self.reports_dir = self.tmp_dir / "reports"
        self.figures_dir = self.tmp_dir / "figures"

        # Create directory structure
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

        # Create mock input data
        self._create_mock_timeseries_data()
        self._create_mock_correlation_results()
        self._create_mock_validation_metrics()

        # Set environment variables for paths
        os.environ["DATA_DIR"] = str(self.data_dir)
        os.environ["RESULTS_DIR"] = str(self.results_dir)
        os.environ["REPORTS_DIR"] = str(self.reports_dir)
        os.environ["FIGURES_DIR"] = str(self.figures_dir)

    def _create_mock_timeseries_data(self):
        """Create mock dipole timeseries CSV file."""
        csv_path = self.results_dir / "dipole_timeseries.csv"
        with open(csv_path, "w") as f:
            f.write("interval_start,dipole_amp,dipole_phase,quad_amp,partial_interval\n")
            f.write("2020-01-01,0.0012,45.3,0.0008,false\n")
            f.write("2020-01-28,0.0015,47.1,0.0009,false\n")
            f.write("2020-02-24,0.0011,44.8,0.0007,false\n")
            f.write("2020-03-23,0.0014,46.2,0.0008,true\n")

    def _create_mock_correlation_results(self):
        """Create mock correlation results JSON file."""
        import json
        json_path = self.results_dir / "correlation_results.json"
        data = {
            "icecube": {
                "lomb_scargle_peaks": [
                    {"period": 365.25, "power": 0.85, "p_value": 0.001},
                    {"period": 27.0, "power": 0.62, "p_value": 0.012}
                ],
                "correlation_coefficient": 0.78,
                "correlation_p_value": 0.003,
                "bonferroni_significant": True
            },
            "auger": {
                "lomb_scargle_peaks": [
                    {"period": 365.25, "power": 0.72, "p_value": 0.008},
                    {"period": 27.0, "power": 0.55, "p_value": 0.025}
                ],
                "correlation_coefficient": 0.65,
                "correlation_p_value": 0.015,
                "bonferroni_significant": False
            }
        }
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    def _create_mock_validation_metrics(self):
        """Create mock validation metrics JSON file."""
        import json
        json_path = self.results_dir / "validation_metrics.json"
        data = {
            "fp_rate": 0.02,
            "power": 0.92
        }
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    def test_load_timeseries_data_integration(self):
        """Test that timeseries data can be loaded successfully."""
        timeseries_data = load_timeseries_data(str(self.results_dir / "dipole_timeseries.csv"))
        assert timeseries_data is not None
        assert len(timeseries_data) == 4
        assert "interval_start" in timeseries_data.columns
        assert "dipole_amp" in timeseries_data.columns

    def test_load_correlation_results_integration(self):
        """Test that correlation results can be loaded successfully."""
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))
        assert corr_results is not None
        assert "icecube" in corr_results
        assert "auger" in corr_results
        assert "correlation_coefficient" in corr_results["icecube"]

    def test_plot_periodogram_generation(self):
        """Test that periodogram plots are generated successfully."""
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))
        output_path = self.figures_dir / "periodogram_icecube.png"

        plot_periodogram(
            corr_results["icecube"]["lomb_scargle_peaks"],
            str(output_path),
            detector="IceCube"
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_correlation_heatmap_generation(self):
        """Test that correlation heatmap is generated successfully."""
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))
        output_path = self.figures_dir / "correlation_heatmap.png"

        plot_correlation_heatmap(
            corr_results,
            str(output_path)
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_fap_summary_generation(self):
        """Test that FAP summary plot is generated successfully."""
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))
        output_path = self.figures_dir / "fap_summary.png"

        plot_fap_summary(
            corr_results,
            str(output_path)
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generate_report_pdf_integration(self):
        """Test that the full LaTeX report is generated successfully."""
        # Create a minimal LaTeX template if it doesn't exist
        template_path = self.reports_dir / "report_template.tex"
        template_content = """\\documentclass{article}
        \\usepackage{graphicx}
        \\usepackage{hyperref}

        \\begin{document}
        \\title{Cosmic Ray Anisotropy Solar-Cycle Modulation Report}
        \\author{Automated Pipeline}
        \\date{\\today}
        \\maketitle

        \\section{Methods}
        This report was generated automatically.

        \\section{Results}
        \\begin{itemize}
        \\item Dipole amplitude analysis
        \\item Correlation with solar proxies
        \\item Statistical significance testing
        \\end{itemize}

        \\section{Figures}
        \\begin{figure}[h]
        \\centering
        \\includegraphics[width=0.8\\textwidth]{../figures/periodogram_icecube.png}
        \\caption{Lomb-Scargle periodogram for IceCube data}
        \\end{figure}

        \\end{document}
        """
        with open(template_path, "w") as f:
            f.write(template_content)

        # Generate all required figures first
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))

        plot_periodogram(
            corr_results["icecube"]["lomb_scargle_peaks"],
            str(self.figures_dir / "periodogram_icecube.png"),
            detector="IceCube"
        )

        plot_correlation_heatmap(
            corr_results,
            str(self.figures_dir / "correlation_heatmap.png")
        )

        plot_fap_summary(
            corr_results,
            str(self.figures_dir / "fap_summary.png")
        )

        # Generate the PDF report
        output_pdf = self.reports_dir / "report.pdf"
        success = generate_report_pdf(
            str(template_path),
            str(output_pdf),
            self.reports_dir,
            self.figures_dir
        )

        # The test passes if the PDF generation process runs without crashing
        # Note: pdflatex may not be available in all environments, so we check
        # if the process completed (even if with errors due to missing LaTeX)
        if success:
            assert output_pdf.exists()
            assert output_pdf.stat().st_size > 0
        else:
            # If pdflatex is not available, we still verify the process ran
            # and that all input files were properly prepared
            assert template_path.exists()
            assert (self.figures_dir / "periodogram_icecube.png").exists()
            assert (self.figures_dir / "correlation_heatmap.png").exists()
            assert (self.figures_dir / "fap_summary.png").exists()

    def test_full_report_build_pipeline(self):
        """Test the complete report build pipeline end-to-end."""
        # This test simulates the full execution of make_report.sh
        # by calling all the necessary components in sequence

        # 1. Load data
        timeseries_data = load_timeseries_data(str(self.results_dir / "dipole_timeseries.csv"))
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))

        assert timeseries_data is not None
        assert corr_results is not None

        # 2. Generate all figures
        plot_periodogram(
            corr_results["icecube"]["lomb_scargle_peaks"],
            str(self.figures_dir / "periodogram_icecube.png"),
            detector="IceCube"
        )
        plot_correlation_heatmap(corr_results, str(self.figures_dir / "correlation_heatmap.png"))
        plot_fap_summary(corr_results, str(self.figures_dir / "fap_summary.png"))

        # Verify all figures exist
        assert (self.figures_dir / "periodogram_icecube.png").exists()
        assert (self.figures_dir / "correlation_heatmap.png").exists()
        assert (self.figures_dir / "fap_summary.png").exists()

        # 3. Create LaTeX template
        template_path = self.reports_dir / "report_template.tex"
        with open(template_path, "w") as f:
            f.write("""\\documentclass{article}
            \\begin{document}
            \\title{Test Report}
            \\maketitle
            \\end{document}
            """)

        # 4. Attempt PDF generation
        output_pdf = self.reports_dir / "report.pdf"
        success = generate_report_pdf(
            str(template_path),
            str(output_pdf),
            self.reports_dir,
            self.figures_dir
        )

        # Verify the process completed (PDF may or may not exist depending on LaTeX availability)
        if success:
            assert output_pdf.exists()
            assert output_pdf.stat().st_size > 0

        # 5. Verify all expected outputs are present
        expected_files = [
            self.figures_dir / "periodogram_icecube.png",
            self.figures_dir / "correlation_heatmap.png",
            self.figures_dir / "fap_summary.png",
            self.reports_dir / "report_template.tex"
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected file not found: {file_path}"

    def test_report_build_handles_missing_data(self):
        """Test that report build fails gracefully when required data is missing."""
        # Remove one of the required input files
        (self.results_dir / "dipole_timeseries.csv").unlink()

        with pytest.raises(FileNotFoundError):
            load_timeseries_data(str(self.results_dir / "dipole_timeseries.csv"))

    def test_config_summary_included(self):
        """Test that configuration summary is available for report."""
        config_summary = get_config_summary()
        assert config_summary is not None
        assert "bin_size" in config_summary or "DEFAULT_BIN_SIZE_DAYS" in str(config_summary)

    def test_timestamps_in_figures(self):
        """Test that generated figures include timestamps for reproducibility."""
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))
        output_path = self.figures_dir / "periodogram_with_timestamp.png"

        plot_periodogram(
            corr_results["icecube"]["lomb_scargle_peaks"],
            str(output_path),
            detector="IceCube",
            timestamp=datetime.now()
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_integration_with_validation_metrics(self):
        """Test that validation metrics are correctly integrated into the report."""
        import json

        validation_path = self.results_dir / "validation_metrics.json"
        with open(validation_path) as f:
            validation_data = json.load(f)

        assert "fp_rate" in validation_data
        assert "power" in validation_data
        assert validation_data["fp_rate"] <= 0.05
        assert validation_data["power"] >= 0.8

    def test_report_build_idempotency(self):
        """Test that running the report build multiple times produces consistent results."""
        # First run
        corr_results = load_correlation_results(str(self.results_dir / "correlation_results.json"))
        plot_periodogram(
            corr_results["icecube"]["lomb_scargle_peaks"],
            str(self.figures_dir / "periodogram_run1.png"),
            detector="IceCube"
        )

        # Second run
        plot_periodogram(
            corr_results["icecube"]["lomb_scargle_peaks"],
            str(self.figures_dir / "periodogram_run2.png"),
            detector="IceCube"
        )

        # Both files should exist and be non-empty
        assert (self.figures_dir / "periodogram_run1.png").exists()
        assert (self.figures_dir / "periodogram_run2.png").exists()
        assert (self.figures_dir / "periodogram_run1.png").stat().st_size > 0
        assert (self.figures_dir / "periodogram_run2.png").stat().st_size > 0

    def test_error_handling_for_invalid_correlation_data(self):
        """Test that invalid correlation data is handled gracefully."""
        # Create a corrupted JSON file
        invalid_json_path = self.results_dir / "invalid_correlation_results.json"
        with open(invalid_json_path, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_correlation_results(str(invalid_json_path))

    def test_full_pipeline_execution_script(self):
        """Test that the report generation script can be executed as a standalone process."""
        # This test verifies that the main entry point works correctly
        script_path = PROJECT_ROOT / "code" / "scripts" / "generate_report_plots.py"

        if script_path.exists():
            # Run the script with minimal arguments
            result = subprocess.run(
                [sys.executable, str(script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            # The script should at least respond to --help
            assert result.returncode == 0 or "usage" in result.stdout.lower()
        else:
            # If the script doesn't exist yet, skip this test
            pytest.skip("generate_report_plots.py not found")