"""
Integration test for the full ingestion pipeline on a single subject.
Verifies that the pipeline successfully downloads, processes, and outputs
the complexity metrics CSV file.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path to allow imports from 'code'
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import DATA_RAW_DIR, DATA_INTERIM_DIR, DATASET_ID
from code.ingestion import download_dataset
from code.complexity import batch_process_complexity
from code.setup_dirs import create_all_directories


class TestIngestionPipeline:
    """Integration tests for the data ingestion and complexity calculation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup after test."""
        # Ensure directories exist
        create_all_directories()
        
        yield

        # Cleanup: Remove generated interim results if they were created during the test
        # We do not delete the raw data if it was downloaded, to respect "Real Data" constraints
        output_path = DATA_INTERIM_DIR / "complexity_metrics.csv"
        if output_path.exists():
            output_path.unlink()
            log_file = DATA_INTERIM_DIR / "ingestion.log"
            if log_file.exists():
                log_file.unlink()

    def test_pipeline_outputs_csv(self):
        """
        Asserts that the full pipeline (download + complexity calculation)
        results in the creation of data/interim/complexity_metrics.csv.
        
        This test verifies the integration of:
        1. Downloading the dataset (or verifying its presence)
        2. Processing images for complexity
        3. Writing the output CSV
        """
        output_path = DATA_INTERIM_DIR / "complexity_metrics.csv"
        
        # Ensure the output file does not exist before the test
        if output_path.exists():
            output_path.unlink()
        
        # Assert it doesn't exist (pre-condition)
        assert not output_path.exists(), "Output CSV should not exist before pipeline run."

        # 1. Attempt to download/verify dataset
        try:
            download_dataset(DATASET_ID)
        except Exception as e:
            # If download fails, check if data exists; if not, skip/fail
            if not (DATA_RAW_DIR / DATASET_ID).exists():
                pytest.skip(f"Dataset {DATASET_ID} could not be downloaded or found. Skipping integration test.")
            # If it exists, we continue to processing

        # 2. Run the complexity batch processing
        # This function is expected to find the stimuli in data/raw and write to data/interim
        try:
            batch_process_complexity()
        except Exception as e:
            # If processing fails, the test should fail explicitly
            pytest.fail(f"Complexity processing failed: {e}")

        # 3. Assert the output file exists
        assert os.path.exists(output_path), "Pipeline failed to create complexity_metrics.csv"
        
        # 4. Verify the file is not empty and has content
        assert len(str(output_path.read_bytes())) > 0, "complexity_metrics.csv is empty"
        
        # 5. Verify basic structure (header check)
        with open(output_path, 'r') as f:
            header = f.readline().strip()
            expected_columns = ["frame_id", "timestamp", "entropy", "fractal_dim", "hrf_convolved"]
            
            # Check if all expected columns are in the header
            for col in expected_columns:
                assert col in header, f"Missing column '{col}' in CSV header. Found: {header}"

        # If we reach here, the integration test passed
        assert True
