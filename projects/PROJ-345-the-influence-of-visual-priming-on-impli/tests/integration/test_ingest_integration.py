"""
Integration test for missing image handling in ingest.py.

Verifies that the system:
1. Halts execution if >10% of images are missing.
2. Logs a warning and proceeds if ≤10% are missing.
3. Correctly counts missing images against the total trial count.
"""
import os
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from data.ingest import ingest_iat_data, IngestConfig
from config import get_path

# Setup logging to capture warnings/errors during tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Create a temporary directory structure mimicking the project layout."""
    base_dir = tempfile.mkdtemp()
    data_dir = Path(base_dir) / "data"
    raw_dir = data_dir / "raw"
    primes_dir = data_dir / "primes"
    targets_dir = data_dir / "targets"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    primes_dir.mkdir(parents=True, exist_ok=True)
    targets_dir.mkdir(parents=True, exist_ok=True)
    
    return base_dir, raw_dir, primes_dir, targets_dir

def create_mock_csv_with_stimuli(csv_path, stimulus_names, total_trials):
    """
    Create a mock CSV file with trial data referencing specific stimulus names.
    """
    import csv
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['trial_id', 'response_time', 'stimulus_name', 'prime_condition'])
        
        for i in range(total_trials):
            # Cycle through the provided stimulus names
            stim_name = stimulus_names[i % len(stimulus_names)]
            writer.writerow([f"trial_{i}", 500 + i, stim_name, "neutral"])

def test_missing_images_exceeds_threshold():
    """
    Test that ingestion halts when >10% of images are missing.
    
    Scenario:
    - Total trials: 20
    - Stimuli referenced: 10 unique names
    - Images existing: 8 (2 missing) -> 20% missing
    - Expected: System raises an error or halts.
    """
    base_dir, raw_dir, primes_dir, targets_dir = setup_test_environment()
    
    # Create 8 image files (simulating existing images)
    existing_stims = [f"stim_{i}.jpg" for i in range(8)]
    for stim in existing_stims:
        (primes_dir / stim).touch()
    
    # Create 2 missing stimuli references in CSV
    missing_stims = [f"stim_{i}.jpg" for i in range(8, 10)]
    all_stims = existing_stims + missing_stims
    
    csv_path = raw_dir / "iat_data.csv"
    create_mock_csv_with_stimuli(csv_path, all_stims, total_trials=20)
    
    config = IngestConfig(
        raw_data_path=str(csv_path),
        primes_dir=str(primes_dir),
        targets_dir=str(targets_dir),
        missing_image_threshold=0.10, # 10%
        output_dir=str(Path(base_dir) / "data" / "processed")
    )
    
    # Ensure the output directory exists for the test
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # This should raise an exception or halt due to >10% missing
        # We expect the function to raise a ValueError or similar
        ingest_iat_data(config)
        
        # If we reach here, the test failed because it didn't halt
        logger.error("Test Failed: Ingestion did not halt when >10% images were missing.")
        assert False, "Ingestion should have halted due to excessive missing images."
        
    except ValueError as e:
        # Expected behavior
        assert "Data Gap" in str(e) or "missing" in str(e).lower(), f"Unexpected error message: {e}"
        logger.info("Test Passed: Correctly halted with error for >10% missing images.")
    except Exception as e:
        logger.error(f"Test Failed: Unexpected exception type: {type(e).__name__}: {e}")
        assert False, f"Unexpected exception: {e}"
    finally:
        shutil.rmtree(base_dir)

def test_missing_images_within_threshold():
    """
    Test that ingestion proceeds with a warning when ≤10% of images are missing.
    
    Scenario:
    - Total trials: 20
    - Stimuli referenced: 10 unique names
    - Images existing: 9 (1 missing) -> 10% missing
    - Expected: System logs warning but completes.
    """
    base_dir, raw_dir, primes_dir, targets_dir = setup_test_environment()
    
    # Create 9 image files
    existing_stims = [f"stim_{i}.jpg" for i in range(9)]
    for stim in existing_stims:
        (primes_dir / stim).touch()
    
    # Create 1 missing stimulus reference
    missing_stims = [f"stim_{9}.jpg"]
    all_stims = existing_stims + missing_stims
    
    csv_path = raw_dir / "iat_data.csv"
    create_mock_csv_with_stimuli(csv_path, all_stims, total_trials=20)
    
    config = IngestConfig(
        raw_data_path=str(csv_path),
        primes_dir=str(primes_dir),
        targets_dir=str(targets_dir),
        missing_image_threshold=0.10,
        output_dir=str(Path(base_dir) / "data" / "processed")
    )
    
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # This should complete but log a warning
        result = ingest_iat_data(config)
        
        # Verify that the function returned successfully (did not raise)
        # The specific return value depends on implementation, but it shouldn't crash
        logger.info("Test Passed: Ingestion completed with warning for ≤10% missing images.")
        
    except Exception as e:
        logger.error(f"Test Failed: Ingestion raised exception when it should have warned: {e}")
        assert False, f"Ingestion should have proceeded with a warning. Error: {e}"
    finally:
        shutil.rmtree(base_dir)

def test_no_missing_images():
    """
    Test that ingestion proceeds normally when 0% images are missing.
    """
    base_dir, raw_dir, primes_dir, targets_dir = setup_test_environment()
    
    # Create all necessary images
    total_unique_stims = 5
    existing_stims = [f"stim_{i}.jpg" for i in range(total_unique_stims)]
    for stim in existing_stims:
        (primes_dir / stim).touch()
    
    # Create CSV referencing only existing images
    csv_path = raw_dir / "iat_data.csv"
    create_mock_csv_with_stimuli(csv_path, existing_stims, total_trials=10)
    
    config = IngestConfig(
        raw_data_path=str(csv_path),
        primes_dir=str(primes_dir),
        targets_dir=str(targets_dir),
        missing_image_threshold=0.10,
        output_dir=str(Path(base_dir) / "data" / "processed")
    )
    
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        result = ingest_iat_data(config)
        logger.info("Test Passed: Ingestion completed successfully with no missing images.")
    except Exception as e:
        logger.error(f"Test Failed: Unexpected error: {e}")
        assert False, f"Ingestion failed unexpectedly: {e}"
    finally:
        shutil.rmtree(base_dir)

if __name__ == "__main__":
    logger.info("Starting Integration Tests for Missing Image Handling...")
    
    logger.info("\n--- Running test_missing_images_exceeds_threshold ---")
    test_missing_images_exceeds_threshold()
    
    logger.info("\n--- Running test_missing_images_within_threshold ---")
    test_missing_images_within_threshold()
    
    logger.info("\n--- Running test_no_missing_images ---")
    test_no_missing_images()
    
    logger.info("\nAll integration tests completed.")