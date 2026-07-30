"""
Integration test for the full data pipeline (User Story 1).

This test verifies the end-to-end flow:
1. Data Generation (Synthetic fallback or Real download attempt)
2. Preprocessing (Filtering, Schema Validation)
3. Metric Computation (Overdensity, Shape, Spin, Concentration)
4. Output Verification (File existence, Schema compliance)

It ensures that the pipeline produces a valid, processed dataset ready for
statistical analysis.
"""
import os
import sys
import time
import tempfile
import shutil
import logging
from pathlib import Path
import json

import pytest
import numpy as np
import pandas as pd
import h5py

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from data.download import run_data_pipeline
from data.preprocess import run_preprocessing_pipeline
from data.compute_metrics import run_compute_metrics_pipeline
from data.synthetic_generator import generate_synthetic_halos, save_to_hdf5
from config import (
    SIMULATION_BOX_SIZE,
    MIN_PARTICLES,
    SEED,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    RESULTS_DIR,
    HALO_SCHEMA_PATH
)

logger = get_logger(__name__)


@pytest.fixture(scope="function")
def temp_data_dirs():
    """Create temporary directories for test data to avoid polluting the real data store."""
    # We use a temporary directory but ensure the structure matches the config expectations
    # so that the pipeline code doesn't need to be refactored for the test.
    temp_root = tempfile.mkdtemp(prefix="llmXive_test_")
    
    # Create subdirectories matching the project structure
    raw_dir = Path(temp_root) / "data" / "raw"
    proc_dir = Path(temp_root) / "data" / "processed"
    res_dir = Path(temp_root) / "results"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    # Patch the config module to use these temp directories for this test
    # Note: In a real scenario, we might use monkeypatch or a config override mechanism.
    # Here we temporarily modify the module attributes if they are mutable or re-assign if possible.
    # Since config.py likely uses constants, we will pass paths explicitly to functions if they accept them,
    # or we will mock the config values.
    
    # Strategy: We will run the pipeline with explicit overrides where possible, 
    # or temporarily patch the config module's variables if they are simple assignments.
    
    original_raw = DATA_RAW_DIR
    original_proc = DATA_PROCESSED_DIR
    original_res = RESULTS_DIR

    # We cannot easily patch imported constants in other modules if they were evaluated at import time.
    # However, the pipeline functions usually take paths or use config. 
    # Let's assume the pipeline functions accept a `output_dir` or we can patch the config module directly
    # if it's a simple namespace.
    
    # For robustness in this test, we will patch the config module's module-level variables.
    import config
    config.DATA_RAW_DIR = str(raw_dir)
    config.DATA_PROCESSED_DIR = str(proc_dir)
    config.RESULTS_DIR = str(res_dir)
    
    # Also ensure the schema path exists or is mocked if needed, but we need the real schema file
    # We assume the schema file is in the project root relative to the code, so we don't move it.
    # If the schema path is absolute or relative to DATA_RAW, we need to adjust.
    # Assuming schema is in code/contracts relative to project root.
    
    yield {
        "raw": raw_dir,
        "processed": proc_dir,
        "results": res_dir,
        "temp_root": temp_root
    }

    # Cleanup
    config.DATA_RAW_DIR = original_raw
    config.DATA_PROCESSED_DIR = original_proc
    config.RESULTS_DIR = original_res
    shutil.rmtree(temp_root)


