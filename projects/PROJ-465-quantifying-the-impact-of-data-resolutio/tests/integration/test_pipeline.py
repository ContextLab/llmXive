"""
Integration test for full downsampling + inference pipeline on GW150914.

This test verifies the end-to-end flow:
1. Download/Load real strain data for GW150914 (or use cached raw data if available).
2. Apply resolution transforms (downsampling + quantization) via code/data/transform.py.
3. Run Bayesian inference via code/inference/run_bilby.py.
4. Verify that posterior files are generated and valid.

Prerequisites:
- GW150914 data must be available (downloaded by T013 or present in data/raw/).
- Dependencies (bilby, gwpy, dynesty) must be installed.
"""
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pytest

# Project imports
from code.config import DATA_DIR, RESULTS_DIR, ensure_directories
from code.utils.seeds import set_global_seed
from code.utils.logging_config import setup_logging, get_derivation_logger
from code.data.transform import generate_all_resolutions, apply_resolution_transforms
from code.inference.run_bilby import run_inference
from code.data.models import ResolutionConfig, PosteriorDistribution

# Configure logging for the test
logger = get_derivation_logger("integration_test_pipeline")

# Constants for GW150914
EVENT_NAME = "GW150914"
# Standard GPS time for GW150914
EVENT_GPS = 1126259462.0
DURATION = 4.0  # seconds
SAMPLING_RATE_ORIGINAL = 16384  # Hz (standard GWOSC rate for this event)
TARGET_SAMPLE_RATES = [4096, 2048, 1024]
BIT_DEPTHS = [16, 32]

def _get_or_fetch_event_data() -> Dict[str, Any]:
    """
    Attempts to load existing raw data or fetches it.
    In a real CI environment, this might rely on a pre-downloaded fixture.
    Here, we attempt to use GWOSC via gwpy if raw data is missing.
    """
    raw_dir = DATA_DIR / "raw"
    event_file = raw_dir / f"{EVENT_NAME}_strain.hdf5"

    if event_file.exists():
        logger.info(f"Found existing raw data at {event_file}")
        return {"path": str(event_file), "source": "local"}

    # If not found, we rely on the download module (T013) to fetch it.
    # Since T013 is a prerequisite, we assume it's implemented.
    # We call the download logic here to ensure data exists for this test.
    try:
        from code.data.download import download_strain_data, check_data_availability
        
        # Check availability first
        if not check_data_availability(EVENT_NAME):
            raise RuntimeError(f"Data for {EVENT_NAME} is not available in GWOSC catalogs.")
        
        # Download
        logger.info(f"Downloading strain data for {EVENT_NAME} from GWOSC...")
        download_strain_data(EVENT_NAME, EVENT_GPS, DURATION, raw_dir)
        
        if event_file.exists():
            logger.info(f"Successfully downloaded data to {event_file}")
            return {"path": str(event_file), "source": "gwosc"}
        else:
            raise FileNotFoundError(f"Download failed: {event_file} not found.")
    except Exception as e:
        logger.error(f"Failed to fetch or find data: {e}")
        raise

def _run_downsampling_pipeline(data_path: str, output_dir: Path) -> Dict[str, Path]:
    """
    Runs the downsampling and quantization pipeline.
    Returns a dictionary mapping resolution config hash to the output file path.
    """
    logger.info("Starting downsampling pipeline...")
    
    # Load data (simplified loading for integration test context)
    # In a full pipeline, this would use the models and utils from data module
    from gwpy.timeseries import TimeSeries
    ts = TimeSeries.read(data_path, format='hdf5') # Assumes standard format

    # Generate all resolution configurations
    resolutions = generate_all_resolutions(
        target_sample_rates=TARGET_SAMPLE_RATES,
        bit_depths=BIT_DEPTHS
    )

    output_paths = {}

    for res_config in resolutions:
        logger.info(f"Processing resolution: {res_config.sample_rate} Hz, {res_config.bit_depth}-bit")
        
        # Apply transforms
        # This calls the implementation in code/data/transform.py
        processed_data = apply_resolution_transforms(
            ts, 
            res_config.sample_rate, 
            res_config.bit_depth
        )
        
        # Save processed data
        out_file = output_dir / f"{EVENT_NAME}_res_{res_config.sample_rate}_bit_{res_config.bit_depth}.hdf5"
        processed_data.write(str(out_file), format='hdf5')
        output_paths[res_config] = out_file
        
        logger.info(f"Saved processed data to {out_file}")

    return output_paths

