"""
Unit tests for fMRIPrep HTML Report Parser (qc_parser.py).
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.preprocessing.qc_parser import (
    QCParserError,
    parse_fmriprep_html,
    find_fmriprep_reports,
    run_qc_parsing
)

# Fixtures
@pytest.fixture
def temp_report_file(tmp_path):
    """Create a temporary fMRIPrep-like HTML report."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Report</title></head>
    <body>
        <h1>fMRIPrep Report: sub-01</h1>
        <div class="qc-metrics">
            <p>Framewise Displacement: 0.45 mm</p>
            <p>Max Displacement: 1.2 mm</p>
            <p>Mean Translation: 0.3 mm</p>
            <p>Mean Rotation: 0.1 deg</p>
            <p>SNR: 15.2</p>
            <p>tSNR: 85.6</p>
        </div>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Mean FD</td><td>0.45 mm</td></tr>
            <tr><td>Max FD</td><td>1.2 mm</td></tr>
            <tr><td>Mean Translation</td><td>0.3 mm</td></tr>
            <tr><td>tSNR</td><td>85.6</td></tr>
        </table>
    </body>
    </html>
    """
    report_path = tmp_path / "sub-01_report.html"
    report_path.write_text(html_content)
    return report_path

@pytest.fixture
def temp_missing_report_file(tmp_path):
    """Create a temporary report with missing metrics."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Report</title></head>
    <body>
        <h1>fMRIPrep Report: sub-02</h1>
        <p>Some random text without metrics.</p>
    </body>
    </html>
    """
    report_path = tmp_path / "sub-02_report.html"
    report_path.write_text(html_content)
    return report_path

class TestParseFMRIPrepHtml:
    def test_parse_valid_report(self, temp_report_file):
        """Test parsing a valid report with all expected metrics."""
        result = parse_fmriprep_html(temp_report_file)

        assert result["parsing_status"] == "success"
        assert result["subject_id"] == "sub-01"
        assert result["report_path"] == str(temp_report_file)

        # Check motion metrics
        assert result["motion"]["mean_fd"] is not None
        assert abs(result["motion"]["mean_fd"] - 0.45) < 0.01
        assert result["motion"]["max_fd"] is not None
        assert abs(result["motion"]["max_fd"] - 1.2) < 0.01
        assert result["motion"]["mean_translation"] is not None
        assert abs(result["motion"]["mean_translation"] - 0.3) < 0.01

        # Check SNR metrics
        assert result["snr"]["snr"] is not None
        assert abs(result["snr"]["snr"] - 15.2) < 0.1
        assert result["snr"]["tSNR"] is not None
        assert abs(result["snr"]["tSNR"] - 85.6) < 0.1

    def test_parse_missing_report(self, temp_missing_report_file):
        """Test parsing a report with missing metrics."""
        result = parse_fmriprep_html(temp_missing_report_file)

        assert result["parsing_status"] == "partial"
        assert len(result["warnings"]) > 0
        assert "Could not extract standard QC metrics" in result["warnings"][0]
        assert result["motion"]["mean_fd"] is None
        assert result["snr"]["tSNR"] is None

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        fake_path = Path("/tmp/nonexistent_report.html")
        with pytest.raises(QCParserError) as exc_info:
            parse_fmriprep_html(fake_path)
        assert "not found" in str(exc_info.value).lower()

    def test_parse_invalid_html(self, tmp_path):
        """Test parsing a file with invalid HTML."""
        bad_html_path = tmp_path / "bad.html"
        bad_html_path.write_text("<html><body>Unclosed tags")
        # BeautifulSoup is lenient, but we can test if it handles it without crashing
        result = parse_fmriprep_html(bad_html_path)
        assert "report_path" in result

class TestRunQcParsing:
    def test_run_qc_parsing_creates_json(self, tmp_path):
        """Test that run_qc_parsing creates a JSON summary file."""
        # Create a mock report
        report_dir = tmp_path / "sub-01" / "figures"
        report_dir.mkdir(parents=True)
        report_file = report_dir / "sub-01_report.html"
        report_file.write_text(
            "<html><body><p>Mean FD: 0.5 mm</p><p>tSNR: 100</p></body></html>"
        )

        output_path = tmp_path / "qc_output.json"

        results = run_qc_parsing(
            data_dir=str(tmp_path),
            output_json_path=str(output_path)
        )

        assert len(results) == 1
        assert output_path.exists()

        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        assert len(saved_data) == 1
        assert saved_data[0]["motion"]["mean_fd"] is not None

    def test_run_qc_parsing_no_reports(self, tmp_path):
        """Test run_qc_parsing when no reports are found."""
        # Create an empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        results = run_qc_parsing(
            data_dir=str(empty_dir),
            output_json_path=str(tmp_path / "empty_qc.json")
        )

        assert results == []