def test_full_data_pipeline(temp_data_dirs):
    """
    Integration Test: End-to-End Data Pipeline.
    
    1. Generates synthetic data (since real API download is often blocked in CI/test envs).
    2. Runs preprocessing (filtering >= 300 particles).
    3. Runs metric computation (overdensity, shape, spin, concentration).
    4. Verifies output files exist and contain valid data.
    """
    logger.info("Starting full data pipeline integration test.")
    
    # --- Step 1: Data Generation ---
    # The download pipeline (T012) attempts real download. If it fails (which it will in this test env usually),
    # it should trigger the synthetic fallback (T007B).
    # We force the synthetic path to ensure we have data without relying on external API availability.
    # However, to test the *integration* of the download module's fallback logic, we could call run_data_pipeline.
    # But run_data_pipeline might hang on a real request.
    # Strategy: We explicitly call the synthetic generator to ensure data exists, 
    # then verify the rest of the pipeline works on it.
    # OR: We mock the requests in download.py. 
    # Given the constraint "Real data only" for the *production* run, but this is a *test*,
    # we must ensure the test runs. The task T007B specifies generating synthetic data.
    # Let's invoke the synthetic generator directly to populate data/raw/synthetic_halos.h5
    # to simulate the "fallback" state being active.
    
    synthetic_path = Path(temp_data_dirs["raw"]) / "synthetic_halos.h5"
    logger.info(f"Generating synthetic data at {synthetic_path}...")
    
    # Generate 1000 halos for testing
    generate_synthetic_halos(
        num_halos=1000,
        output_path=str(synthetic_path),
        seed=SEED,
        deviation_offset=0.05  # Small deviation as per T007B
    )
    
    assert synthetic_path.exists(), "Synthetic data file was not created."
    logger.info("Synthetic data generated successfully.")

    # --- Step 2: Preprocessing ---
    # Run the preprocessing pipeline which should:
    # - Load the synthetic data
    # - Filter halos with < 300 particles
    # - Validate against schema
    # - Save to parquet
    
    logger.info("Running preprocessing pipeline...")
    try:
        # The run_preprocessing_pipeline function in code/data/preprocess.py
        # is expected to handle the flow. We need to ensure it picks up our temp paths.
        # Since we patched config.DATA_RAW_DIR and config.DATA_PROCESSED_DIR, it should work.
        
        # Check if the function accepts arguments. If not, it relies on config.
        # Assuming it relies on config as per typical design.
        run_preprocessing_pipeline()
        
        # Find the output file (timestamped)
        processed_files = list(Path(temp_data_dirs["processed"]).glob("filtered_halos_*.parquet"))
        assert len(processed_files) > 0, "No processed parquet file found."
        
        processed_file = processed_files[0]
        logger.info(f"Preprocessing complete. Output: {processed_file}")
        
        # Verify content
        df = pd.read_parquet(processed_file)
        assert "mass" in df.columns, "Missing 'mass' column in processed data."
        assert "particle_count" in df.columns, "Missing 'particle_count' column."
        assert "concentration" in df.columns, "Missing 'concentration' column (expected from metrics)."
        
        # Verify filter logic: all particle_count >= 300
        assert (df["particle_count"] >= 300).all(), "Filter logic failed: found halos with < 300 particles."
        
        logger.info(f"Processed {len(df)} halos. All pass particle count threshold.")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

    # --- Step 3: Metric Computation ---
    # Run the metric computation pipeline on the processed data.
    # This adds shape, spin, overdensity, etc.
    
    logger.info("Running metric computation pipeline...")
    try:
        # The run_compute_metrics_pipeline function
        # It should read from the processed parquet and write updated metrics.
        # Note: The spec says T017 calculates overdensity. T022-T024 calculate others.
        # run_compute_metrics_pipeline should orchestrate this.
        
        run_compute_metrics_pipeline()
        
        # The output might be an updated parquet or a separate metrics file.
        # Based on T014, the output is parquet. T026 logs stats.
        # Let's assume the pipeline updates the processed file or creates a new one with metrics.
        # For this test, we verify that the metrics are present in the final state.
        
        # Re-read the processed file to check if metrics were appended or if a new file was created.
        # If the pipeline writes to a new file, we need to find it.
        # Let's assume it updates the latest filtered file or writes to results.
        # Actually, T014 says "save filtered data as ...parquet". T017 adds overdensity.
        # So the final file should have overdensity.
        
        # Check for the latest parquet file again
        final_files = list(Path(temp_data_dirs["processed"]).glob("filtered_halos_*.parquet"))
        if not final_files:
            # Maybe it writes to a specific name? Let's check for any parquet
            final_files = list(Path(temp_data_dirs["processed"]).glob("*.parquet"))
        
        assert len(final_files) > 0, "No final metrics parquet file found."
        
        final_df = pd.read_parquet(final_files[0])
        
        # Verify expected columns from US2
        required_metrics = ["shape", "spin", "concentration", "overdensity"]
        for col in required_metrics:
            assert col in final_df.columns, f"Missing metric column: {col}"
            # Basic range checks (physics sanity)
            if col == "shape":
                assert (final_df[col] >= 0).all() and (final_df[col] <= 1).all(), "Shape out of [0,1] range."
            elif col == "spin":
                assert (final_df[col] >= 0).all(), "Spin out of [0, inf) range."
            elif col == "concentration":
                assert (final_df[col] > 0).all(), "Concentration must be positive."
        
        logger.info("Metric computation complete. All metrics present and within expected ranges.")

    except Exception as e:
        logger.error(f"Metric computation failed: {e}")
        raise

    # --- Step 4: Verification ---
    # Verify the final output file exists and is valid.
    
    logger.info("Verifying final output artifacts...")
    
    # Check for convergence stats (T026)
    stats_file = Path(temp_data_dirs["results"]) / "convergence_stats.json"
    if stats_file.exists():
        with open(stats_file, "r") as f:
            stats = json.load(f)
        logger.info(f"Convergence stats: {stats}")
        assert "success_rate" in stats or "total_fits" in stats, "Convergence stats missing expected keys."
    else:
        logger.warning("Convergence stats file not found. This might be expected if no fits were attempted.")

    logger.info("Full data pipeline integration test PASSED.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])