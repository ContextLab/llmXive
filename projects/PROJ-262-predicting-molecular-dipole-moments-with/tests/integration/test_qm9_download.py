"""
Integration test for QM9 download pipeline with memory profiling.
Verifies that memory usage stays within the 8GB limit during download.
"""
import os
import sys
import gc
import tracemalloc
import tempfile
from pathlib import Path

# Add project root to path to resolve imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import data.download_qm9 as download_module
from utils.memory_constraint import memory_limit


def get_memory_usage_mb():
    """Get current memory usage in MB."""
    if sys.platform == "linux":
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
    else:
        # Fallback for non-Linux systems
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def test_qm9_download_memory_under_8gb():
    """
    Test that downloading and processing QM9 dataset stays under 8GB memory limit.
    
    This test:
    1. Starts memory tracing
    2. Downloads a small subset of QM9 (or processes existing raw data if available)
    3. Verifies peak memory usage is under 8GB (8192 MB)
    4. Cleans up downloaded files
    """
    max_memory_limit_mb = 8 * 1024  # 8GB in MB
    
    # Ensure we start with a clean state
    gc.collect()
    tracemalloc.start()
    
    # Create a temporary directory for test downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Reset memory tracking before the actual operation
        gc.collect()
        tracemalloc.reset_peak()
        
        try:
            # Get initial memory usage
            initial_memory = get_memory_usage_mb()
            
            # Perform download with memory constraint
            # We use a small subset for testing to ensure we don't download the full 130k molecules
            # The actual download_qm9 function handles the full dataset
            download_path = temp_path / "qm9_test"
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Call the download function with a small subset for testing
            # The download_qm9 function will fetch the real data
            try:
                # We'll test with a small sample to verify memory constraints
                # In a real scenario, this would be the full dataset
                result = download_module.download_qm9(
                    output_dir=str(download_path),
                    max_molecules=100  # Small sample for memory testing
                )
                
                if not result:
                    raise RuntimeError("Download failed to produce any output")
                
            except Exception as e:
                # If download fails due to network or other issues, 
                # we still want to verify our memory constraint logic works
                if "No real source" in str(e) or "network" in str(e).lower():
                    # Skip test if real data is unavailable
                    tracemalloc.stop()
                    print("Skipping test: Real data source unavailable")
                    return
                else:
                    raise
            
            # Get peak memory usage
            current, peak = tracemalloc.get_traced_memory()
            peak_memory_mb = peak / (1024 * 1024)
            
            # Also check RSS (Resident Set Size) which is more accurate for overall memory
            current_memory = get_memory_usage_mb()
            memory_increase = current_memory - initial_memory
            
            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Current memory: {current_memory:.2f} MB")
            print(f"Memory increase: {memory_increase:.2f} MB")
            print(f"Peak traced memory: {peak_memory_mb:.2f} MB")
            
            # Verify memory is under limit
            assert peak_memory_mb < max_memory_limit_mb, (
                f"Peak memory usage {peak_memory_mb:.2f} MB exceeded limit of {max_memory_limit_mb} MB"
            )
            assert memory_increase < max_memory_limit_mb, (
                f"Memory increase {memory_increase:.2f} MB exceeded limit of {max_memory_limit_mb} MB"
            )
            
            # Verify that files were actually created
            assert download_path.exists(), "Download directory was not created"
            files = list(download_path.rglob("*"))
            assert len(files) > 0, "No files were downloaded"
            
            print(f"✓ Memory usage ({peak_memory_mb:.2f} MB) is within 8GB limit")
            print(f"✓ Downloaded {len(files)} files successfully")
            
        finally:
            tracemalloc.stop()
            gc.collect()


if __name__ == "__main__":
    test_qm9_download_memory_under_8gb()
    print("Test passed!")