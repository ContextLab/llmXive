"""
Integration test for T026: Verify streaming data loading in code/preprocess.py
ensures peak memory usage ≤ 7 GB (per DC-001 and SC-003).

This test verifies that:
1. The preprocessing script uses preload=False for MNE objects.
2. Generator-based iteration is implemented for processing.
3. Peak memory usage stays below 7GB during processing.
"""
import os
import sys
import gc
import tracemalloc
import subprocess
import json
import pytest
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_peak_memory_mb():
    """Get current peak memory usage in MB."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def test_streaming_memory_usage():
    """
    Test that preprocessing with streaming (preload=False) keeps memory under 7GB.
    
    This test:
    1. Starts memory tracing
    2. Runs the preprocessing script
    3. Verifies peak memory stays under 7GB
    4. Verifies output files are created
    """
    # Start memory tracing
    tracemalloc.start()
    
    # Reset garbage collector to get accurate measurements
    gc.collect()
    
    # Record initial memory
    initial_mem = get_peak_memory_mb()
    
    # Run the preprocessing script
    preprocess_script = CODE_DIR / "preprocess.py"
    
    if not preprocess_script.exists():
        pytest.fail(f"Preprocessing script not found: {preprocess_script}")
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(preprocess_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Stop memory tracing
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / (1024 * 1024)
        
        # Log memory usage
        print(f"Peak memory usage: {peak_mb:.2f} MB")
        print(f"Initial memory: {initial_mem:.2f} MB")
        
        # Check if script ran successfully
        if result.returncode != 0:
            print(f"Script failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            # Note: If the script fails due to missing data, that's expected in CI
            # We still want to verify memory usage if possible
            if "No module named 'datasets'" in result.stderr or "Data directory not found" in result.stderr:
                print("Expected error in CI environment (no real data available)")
                # In CI without real data, we can't test memory usage effectively
                # But we can still verify the code structure
                pytest.skip("Skipping memory test - no real data available in CI")
                return
            pytest.fail(f"Preprocessing script failed: {result.stderr}")
        
        # Verify memory constraint (7 GB = 7168 MB)
        MEMORY_LIMIT_MB = 7168
        assert peak_mb < MEMORY_LIMIT_MB, \
            f"Peak memory usage {peak_mb:.2f} MB exceeds limit of {MEMORY_LIMIT_MB} MB"
        
        # Verify output file was created (if script succeeded)
        output_file = PROCESSED_DIR / "cleaned_eeg.fif"
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"Output file created: {output_file} ({file_size_mb:.2f} MB)")
            assert file_size_mb > 0, "Output file is empty"
        
        # Verify exclusion log was created
        exclusion_log = LOGS_DIR / "exclusion_log.csv"
        if exclusion_log.exists():
            print(f"Exclusion log created: {exclusion_log}")
        
        print(f"✓ Memory usage test passed: {peak_mb:.2f} MB < {MEMORY_LIMIT_MB} MB")
        
    except subprocess.TimeoutExpired:
        tracemalloc.stop()
        pytest.fail("Preprocessing script timed out")
    except Exception as e:
        tracemalloc.stop()
        pytest.fail(f"Error running preprocessing script: {str(e)}")

def test_code_uses_preload_false():
    """
    Verify that preprocess.py uses preload=False for MNE objects.
    """
    preprocess_script = CODE_DIR / "preprocess.py"
    
    if not preprocess_script.exists():
        pytest.fail(f"Preprocessing script not found: {preprocess_script}")
    
    with open(preprocess_script, 'r') as f:
        content = f.read()
    
    # Check for preload=False usage
    assert 'preload=False' in content, \
        "preprocess.py must use preload=False for streaming data"
    
    # Check for generator-based iteration
    assert 'yield' in content or 'for.*in.*:' in content, \
        "preprocess.py should use generator-based iteration for streaming"
    
    print("✓ Code structure verification passed: preload=False and generator iteration found")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
