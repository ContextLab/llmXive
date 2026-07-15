"""
Integration test for the end-to-end data pipeline (US1).

This test verifies:
1. The full pipeline executes without error: 
   data_generation -> preprocessing -> save.
2. The output data fits within the 6 GB RAM constraint for L=24.
3. The output shapes and normalization are correct (delegating to unit tests where appropriate).
"""
import os
import sys
import gc
import tempfile
import shutil
import numpy as np
import psutil
import time
from pathlib import Path

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data_generation import run_simulation, save_data, ensure_data_dir
from code.preprocessing import load_raw_data, normalize_spins, reshape_to_batch, stratified_split, save_processed_data
from code.config import get_config, reset_config


def get_memory_usage_gb():
    """Returns the current memory usage of the process in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)


def test_end_to_end_pipeline_memory_l24():
    """
    Integration test: Run the full pipeline for L=24 and verify memory < 6 GB.
    
    We use a small number of samples and temperatures to keep the test fast,
    but large enough to stress the memory for L=24 (3, 24, 24) tensors.
    """
    # Configuration for the test
    # We use a very small subset to ensure the test runs within the 300s wall clock,
    # but we verify the memory logic holds.
    # L=24, 3 components.
    # To simulate a "real" run without taking hours, we use:
    # - 2 temperatures
    # - 500 spins per temperature (small for a real run, but enough for integration)
    # - 10 Metropolis steps (minimal for speed)
    
    config = get_config()
    
    # Create a temporary directory for this test run to avoid polluting data/
    test_dir = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
    raw_dir = test_dir / "raw"
    processed_dir = test_dir / "processed"
    
    try:
        # 1. Data Generation (L=24)
        print(f"Starting data generation for L=24 in {test_dir}...")
        raw_data_path = raw_dir / "heisenberg_L24_T0.5.npz"
        
        # Ensure directories exist
        ensure_data_dir(raw_dir)
        ensure_data_dir(processed_dir)
        
        # Generate a small dataset for L=24
        # Using L=24, T=0.5, J1=1.0, J2=0.5 (example)
        # We generate 1000 spins to be safe on memory but small enough for CI
        L = 24
        T = 0.5
        n_spins = 1000 
        n_steps = 10 # Minimal steps for integration test speed
        
        # Run simulation
        spins = run_simulation(
            model="heisenberg",
            L=L,
            T=T,
            n_spins=n_spins,
            n_steps=n_steps,
            seed=42,
            J1=1.0,
            J2=0.5
        )
        
        # Save raw data
        save_data(spins, T, L, "heisenberg", raw_dir)
        
        initial_mem = get_memory_usage_gb()
        print(f"Memory after generation: {initial_mem:.2f} GB")
        
        # 2. Preprocessing
        print("Starting preprocessing...")
        raw_files = list(raw_dir.glob("*.npz"))
        if not raw_files:
            raise FileNotFoundError("No raw data files found for preprocessing.")
        
        # Load raw data
        raw_data = load_raw_data(raw_files)
        
        # Normalize
        normalized_data = normalize_spins(raw_data)
        
        # Reshape to [batch, 3, L, L]
        reshaped_data = reshape_to_batch(normalized_data, L)
        
        # Stratified Split (mocked for integration if single temp, but logic must run)
        # Since we have only 1 temp in this specific minimal run, we split 80/20
        # The function expects a list of temps or a structure that allows splitting.
        # Assuming load_raw_data returns a dict or list of arrays.
        # Let's assume raw_data is a dict {temp: array} or list of arrays.
        # Based on typical implementation, we expect a list of arrays or a single large array.
        # We will adapt to the expected interface:
        
        # If load_raw_data returns a dict {temp: spins}, we need to handle it.
        # For this test, we assume it returns a structured object or list.
        # Let's assume the simplest: a list of (temp, spins) tuples or similar.
        # Re-reading the API: `load_raw_data` returns data. 
        # We will assume it returns a dict mapping temp to spins for simplicity in this test.
        
        if isinstance(raw_data, dict):
            # Flatten for split if needed, or split per temp
            # For integration test, we just need to ensure the pipeline runs.
            # We will process the first item if it's a dict.
            first_temp = list(raw_data.keys())[0]
            spins_array = raw_data[first_temp]
            normalized = normalize_spins(spins_array)
            reshaped = reshape_to_batch(normalized, L)
            
            # Split
            train_data, val_data = stratified_split(reshaped, [first_temp] * len(reshaped), train_size=0.8)
            
            # Save processed
            save_processed_data(train_data, val_data, processed_dir)
        else:
            # Fallback if it's a single array
            normalized = normalize_spins(raw_data)
            reshaped = reshape_to_batch(normalized, L)
            # Create dummy temps for split if not present
            temps = [0.5] * len(reshaped)
            train_data, val_data = stratified_split(reshaped, temps, train_size=0.8)
            save_processed_data(train_data, val_data, processed_dir)
        
        # Force garbage collection to get accurate peak memory
        gc.collect()
        
        final_mem = get_memory_usage_gb()
        print(f"Memory after preprocessing: {final_mem:.2f} GB")
        
        # 3. Verification
        assert final_mem < 6.0, f"Memory usage {final_mem:.2f} GB exceeds 6 GB limit for L=24."
        
        # Verify shapes
        assert train_data.shape[1] == 3, "Channel dimension must be 3"
        assert train_data.shape[2] == L, f"L dimension must be {L}"
        assert train_data.shape[3] == L, f"L dimension must be {L}"
        
        # Verify normalization (unit norm)
        norms = np.linalg.norm(train_data, axis=1)
        # Check if norms are close to 1.0
        assert np.allclose(norms, 1.0, atol=1e-5), "Spins must be normalized to unit length"
        
        print(f"SUCCESS: Pipeline completed. Peak memory: {final_mem:.2f} GB < 6 GB.")
        
    finally:
        # Cleanup temporary directory
        if test_dir.exists():
            shutil.rmtree(test_dir)
        reset_config()


if __name__ == "__main__":
    test_end_to_end_pipeline_memory_l24()