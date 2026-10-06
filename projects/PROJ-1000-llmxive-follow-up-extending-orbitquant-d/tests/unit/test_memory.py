"""
Unit test to verify memory usage of the MS-COCO streaming download script.

This test verifies that `code/data/download_coco.py` runs with memory usage
below a specified threshold (2GB) by monitoring the process during execution.
"""
import os
import sys
import subprocess
import time
import gc
from pathlib import Path
import tempfile
import json

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    pytest.skip("psutil not installed, skipping memory test", allow_module_level=True)

from config import Config

MEMORY_LIMIT_MB = 2048  # 2GB limit

def get_process_memory_mb(pid: int) -> float:
    """Get current RSS memory usage of a process in MB."""
    process = psutil.Process(pid)
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def test_streaming_memory_usage():
    """
    Test that downloading MS-COCO with streaming=True keeps memory under 2GB.
    
    This runs the download script as a subprocess and monitors its memory usage.
    """
    if not HAS_PSUTIL:
        pytest.skip("psutil required for memory test")

    config = Config()
    script_path = project_root / "code" / "data" / "download_coco.py"
    
    if not script_path.exists():
        pytest.fail(f"Script not found at {script_path}")

    # Create a temporary directory for output to avoid interfering with real data
    # Note: The script uses Config paths, so we rely on the script's internal logic
    # but we can verify the process behavior.
    
    # Start the process
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root)
    )

    max_memory_mb = 0
    pid = process.pid
    start_time = time.time()
    timeout = 300  # 5 minutes timeout

    try:
        while process.poll() is None:
            # Check timeout
            if time.time() - start_time > timeout:
                process.kill()
                pytest.fail("Process timed out after 5 minutes")
            
            try:
                current_mem = get_process_memory_mb(pid)
                if current_mem > max_memory_mb:
                    max_memory_mb = current_mem
                    
                # Log every 10 seconds to avoid too many calls
                if int(time.time() - start_time) % 10 == 0:
                    print(f"Current memory usage: {current_mem:.2f} MB")
                    
            except psutil.NoSuchProcess:
                # Process might have exited
                break
            
            time.sleep(1)  # Poll every second

        # Final check
        if process.returncode != 0:
            stdout, stderr = process.communicate()
            pytest.fail(f"Process failed with code {process.returncode}\nStderr: {stderr.decode()}\nStdout: {stdout.decode()}")

    finally:
        if process.poll() is None:
            process.kill()
            process.wait()

    print(f"Maximum memory usage observed: {max_memory_mb:.2f} MB")
    print(f"Memory limit: {MEMORY_LIMIT_MB} MB")

    assert max_memory_mb < MEMORY_LIMIT_MB, (
        f"Memory usage exceeded limit: {max_memory_mb:.2f} MB > {MEMORY_LIMIT_MB} MB. "
        "Ensure streaming=True is used in datasets.load_dataset()."
    )

def test_streaming_output_exists():
    """
    Verify that the streaming script produces the expected output file.
    """
    config = Config()
    output_csv = config.data_processed_path / "coco_prompts_streaming.csv"
    meta_file = config.data_raw_path / "coco_2017_val_streaming_meta.json"

    # Run the script if output doesn't exist (or force re-run for testing)
    # In a real CI/CD, this would be part of the pipeline setup
    if not output_csv.exists():
        script_path = project_root / "code" / "data" / "download_coco.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.fail(f"Failed to run download_coco.py: {result.stderr}")

    assert output_csv.exists(), f"Output CSV {output_csv} does not exist"
    assert meta_file.exists(), f"Metadata file {meta_file} does not exist"

    # Verify CSV content
    with open(output_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "CSV file is empty"
        assert "id" in reader.fieldnames, "Missing 'id' column"
        assert "caption" in reader.fieldnames, "Missing 'caption' column"

    # Verify metadata
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["mode"] == "streaming", "Metadata does not indicate streaming mode"
        assert meta["num_samples"] > 0, "No samples recorded in metadata"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
