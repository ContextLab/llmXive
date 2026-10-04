import os
from pathlib import Path

import pytest

# Import the main entry point from the module we just implemented
from src.metrics.generate_validation_report import main as generate_report_main

@pytest.mark.usefixtures("temp_stimuli_dir", "temp_rating_file")
def test_report_generated(tmp_path):
    """
    Run the report generation script and verify that the markdown file
    is created at the expected location.
    """
    # Ensure the working directory is the project root so that relative
    # paths inside the module resolve correctly.
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Execute the report generation
        generate_report_main()

        report_path = Path("data/derived/pilot_validation_report.md")
        assert report_path.is_file(), f"Report file not found at {report_path}"
    finally:
        os.chdir(original_cwd)