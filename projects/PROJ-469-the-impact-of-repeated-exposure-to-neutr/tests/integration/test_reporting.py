"""
Integration test for report generation (T027).

Validates that the reporting pipeline produces the expected artifacts:
1. A PDF report file exists in the results directory.
2. The PDF file size is within the allowed limit (<= 5 MB).
3. Summary CSV files exist with expected content.
"""
import os
import pytest
from pathlib import Path
import sys

# Add project root to path if running outside standard environment
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config_manager import get_results_path
from logging_config import setup_logging, get_logger

# Constants
MAX_REPORT_SIZE_MB = 5
EXPECTED_REPORT_FILENAME = "report.pdf"
EXPECTED_SUMMARY_FILENAME = "model_summary.csv"
EXPECTED_DIAGNOSTICS_FILENAME = "diagnostics.csv"

logger = get_logger(__name__)


@pytest.fixture(scope="module")
def results_dir():
    """Get the results directory path."""
    return get_results_path()


@pytest.fixture(scope="module")
def report_path(results_dir):
    """Get the expected path to the generated report."""
    return results_dir / EXPECTED_REPORT_FILENAME


@pytest.fixture(scope="module")
def summary_path(results_dir):
    """Get the expected path to the summary CSV."""
    return results_dir / EXPECTED_SUMMARY_FILENAME


@pytest.fixture(scope="module")
def diagnostics_path(results_dir):
    """Get the expected path to the diagnostics CSV."""
    return results_dir / EXPECTED_DIAGNOSTICS_FILENAME


def test_report_file_exists(results_dir):
    """
    Test that the report generation process creates the PDF file.
    
    This test verifies that the reporting pipeline (T028, T030, T031)
    has successfully written the report to disk.
    """
    report_file = results_dir / EXPECTED_REPORT_FILENAME
    assert report_file.exists(), (
        f"Report file '{report_file}' does not exist. "
        "Ensure the reporting pipeline (main.py -> reporting.py) has been executed."
    )
    logger.info(f"Report file found: {report_file}")


def test_report_size_within_limit(report_path):
    """
    Test that the generated PDF report is within the size constraint (<= 5 MB).
    
    This ensures the report is optimized and does not contain excessive
    embedded assets that would bloat the file size.
    """
    if not report_path.exists():
        pytest.skip("Report file does not exist; cannot check size.")
    
    file_size_bytes = report_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    assert file_size_mb <= MAX_REPORT_SIZE_MB, (
        f"Report file size ({file_size_mb:.2f} MB) exceeds limit ({MAX_REPORT_SIZE_MB} MB). "
        "Please optimize images or reduce plot resolution in reporting.py."
    )
    logger.info(f"Report size check passed: {file_size_mb:.2f} MB <= {MAX_REPORT_SIZE_MB} MB")


def test_model_summary_csv_exists(summary_path):
    """
    Test that the model summary CSV file exists.
    
    Verifies that T029 (Generate CSV summary tables) has been executed.
    """
    assert summary_path.exists(), (
        f"Model summary file '{summary_path}' does not exist. "
        "Ensure T029 (summary table generation) has been run."
    )
    logger.info(f"Model summary file found: {summary_path}")


def test_diagnostics_csv_exists(diagnostics_path):
    """
    Test that the diagnostics CSV file exists.
    
    Verifies that imputation diagnostics and model fit stats are saved.
    """
    assert diagnostics_path.exists(), (
        f"Diagnostics file '{diagnostics_path}' does not exist. "
        "Ensure preprocessing and model diagnostics are saved."
    )
    logger.info(f"Diagnostics file found: {diagnostics_path}")


def test_report_content_structure(report_path):
    """
    Optional: Verify the PDF file is not empty and has a valid header.
    
    This is a basic sanity check to ensure the file is a valid PDF
    and not an empty placeholder.
    """
    if not report_path.exists():
        pytest.skip("Report file does not exist; cannot check content.")
    
    with open(report_path, "rb") as f:
        header = f.read(8)
        
    # PDF files start with %PDF
    assert header.startswith(b"%PDF"), (
        f"File '{report_path}' does not appear to be a valid PDF. "
        "Header found: {header}"
    )
    logger.info("Report file has valid PDF header.")
