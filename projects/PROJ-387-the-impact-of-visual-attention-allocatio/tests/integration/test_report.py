import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from reporting.generate_report import (
    load_lmm_summary_csv,
    load_correction_results_json,
    generate_report_content,
    main
)
from utils.config import get_project_root
from utils.directories import ensure_directory


class TestReportCompleteness:
    """Integration test for report generation completeness (T035).

    This test verifies that the report generation pipeline:
    1. Successfully loads LMM summary CSV and correction results JSON
    2. Generates a complete markdown report
    3. Includes all required sections: coefficients, corrected p-values, associational disclaimer
    4. Writes the report to the expected output path
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up test environment and clean up after."""
        self.project_root = get_project_root()
        self.output_dir = self.project_root / "output" / "results"
        ensure_directory(self.output_dir)
        
        # Store original files if they exist
        self.lmm_csv_path = self.project_root / "output" / "results" / "lmm_summary.csv"
        self.correction_json_path = self.project_root / "output" / "results" / "correction_results.json"
        self.report_path = self.project_root / "output" / "results" / "final_report.md"
        
        self.original_lmm_csv = None
        self.original_correction_json = None
        self.original_report = None

        if self.lmm_csv_path.exists():
            self.original_lmm_csv = self.lmm_csv_path.read_text()
        if self.correction_json_path.exists():
            self.original_correction_json = self.correction_json_path.read_text()
        if self.report_path.exists():
            self.original_report = self.report_path.read_text()

        yield

        # Restore original files
        if self.original_lmm_csv is not None:
            self.lmm_csv_path.write_text(self.original_lmm_csv)
        elif self.lmm_csv_path.exists():
            self.lmm_csv_path.unlink()

        if self.original_correction_json is not None:
            self.correction_json_path.write_text(self.original_correction_json)
        elif self.correction_json_path.exists():
            self.correction_json_path.unlink()

        if self.original_report is not None:
            self.report_path.write_text(self.original_report)
        elif self.report_path.exists():
            self.report_path.unlink()

    def test_report_completeness(self):
        """Test that the report generation produces a complete, valid report.

        This test:
        1. Creates mock LMM summary CSV and correction results JSON files
        2. Runs the report generation
        3. Verifies the report exists and contains all required sections
        4. Verifies the associational disclaimer is present
        """
        # Create mock LMM summary CSV
        mock_lmm_csv = """metric,valence,coef,p_raw
        fixation_duration,positive,0.25,0.03
        fixation_duration,negative,0.15,0.08
        saccade_amplitude,positive,0.18,0.04
        saccade_amplitude,negative,0.12,0.12
        gaze_distribution,positive,0.22,0.02
        gaze_distribution,negative,0.08,0.15
        """
        self.lmm_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.lmm_csv_path.write_text(mock_lmm_csv)

        # Create mock correction results JSON
        mock_correction_json = {
            "method": "bonferroni",
            "n_tests": 6,
            "results": [
                {"metric": "fixation_duration", "valence": "positive", "p_raw": 0.03, "p_corrected": 0.18},
                {"metric": "fixation_duration", "valence": "negative", "p_raw": 0.08, "p_corrected": 0.48},
                {"metric": "saccade_amplitude", "valence": "positive", "p_raw": 0.04, "p_corrected": 0.24},
                {"metric": "saccade_amplitude", "valence": "negative", "p_raw": 0.12, "p_corrected": 0.72},
                {"metric": "gaze_distribution", "valence": "positive", "p_raw": 0.02, "p_corrected": 0.12},
                {"metric": "gaze_distribution", "valence": "negative", "p_raw": 0.15, "p_corrected": 0.90}
            ],
            "association_label": "associational"
        }
        self.correction_json_path.write_text(json.dumps(mock_correction_json, indent=2))

        # Run report generation
        main()

        # Assert report was created
        assert self.report_path.exists(), "Report file was not created"

        report_content = self.report_path.read_text()

        # Verify required sections exist
        assert "# Final Analysis Report" in report_content, "Report missing title"
        assert "## Linear Mixed-Effects Model Results" in report_content, "Report missing LMM section"
        assert "## Multiple-Comparison Correction Results" in report_content, "Report missing correction section"

        # Verify data content is present
        assert "fixation_duration" in report_content, "Report missing metric data"
        assert "positive" in report_content, "Report missing valence data"
        assert "0.25" in report_content, "Report missing coefficient values"

        # Verify associational disclaimer is present (FR-005)
        assert "associational" in report_content.lower(), "Report missing associational disclaimer"
        assert "causal" not in report_content.lower() or "not causal" in report_content.lower(), \
            "Report contains inappropriate causal language"

        # Verify the report structure is complete
        assert len(report_content) > 500, "Report appears to be incomplete or truncated"

    def test_report_handles_missing_files(self):
        """Test that report generation fails gracefully when input files are missing."""
        # Remove input files if they exist
        if self.lmm_csv_path.exists():
            self.lmm_csv_path.unlink()
        if self.correction_json_path.exists():
            self.correction_json_path.unlink()

        # Attempt to generate report - should fail or handle missing files
        # The main function should either raise an appropriate error or log a clear message
        try:
            main()
            # If it doesn't raise, check if it handled the error gracefully
            assert not self.report_path.exists() or "Error" in self.report_path.read_text(), \
                "Report should not be generated without input files"
        except (FileNotFoundError, ValueError) as e:
            # Expected behavior: clear error about missing files
            assert "lmm_summary" in str(e).lower() or "correction" in str(e).lower(), \
                f"Error message should mention missing input files: {e}"

    def test_report_includes_all_valence_categories(self):
        """Test that the report includes results for all valence categories present in the data."""
        # Create mock data with multiple valence categories
        mock_lmm_csv = """metric,valence,coef,p_raw
        fixation_duration,positive,0.25,0.03
        fixation_duration,negative,0.15,0.08
        fixation_duration,neutral,0.10,0.15
        saccade_amplitude,positive,0.18,0.04
        saccade_amplitude,negative,0.12,0.12
        saccade_amplitude,neutral,0.08,0.20
        """
        self.lmm_csv_path.write_text(mock_lmm_csv)

        mock_correction_json = {
            "method": "bonferroni",
            "n_tests": 6,
            "results": [
                {"metric": "fixation_duration", "valence": "positive", "p_raw": 0.03, "p_corrected": 0.18},
                {"metric": "fixation_duration", "valence": "negative", "p_raw": 0.08, "p_corrected": 0.48},
                {"metric": "fixation_duration", "valence": "neutral", "p_raw": 0.15, "p_corrected": 0.90},
                {"metric": "saccade_amplitude", "valence": "positive", "p_raw": 0.04, "p_corrected": 0.24},
                {"metric": "saccade_amplitude", "valence": "negative", "p_raw": 0.12, "p_corrected": 0.72},
                {"metric": "saccade_amplitude", "valence": "neutral", "p_raw": 0.20, "p_corrected": 1.20}
            ],
            "association_label": "associational"
        }
        self.correction_json_path.write_text(json.dumps(mock_correction_json, indent=2))

        main()

        report_content = self.report_path.read_text()

        # Verify all valence categories are mentioned
        assert "positive" in report_content, "Report missing positive valence category"
        assert "negative" in report_content, "Report missing negative valence category"
        assert "neutral" in report_content, "Report missing neutral valence category"