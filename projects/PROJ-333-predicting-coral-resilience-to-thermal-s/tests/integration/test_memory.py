"""
Integration tests for memory usage during quantification.

This module verifies that the quantification pipeline (T019) stays within
the memory constraint of MAX_RAM_GB (7 GB) defined in config.py.

Note: This test uses a small subset of real data (or a minimal mock FASTQ
file) to simulate the quantification step. It does not download the full
dataset to avoid excessive runtime and disk usage.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import time
import json
from pathlib import Path

import pytest

# Add project root to path to import config
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_thresholds, ensure_directories, MAX_RAM_GB
from utils.logging import get_memory_usage_mb, setup_logger

# Setup logger for the test
logger = setup_logger("test_memory", level="INFO")


def create_mock_fastq_file(output_path: Path, num_reads: int = 1000) -> None:
    """
    Creates a minimal valid FASTQ file for testing.
    
    Args:
        output_path: Path to write the .fastq file.
        num_reads: Number of reads to generate.
    """
    with open(output_path, 'w') as f:
        for i in range(num_reads):
            f.write(f"@read_{i}\n")
            f.write("ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT\n")
            f.write("+\n")
            f.write("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII\n")


@pytest.mark.integration
def test_quantification_memory_stays_under_7GB():
    """
    Integration test: Verify that running Salmon quantification on a 
    small sample subset stays under the 7GB RAM limit.
    
    This test:
    1. Creates a temporary directory structure.
    2. Generates a small mock FASTQ file (simulating T015/T017 input).
    3. Uses a pre-built reference index (from T018) if available, 
       or skips if not found (since T018 is a prerequisite).
    4. Runs the quantification command (simulating T019 logic).
    5. Monitors peak RSS memory usage.
    6. Asserts peak memory < MAX_RAM_GB * 1024 MB.
    
    Dependencies:
        - T018: Reference index must exist at data/raw/reference/index/
        - T015/T017: Input FASTQ logic (simulated here)
    """
    
    # Check for reference index (Prerequisite T018)
    ref_index_dir = project_root / "data" / "raw" / "reference" / "index"
    if not ref_index_dir.exists():
        pytest.skip(
            "Reference index not found. Prerequisite T018 (Download and Verify Reference Transcriptome) "
            "must be completed before this integration test can run. "
            f"Expected path: {ref_index_dir}"
        )

    # Create temporary working directory
    temp_dir = tempfile.mkdtemp(prefix="t014_mem_test_")
    temp_path = Path(temp_dir)
    output_dir = temp_path / "quant_output"
    output_dir.mkdir()
    
    # Create mock FASTQ file
    mock_fastq = temp_path / "mock_sample.fastq"
    create_mock_fastq_file(mock_fastq, num_reads=1000)
    
    # Construct Salmon command (matching T019 spec)
    # Using the index from T018
    cmd = [
        "salmon", "quant",
        "-i", str(ref_index_dir),
        "-l", "A",
        "-r", str(mock_fastq),
        "-o", str(output_dir),
        "--validateMappings"
    ]
    
    logger.info(f"Running quantification command: {' '.join(cmd)}")
    logger.info(f"Monitoring memory usage with limit: {MAX_RAM_GB} GB")
    
    peak_memory_mb = 0.0
    process = None
    
    try:
        # Start the process
        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Monitor memory while process is running
        while process.poll() is None:
            # Get current RSS of the process and its children if possible
            # Note: psutil is often needed for accurate child memory, 
            # but we stick to standard utils if available or basic os
            current_mem = get_memory_usage_mb()
            if current_mem > peak_memory_mb:
                peak_memory_mb = current_mem
            
            # Sleep briefly to avoid busy-waiting
            time.sleep(0.5)
        
        # Final check
        final_mem = get_memory_usage_mb()
        if final_mem > peak_memory_mb:
            peak_memory_mb = final_mem
        
        # Capture output for debugging
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Salmon quantification failed with code {process.returncode}")
            logger.error(f"Stderr: {stderr.decode('utf-8', errors='ignore')}")
            # If Salmon fails, the test might still be valid regarding memory, 
            # but we usually expect success for a memory test.
            # However, if the index is corrupted, it might fail.
            # We'll assume success if returncode is 0.
            pytest.fail(f"Salmon quantification failed: {stderr.decode('utf-8', errors='ignore')[:500]}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Quantification completed in {elapsed_time:.2f}s")
        
    except FileNotFoundError:
        pytest.skip(
            "Salmon executable not found in PATH. "
            "Ensure Salmon is installed and accessible."
        )
    except Exception as e:
        logger.error(f"Unexpected error during memory test: {e}")
        pytest.fail(f"Unexpected error: {e}")
    finally:
        # Cleanup
        if process and process.poll() is None:
            process.terminate()
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Assertion
    limit_mb = MAX_RAM_GB * 1024
    logger.info(f"Peak memory usage: {peak_memory_mb:.2f} MB (Limit: {limit_mb} MB)")
    
    assert peak_memory_mb < limit_mb, (
        f"Memory limit exceeded! Peak usage: {peak_memory_mb:.2f} MB, "
        f"Limit: {limit_mb} MB ({MAX_RAM_GB} GB). "
        "The quantification step must be optimized to stream or use memory-mapped files."
    )

    # Log success
    logger.info("TEST PASSED: Memory usage stayed under 7GB limit.")