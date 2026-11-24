import pytest
from pathlib import Path
from code.preprocessing.fmriprep_runner import parse_fmriprep_html

def test_parse_fmriprep_html_success(tmp_path):
    """Test that a valid HTML report is recognized."""
    html_file = tmp_path / "report.html"
    html_file.write_text("<html><body><h1>fMRIPrep</h1><table id='motion'>Motion Summary</table></body></html>")
    assert parse_fmriprep_html(html_file) is True

def test_parse_fmriprep_html_failure(tmp_path):
    """Test that an invalid HTML report is rejected."""
    html_file = tmp_path / "report.html"
    html_file.write_text("<html><body>No data here</body></html>")
    assert parse_fmriprep_html(html_file) is False

def test_parse_fmriprep_html_missing(tmp_path):
    """Test that a missing file returns False."""
    assert parse_fmriprep_html(tmp_path / "missing.html") is False