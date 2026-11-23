"""
Integration test for the full download-quantize-noise pipeline.

This test verifies the end-to-end flow:
1. Downloads a subset of the LIBERO dataset (N=50 episodes).
2. Quantizes the data to discrete state vectors.
3. Injects Gaussian noise.
4. Validates the output file size and data integrity (no NaNs).

Output: data/processed/test_subset.json
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import numpy as np

from data.download_libero import download_libero_subset
from data.quantize import quantize_dataset
from data.noise import inject_noise
from data.schema import QuantizationLevel, validate_state_vector_consistency
from utils.logging import get_logger, DataFetchError, QuantizationError
from config import DATA_DIR, SUBSET_SIZE

logger = get_logger(__name__)

# Constants for this test
TEST_OUTPUT_DIR = DATA_DIR / "processed"
TEST_OUTPUT_FILE = TEST_OUTPUT_DIR / "test_subset.json"
MAX_FILE_SIZE_MB = 100
EXPECTED_EPISODES = 50  # N=50 as per task spec

def run_pipeline_test():
    """
    Executes the full pipeline and asserts constraints.
    """
    # Ensure output directory exists
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download
    logger.info(f"Downloading LIBERO subset (N={EXPECTED_EPISODES})...")
    try:
        hdf5_path = download_libero_subset(num_episodes=EXPECTED_EPISODES)
    except DataFetchError as e:
        logger.error(f"Failed to download data: {e}")
        raise

    if not os.path.exists(hdf5_path):
        raise FileNotFoundError(f"Downloaded file not found at {hdf5_path}")

    # 2. Quantize
    logger.info("Quantizing dataset...")
    try:
        # Using 'low' (4-bit) for this test to ensure small file size
        quantized_data = quantize_dataset(hdf5_path, level=QuantizationLevel.LOW)
    except QuantizationError as e:
        logger.error(f"Quantization failed: {e}")
        raise

    # 3. Inject Noise
    logger.info("Injecting noise...")
    noisy_data = inject_noise(quantized_data, std_dev=0.5)

    # 4. Save to JSON
    logger.info(f"Saving output to {TEST_OUTPUT_FILE}...")
    with open(TEST_OUTPUT_FILE, 'w') as f:
        json.dump(noisy_data, f)

    # 5. Assertions
    assert_file_size_check()
    assert_no_nan_values()
    assert_schema_validity()

    logger.info("All integration tests passed.")

def assert_file_size_check():
    """Assert output file is < 100MB."""
    file_size_bytes = os.path.getsize(TEST_OUTPUT_FILE)
    file_size_mb = file_size_bytes / (1024 * 1024)
    logger.info(f"Output file size: {file_size_mb:.2f} MB")

    if file_size_mb >= MAX_FILE_SIZE_MB:
        raise AssertionError(
            f"Output file size ({file_size_mb:.2f} MB) exceeds limit ({MAX_FILE_SIZE_MB} MB)"
        )

def assert_no_nan_values():
    """Assert no NaN values exist in the JSON data."""
    with open(TEST_OUTPUT_FILE, 'r') as f:
        data = json.load(f)

    # Traverse the structure to find floats
    def check_for_nan(obj, path="root"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check_for_nan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_for_nan(item, f"{path}[{i}]")
        elif isinstance(obj, float):
            if np.isnan(obj):
                raise ValueError(f"NaN value found at {path}")

    check_for_nan(data)
    logger.info("No NaN values found in output data.")

def assert_schema_validity():
    """Assert the data structure matches the expected schema."""
    with open(TEST_OUTPUT_FILE, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Root data must be a list of episodes")

    if len(data) != EXPECTED_EPISODES:
        raise ValueError(f"Expected {EXPECTED_EPISODES} episodes, got {len(data)}")

    # Validate first episode structure roughly
    first_ep = data[0]
    if "states" not in first_ep:
        raise ValueError("Episode missing 'states' key")

    # Check that state vectors are lists of integers (4-bit)
    for state in first_ep["states"]:
        for val in state:
            if not isinstance(val, int):
                raise ValueError(f"State value {val} is not an integer")
            if not (0 <= val <= 15):
                raise ValueError(f"State value {val} out of 4-bit range [0, 15]")

    logger.info("Schema validity check passed.")

def main():
    """Entry point for the integration test."""
    try:
        run_pipeline_test()
        print("SUCCESS: Integration test passed.")
        return 0
    except Exception as e:
        print(f"FAILURE: Integration test failed with error: {e}")
        logger.exception("Test execution failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())