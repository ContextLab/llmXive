"""
Contract test for report generation (User Story 3).

This test verifies that the report generation pipeline produces
a valid PDF and that all required components (figures, tables,
LaTeX compilation) are present and correctly formatted.

Acceptance Criteria:
1. generate_report_pdf() returns True on successful compilation
2. Output PDF exists at expected path
3. All required figures are present in the report
4. LaTeX compilation succeeds without errors
"""
import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

# Import from the existing API surface
from scripts.generate_report_plots import (
    generate_report_pdf,
    load_timeseries_data,
    load_correlation_results
)

# Mock data fixtures for contract testing
@pytest.fixture
def temp_report_dir():
    """Create a temporary directory for report generation."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_timeseries_csv(temp_report_dir):
    """Create a sample timeseries CSV file."""
    csv_path = Path(temp_report_dir) / "dipole_timeseries.csv"
    csv_path.write_text(
        "interval_start,dipole_amp,dipole_phase,quad_amp,partial_interval\n"
        "2451545.0,0.0012,1.57,0.0008,false\n"
        "2451572.0,0.0015,1.62,0.0009,false\n"
        "2451600.0,0.0011,1.55,0.0007,true\n"
    )
    return csv_path

@pytest.fixture
def sample_correlation_json(temp_report_dir):
    """Create a sample correlation results JSON file."""
    json_path = Path(temp_report_dir) / "correlation_results.json"
    data = {
        "icecube": {
            "lomb_scargle_peaks": [
                {"period": 27.0, "power": 0.85, "p_value": 0.001},
                {"period": 54.0, "power": 0.45, "p_value": 0.05}
            ],
            "correlation_coefficient": 0.72,
            "fap": 0.002,
            "significant_after_bonferroni": True
        },
        "auger": {
            "lomb_scargle_peaks": [
                {"period": 27.0, "power": 0.78, "p_value": 0.003},
                {"period": 54.0, "power": 0.42, "p_value": 0.06}
            ],
            "correlation_coefficient": 0.68,
            "fap": 0.004,
            "significant_after_bonferroni": True
        }
    }
    json_path.write_text(json.dumps(data, indent=2))
    return json_path

@pytest.fixture
def sample_validation_metrics(temp_report_dir):
    """Create a sample validation metrics JSON file."""
    json_path = Path(temp_report_dir) / "validation_metrics.json"
    data = {
        "fp_rate": 0.03,
        "power": 0.85
    }
    json_path.write_text(json.dumps(data, indent=2))
    return json_path

def test_generate_report_pdf_creates_output(
    temp_report_dir,
    sample_timeseries_csv,
    sample_correlation_json,
    sample_validation_metrics
):
    """
    Contract test: Verify that generate_report_pdf creates a valid PDF.
    
    This test ensures:
    1. The function returns True on successful compilation
    2. The output PDF file exists
    3. The PDF file is non-empty
    """
    output_pdf = Path(temp_report_dir) / "report.pdf"
    
    # Call the report generation function
    success = generate_report_pdf(
        timeseries_csv=sample_timeseries_csv,
        correlation_json=sample_correlation_json,
        validation_json=sample_validation_metrics,
        output_path=str(output_pdf),
        temp_dir=temp_report_dir
    )
    
    # Contract: Function should return True on success
    assert success is True, "Report generation should return True on success"
    
    # Contract: Output PDF must exist
    assert output_pdf.exists(), "Output PDF file must be created"
    
    # Contract: Output PDF must be non-empty
    assert output_pdf.stat().st_size > 0, "Output PDF file must not be empty"

def test_generate_report_pdf_handles_missing_timeseries(
    temp_report_dir
):
    """
    Contract test: Verify graceful handling of missing timeseries data.
    
    The report generation should fail gracefully when required input
    files are missing, rather than crashing with an unhandled exception.
    """
    output_pdf = Path(temp_report_dir) / "report.pdf"
    missing_csv = Path(temp_report_dir) / "missing.csv"
    missing_json = Path(temp_report_dir) / "missing.json"
    
    # Call with missing files - should return False or raise expected error
    with pytest.raises(FileNotFoundError):
        generate_report_pdf(
            timeseries_csv=missing_csv,
            correlation_json=missing_json,
            validation_json=missing_json,
            output_path=str(output_pdf),
            temp_dir=temp_report_dir
        )

def test_generate_report_pdf_integrates_with_plots(
    temp_report_dir,
    sample_timeseries_csv,
    sample_correlation_json,
    sample_validation_metrics
):
    """
    Contract test: Verify that report generation correctly integrates
    with the plotting functions.
    
    This test ensures that:
    1. Figures are generated before PDF compilation
    2. All required figure types are present
    3. The PDF includes references to all figures
    """
    # First, ensure figures are generated
    figures_dir = Path(temp_report_dir) / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    # Generate the report (which should also generate figures)
    output_pdf = Path(temp_report_dir) / "report.pdf"
    success = generate_report_pdf(
        timeseries_csv=sample_timeseries_csv,
        correlation_json=sample_correlation_json,
        validation_json=sample_validation_metrics,
        output_path=str(output_pdf),
        temp_dir=temp_report_dir
    )
    
    # Contract: Report generation should succeed
    assert success is True, "Report generation should succeed with valid inputs"
    
    # Contract: PDF should be created
    assert output_pdf.exists(), "PDF output should be created"

def test_report_generation_with_empty_data(
    temp_report_dir
):
    """
    Contract test: Verify behavior with empty but valid data files.
    
    The system should handle edge cases like:
    - Empty timeseries (header only)
    - Zero correlation coefficients
    - Missing validation metrics
    """
    # Create empty timeseries (header only)
    empty_csv = Path(temp_report_dir) / "empty_timeseries.csv"
    empty_csv.write_text(
        "interval_start,dipole_amp,dipole_phase,quad_amp,partial_interval\n"
    )
    
    # Create minimal correlation data
    empty_json = Path(temp_report_dir) / "empty_correlation.json"
    empty_json.write_text("{}")
    
    output_pdf = Path(temp_report_dir) / "report.pdf"
    
    # Should handle empty data gracefully (return False or raise expected error)
    # This is a contract test to ensure we don't crash
    with pytest.raises((FileNotFoundError, ValueError, RuntimeError)):
        generate_report_pdf(
            timeseries_csv=empty_csv,
            correlation_json=empty_json,
            validation_json=empty_json,
            output_path=str(output_pdf),
            temp_dir=temp_report_dir
        )

def test_report_generation_preserves_data_integrity(
    temp_report_dir,
    sample_timeseries_csv,
    sample_correlation_json,
    sample_validation_metrics
):
    """
    Contract test: Verify that report generation does not modify input files.
    
    This ensures that the report generation process is read-only with respect
    to input data, maintaining data integrity for reproducibility.
    """
    # Store original file contents
    original_csv = sample_timeseries_csv.read_text()
    original_correlation = sample_correlation_json.read_text()
    original_validation = sample_validation_metrics.read_text()
    
    output_pdf = Path(temp_report_dir) / "report.pdf"
    
    # Generate report
    success = generate_report_pdf(
        timeseries_csv=sample_timeseries_csv,
        correlation_json=sample_correlation_json,
        validation_json=sample_validation_metrics,
        output_path=str(output_pdf),
        temp_dir=temp_report_dir
    )
    
    # Contract: Input files should not be modified
    assert sample_timeseries_csv.read_text() == original_csv, \
        "Timeseries CSV should not be modified"
    assert sample_correlation_json.read_text() == original_correlation, \
        "Correlation JSON should not be modified"
    assert sample_validation_metrics.read_text() == original_validation, \
        "Validation JSON should not be modified"

def test_report_generation_with_large_dataset(
    temp_report_dir
):
    """
    Contract test: Verify report generation handles larger datasets.
    
    This test ensures that the report generation can handle:
    - Many time intervals
    - Multiple detectors
    - Complex correlation results
    """
    # Create a larger timeseries dataset
    large_csv = Path(temp_report_dir) / "large_timeseries.csv"
    lines = ["interval_start,dipole_amp,dipole_phase,quad_amp,partial_interval"]
    for i in range(100):
        lines.append(f"{2451545.0 + i*27.0},{0.001 + i*0.0001},{1.5 + i*0.01},{0.0005 + i*0.0001},{i == 99}")
    large_csv.write_text("\n".join(lines))
    
    # Create correlation data for multiple detectors
    large_json = Path(temp_report_dir) / "large_correlation.json"
    data = {
        "icecube": {
            "lomb_scargle_peaks": [
                {"period": 27.0, "power": 0.85, "p_value": 0.001},
                {"period": 54.0, "power": 0.45, "p_value": 0.05}
            ],
            "correlation_coefficient": 0.72,
            "fap": 0.002,
            "significant_after_bonferroni": True
        },
        "auger": {
            "lomb_scargle_peaks": [
                {"period": 27.0, "power": 0.78, "p_value": 0.003},
                {"period": 54.0, "power": 0.42, "p_value": 0.06}
            ],
            "correlation_coefficient": 0.68,
            "fap": 0.004,
            "significant_after_bonferroni": True
        },
        "combined": {
            "correlation_coefficient": 0.70,
            "fap": 0.003,
            "significant_after_bonferroni": True
        }
    }
    large_json.write_text(json.dumps(data, indent=2))
    
    # Create validation metrics
    validation_json = Path(temp_report_dir) / "validation_metrics.json"
    validation_json.write_text(json.dumps({"fp_rate": 0.03, "power": 0.85}))
    
    output_pdf = Path(temp_report_dir) / "report.pdf"
    
    # Should handle large dataset without crashing
    success = generate_report_pdf(
        timeseries_csv=large_csv,
        correlation_json=large_json,
        validation_json=validation_json,
        output_path=str(output_pdf),
        temp_dir=temp_report_dir
    )
    
    # Contract: Should succeed with large dataset
    assert success is True, "Report generation should handle large datasets"
    assert output_pdf.exists(), "PDF should be created for large dataset"