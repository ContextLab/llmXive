"""
Integration test for the full preprocessing pipeline on 1 subject.

This test verifies the end-to-end flow:
1. Download a single subject's data from OpenNeuro (ds000224).
2. Run the preprocessing pipeline (motion correction, normalization, filtering).
3. Validate that output files exist and contain non-zero data.
4. Verify resource monitoring logs are updated.

Prerequisites:
- OpenNeuro CLI or wget availability (handled by download.py logic).
- FSL/AFNI tools availability (checked by dependency_check).
- Real data access from the internet.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from config import get_dataset_ids, get_sample_limit
from models import Subject
from utils import ResourceMonitor
from download import download_subject_data
from preprocess import run_preprocessing_pipeline


def test_full_preprocessing_pipeline_single_subject():
    """
    Integration test: Download 1 subject, preprocess, and verify outputs.
    """
    # Setup: Create a temporary directory for this test run
    # to avoid polluting the main data directory during CI
    test_output_dir = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
    data_raw_dir = test_output_dir / "raw"
    data_processed_dir = test_output_dir / "processed"
    data_raw_dir.mkdir(parents=True)
    data_processed_dir.mkdir(parents=True)

    # Configuration
    dataset_ids = get_dataset_ids()
    # Prioritize ds000224 as per task T013/T014 logic
    target_dataset = dataset_ids[0] if dataset_ids else "ds000224"
    sample_limit = get_sample_limit()

    # We only need 1 subject for this integration test
    # In a real run, this would iterate, but for T012 we verify the pipeline works on 1.
    # We will attempt to download the first available subject (sub-01 usually).
    subject_id = "sub-01"
    output_file_name = f"{subject_id}_preprocessed_bold.nii.gz"
    output_path = data_processed_dir / output_file_name

    # Initialize Resource Monitor for this test
    # We write to a specific JSON file to verify the mechanism works
    resource_log_path = test_output_dir / "resource_profile_test.json"
    monitor = ResourceMonitor(log_file=resource_log_path)
    monitor.start()

    try:
        # Step 1: Download Data
        # We pass the specific subject ID to limit download scope if the downloader supports it,
        # or we download the dataset and filter.
        # Assuming download_subject_data handles the logic to fetch the specific subject.
        print(f"Starting download for {subject_id} from {target_dataset}...")
        downloaded_path = download_subject_data(
            dataset_id=target_dataset,
            subject_id=subject_id,
            output_dir=data_raw_dir,
            limit=1
        )

        if not downloaded_path:
            # If download fails (e.g., network issue or subject missing), fail the test
            assert False, f"Failed to download data for {subject_id} from {target_dataset}"

        # Step 2: Preprocess Data
        print(f"Starting preprocessing for {subject_id}...")
        success = run_preprocessing_pipeline(
            input_path=downloaded_path,
            output_dir=data_processed_dir,
            subject_id=subject_id
        )

        assert success, "Preprocessing pipeline returned failure status"
        assert output_path.exists(), f"Expected output file {output_path} was not created"

        # Step 3: Validate Output File
        # Check file size > 0
        file_size = output_path.stat().st_size
        assert file_size > 0, f"Output file {output_path} is empty"

        # Step 4: Validate Resource Monitor
        # Check that the resource log was written and contains data
        assert resource_log_path.exists(), "Resource monitor log file was not created"
        with open(resource_log_path, 'r') as f:
            resource_data = json.load(f)
        
        assert "subjects" in resource_data, "Resource log missing 'subjects' key"
        assert subject_id in resource_data["subjects"], f"Subject {subject_id} not in resource log"
        
        # Verify at least one metric was recorded
        subject_stats = resource_data["subjects"][subject_id]
        assert "peak_ram_mb" in subject_stats, "Resource log missing peak_ram_mb"
        assert subject_stats["peak_ram_mb"] > 0, "Recorded RAM usage is zero or negative"

        print("Integration test PASSED: Download, Preprocessing, and Resource Monitoring verified.")

    finally:
        # Cleanup: Remove the temporary directory
        if test_output_dir.exists():
            shutil.rmtree(test_output_dir)
        monitor.stop()
        print("Test cleanup complete.")


if __name__ == "__main__":
    # Allow running directly for debugging
    test_full_preprocessing_pipeline_single_subject()
    print("Direct execution successful.")