def _run_inference_pipeline(processed_files: Dict[Any, Path], output_dir: Path):
    """
    Runs the bilby inference pipeline on each processed file.
    """
    logger.info("Starting inference pipeline...")
    
    # Set seed for reproducibility
    set_global_seed(42)

    results = {}

    for res_config, data_path in processed_files.items():
        logger.info(f"Running inference for {res_config.sample_rate} Hz, {res_config.bit_depth}-bit...")
        
        # Run inference
        # This calls the implementation in code/inference/run_bilby.py
        posterior_file, metadata = run_inference(
            strain_file=str(data_path),
            event_name=EVENT_NAME,
            gps_time=EVENT_GPS,
            duration=DURATION,
            sample_rate=res_config.sample_rate,
            resolution_config=res_config,
            output_dir=output_dir
        )

        if posterior_file and posterior_file.exists():
            results[res_config] = posterior_file
            logger.info(f"Inference complete. Posterior saved to {posterior_file}")
        else:
            logger.warning(f"Inference did not produce a posterior file for {res_config}")

    return results

@pytest.mark.integration
def test_full_pipeline_gw150914():
    """
    Integration test:
    1. Ensure GW150914 data exists (fetch if needed).
    2. Downsample and quantize.
    3. Run bilby inference.
    4. Assert that posterior files exist and contain valid data.
    """
    # Setup temporary directory for this test run to avoid cluttering data/
    # However, the spec requires artifacts in data/derived/. We will use a temp dir
    # but verify the logic works, then copy to the real location if needed.
    # For this test, we use a temp dir to ensure isolation, but the code paths
    # must match the production code which writes to data/derived/ and results/posteriors/.
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        processed_dir = tmp_path / "processed"
        posteriors_dir = tmp_path / "posteriors"
        processed_dir.mkdir()
        posteriors_dir.mkdir()

        # 1. Get Data
        try:
            data_info = _get_or_fetch_event_data()
            data_path = data_info["path"]
        except Exception as e:
            pytest.fail(f"Failed to obtain GW150914 data: {e}")

        # 2. Downsampling
        try:
            processed_files = _run_downsampling_pipeline(data_path, processed_dir)
            assert len(processed_files) > 0, "No files were processed."
        except Exception as e:
            pytest.fail(f"Downsampling pipeline failed: {e}")

        # 3. Inference
        try:
            posterior_files = _run_inference_pipeline(processed_files, posteriors_dir)
        except Exception as e:
            pytest.fail(f"Inference pipeline failed: {e}")

        # 4. Verification
        assert len(posterior_files) > 0, "Inference produced no posterior files."
        
        for res_config, p_file in posterior_files.items():
            assert p_file.exists(), f"Posterior file missing: {p_file}"
            
            # Basic validation: Check if file is not empty and contains expected keys
            # bilby posterior files are typically JSON or HDF5. 
            # We assume bilby saves to JSON by default in this context or we check the extension.
            if p_file.suffix == '.json':
                import json
                with open(p_file, 'r') as f:
                    data = json.load(f)
                    assert 'samples' in data or 'posterior' in data, "Posterior file missing 'samples' or 'posterior' key."
            elif p_file.suffix == '.hdf5':
                import h5py
                with h5py.File(p_file, 'r') as f:
                    assert 'posterior' in f or 'samples' in f, "Posterior file missing 'posterior' or 'samples' group."
            else:
                # Fallback: check file size
                assert p_file.stat().st_size > 0, f"Posterior file is empty: {p_file}"

    logger.info("Integration test passed: Full pipeline executed successfully.")

if __name__ == "__main__":
    # Allow running directly
    setup_logging(level=logging.INFO)
    ensure_directories()
    test_full_pipeline_gw150914()
    print("Integration test completed successfully.")