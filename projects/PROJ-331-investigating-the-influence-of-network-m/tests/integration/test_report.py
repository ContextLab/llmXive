"""
Integration test for PDF generation (US3).
Verifies SC-004: PDF generation completes in <= 2 minutes and file size <= 5MB.
"""
import os
import sys
import time
import json
import pytest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from report import generate_pdf
from config import ensure_dirs

# Constants for the test
TIMEOUT_SECONDS = 120  # 2 minutes
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MOCK_RESULTS_PATH = "data/processed/motif_profiles.json"
MOCK_EFFICIENCY_PATH = "data/processed/global_efficiency.json"
MOCK_RSFC_PATH = "data/processed/rsfc.npy"
OUTPUT_PDF_PATH = "results/test_report.pdf"

# Mock data schema for the test to run without full pipeline data
# In a real CI run, these files would be produced by T027, T015, T039
MOCK_MOTIF_PROFILES = {
    "motifs": [
        {"id": "M1", "z_scores": {"10p": 1.2, "20p": 1.1, "30p": 1.05}, "median_z": 1.1},
        {"id": "M2", "z_scores": {"10p": -0.5, "20p": -0.4, "30p": -0.45}, "median_z": -0.45},
        {"id": "M3", "z_scores": {"10p": 0.0, "20p": 0.0, "30p": 0.0}, "median_z": 0.0},
        {"id": "M4", "z_scores": {"10p": 2.5, "20p": 2.6, "30p": 2.55}, "median_z": 2.55},
    ],
    "thresholds": ["10p", "20p", "30p"]
}

MOCK_EFFICIENCY = {
    "subjects": [
        {"id": "sub-01", "global_efficiency": 0.45, "strength": 120.5},
        {"id": "sub-02", "global_efficiency": 0.42, "strength": 115.2},
        {"id": "sub-03", "global_efficiency": 0.48, "strength": 130.1},
        {"id": "sub-04", "global_efficiency": 0.41, "strength": 110.0},
        {"id": "sub-05", "global_efficiency": 0.46, "strength": 125.3},
    ]
}

def _create_mock_data():
    """Create mock input files required for the report generation."""
    ensure_dirs()
    
    # Ensure data/processed exists
    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)
    
    # Write mock motif profiles
    with open(data_processed / "motif_profiles.json", "w") as f:
        json.dump(MOCK_MOTIF_PROFILES, f)
    
    # Write mock efficiency data
    with open(data_processed / "global_efficiency.json", "w") as f:
        json.dump(MOCK_EFFICIENCY, f)
    
    # Create a dummy rsfc.npy (3 subjects x 100 regions for example)
    import numpy as np
    dummy_rsfc = np.random.rand(5, 100) # 5 subjects, 100 regions
    np.save(data_processed / "rsfc.npy", dummy_rsfc)

def _cleanup_mock_data():
    """Remove mock data files after test."""
    files_to_remove = [
        project_root / "data" / "processed" / "motif_profiles.json",
        project_root / "data" / "processed" / "global_efficiency.json",
        project_root / "data" / "processed" / "rsfc.npy",
        project_root / "results" / "test_report.pdf"
    ]
    for f in files_to_remove:
        if f.exists():
            f.unlink()

@pytest.fixture(scope="function")
def mock_environment():
    """Setup and teardown for mock data."""
    _create_mock_data()
    yield
    _cleanup_mock_data()

def test_pdf_generation_performance(mock_environment):
    """
    Integration test: Verify PDF generation completes in <= 2 minutes 
    and file size <= 5MB (SC-004).
    """
    # Ensure results directory exists
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "test_report.pdf"
    if output_path.exists():
        output_path.unlink()

    start_time = time.time()
    
    # Call the report generation function
    # This function is expected to exist in code/report.py (T035/T037a)
    # It aggregates data from T027, T015, T039 and generates the PDF
    try:
        generate_pdf(output_path=str(output_path))
    except Exception as e:
        pytest.fail(f"PDF generation failed with exception: {e}")

    elapsed_time = time.time() - start_time
    
    # Check 1: Execution time <= 2 minutes
    assert elapsed_time <= TIMEOUT_SECONDS, (
        f"PDF generation took {elapsed_time:.2f} seconds, "
        f"exceeding the limit of {TIMEOUT_SECONDS} seconds."
    )

    # Check 2: File size <= 5MB
    assert output_path.exists(), "Output PDF file was not created."
    file_size = output_path.stat().st_size
    assert file_size <= MAX_FILE_SIZE_BYTES, (
        f"PDF file size is {file_size / (1024*1024):.2f} MB, "
        f"exceeding the limit of {MAX_FILE_SIZE_BYTES / (1024*1024)} MB."
    )

    # Check 3: File is not empty and has content
    assert file_size > 1000, "PDF file is suspiciously small (likely empty or truncated)."

    # Check 4: Verify the mandatory disclaimer string is present (T036)
    # We read the binary content and search for the string (PDFs are binary but text strings are embedded)
    with open(output_path, "rb") as f:
        content = f.read()
        disclaimer = b"These findings are associational only and do not imply causation."
        assert disclaimer in content, "Mandatory disclaimer string not found in PDF."

    print(f"✓ PDF generation passed SC-004 checks: Time={elapsed_time:.2f}s, Size={file_size/1024:.1f}KB")