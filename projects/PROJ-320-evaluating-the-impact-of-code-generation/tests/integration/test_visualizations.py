import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.analysis.visualizations import run_visualization_pipeline
from code.utils.config import get_path
from code.utils.logging import setup_logging


@pytest.mark.integration
def test_histogram_generation():
    """
    Integration test for T030b: Histogram generation.
    
    Asserts that the visualization pipeline successfully generates
    the PDF report containing histograms at the expected path:
    reports/figures/histograms.pdf
    
    This test verifies:
    1. The pipeline executes without raising exceptions.
    2. The output file `reports/figures/histograms.pdf` exists on disk.
    3. The file is non-empty (size > 0 bytes).
    """
    # Setup logging for the test run
    logger = setup_logging("test_histogram_generation")
    
    # Ensure the output directory exists
    output_dir = get_path("reports_figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "histograms.pdf"
    
    # Clean up any existing file to ensure we are testing fresh generation
    if output_file.exists():
        output_file.unlink()
    
    logger.info(f"Starting histogram generation pipeline. Output target: {output_file}")
    
    try:
        # Execute the visualization pipeline
        # This function is expected to load processed metrics and generate the PDF
        run_visualization_pipeline()
        
        # Assertion 1: File must exist
        assert output_file.exists(), (
            f"Histogram generation failed: Output file '{output_file}' was not created. "
            "Ensure data/processed/prs_metrics.csv exists and contains valid data."
        )
        
        # Assertion 2: File must not be empty
        file_size = output_file.stat().st_size
        assert file_size > 0, (
            f"Histogram generation failed: Output file '{output_file}' is empty (0 bytes). "
            "Check if the pipeline encountered an error during plotting."
        )
        
        logger.info(f"Histogram generation successful. File size: {file_size} bytes.")
        
    except Exception as e:
        logger.error(f"Histogram generation pipeline failed with error: {e}")
        raise
    
    finally:
        # Cleanup is optional for integration tests but good practice if we want to keep the workspace clean
        # For this test, we leave the artifact as evidence of success unless the test fails.
        pass