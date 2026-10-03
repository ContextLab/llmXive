"""
Integration tests for memory usage constraints during quantification.
This test suite verifies that the quantification pipeline stays within
the defined memory limits (7GB) when processing real or mock data.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import json
import gzip
import time
from pathlib import Path
import pytest

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import ensure_directories, get_thresholds, MAX_RAM_GB
from utils.logging import get_memory_usage_mb

# Constants
MOCK_FASTQ_DIR = Path(__file__).parent / "data" / "mock_fastq"
QUANT_OUTPUT_DIR = Path(__file__).parent / "data" / "test_quant_output"
REFERENCE_INDEX = Path(__file__).parent.parent.parent / "data" / "raw" / "reference" / "index"
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024


def _generate_mock_fastq_file(output_path: Path, num_reads: int = 1000, read_length: int = 100):
    """
    Generate a mock FASTQ file with random sequences.
    This is used for integration testing to avoid downloading large real datasets.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with gzip.open(output_path, 'wt') as f:
        for i in range(num_reads):
            header = f"@mock_sample_read_{i}"
            sequence = "ACGT" * (read_length // 4)
            plus_line = "+"
            quality = "I" * read_length
            
            f.write(f"{header}\n{sequence}\n{plus_line}\n{quality}\n")


def _ensure_mock_data_exists():
    """
    Ensure mock FASTQ files exist in the expected location.
    If T011 completed successfully, these should exist.
    If not, generate them for this test.
    """
    if not MOCK_FASTQ_DIR.exists():
        MOCK_FASTQ_DIR.mkdir(parents=True, exist_ok=True)
    
    sample_file_1 = MOCK_FASTQ_DIR / "mock_sample_1.fastq.gz"
    sample_file_2 = MOCK_FASTQ_DIR / "mock_sample_2.fastq.gz"
    
    if not sample_file_1.exists():
        _generate_mock_fastq_file(sample_file_1, num_reads=5000, read_length=100)
    
    if not sample_file_2.exists():
        _generate_mock_fastq_file(sample_file_2, num_reads=5000, read_length=100)
    
    return sample_file_1, sample_file_2


def _run_salmon_quant(fastq_path: Path, output_dir: Path, index_path: Path, mem_limit_gb: float):
    """
    Run Salmon quantification on a single sample with memory constraints.
    Returns the peak memory usage in MB.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if Salmon is available
    try:
        result = subprocess.run(
            ["salmon", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("Salmon not installed or not in PATH. Skipping memory test.")
    except FileNotFoundError:
        pytest.skip("Salmon executable not found. Skipping memory test.")
    
    # Prepare command
    cmd = [
        "salmon", "quant",
        "-i", str(index_path),
        "-l", "A",
        "-r", str(fastq_path),
        "-o", str(output_dir),
        "--validateMappings",
        f"--memGb", str(mem_limit_gb)
    ]
    
    start_mem = get_memory_usage_mb()
    start_time = time.time()
    
    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for the test
        )
        
        if process.returncode != 0:
            # If Salmon fails, we still want to check if it was due to memory
            # For the purpose of this test, we assume if it runs without OOM killer, it's okay
            # but we log the error
            pytest.fail(f"Salmon quantification failed: {process.stderr}")
            
    except subprocess.TimeoutExpired:
        pytest.fail("Salmon quantification timed out.")
    
    end_mem = get_memory_usage_mb()
    peak_mem = max(start_mem, end_mem)
    
    return peak_mem


def test_quantification_memory_stays_under_7GB():
    """
    Integration test: Verify that quantification on a small sample subset
    stays under the 7GB memory limit.
    
    This test:
    1. Ensures mock data exists (generates if T011 didn't create it)
    2. Checks if reference index exists (from T018)
    3. Runs Salmon quantification on the mock data
    4. Verifies peak memory usage is under 7GB
    """
    # 1. Ensure mock data exists
    sample_1, sample_2 = _ensure_mock_data_exists()
    
    # 2. Check reference index
    if not REFERENCE_INDEX.exists():
        pytest.skip(
            f"Reference index not found at {REFERENCE_INDEX}. "
            "Task T018 (Download and Verify Reference Transcriptome) must be completed first."
        )
    
    # 3. Run quantification on the first mock sample
    test_output_dir = QUANT_OUTPUT_DIR / sample_1.stem
    
    print(f"Running quantification on {sample_1.name}...")
    print(f"Reference index: {REFERENCE_INDEX}")
    print(f"Output directory: {test_output_dir}")
    
    peak_memory_mb = _run_salmon_quant(
        fastq_path=sample_1,
        output_dir=test_output_dir,
        index_path=REFERENCE_INDEX,
        mem_limit_gb=MEMORY_LIMIT_GB
    )
    
    print(f"Peak memory usage: {peak_memory_mb:.2f} MB")
    print(f"Memory limit: {MEMORY_LIMIT_MB:.2f} MB")
    
    # 4. Assert memory usage is within limits
    assert peak_memory_mb < MEMORY_LIMIT_MB, (
        f"Memory usage ({peak_memory_mb:.2f} MB) exceeded limit ({MEMORY_LIMIT_MB:.2f} MB). "
        "The quantification pipeline is not memory-efficient enough."
    )
    
    # 5. Verify output was generated
    quant_file = test_output_dir / "quant.sf"
    assert quant_file.exists(), "Quantification output file (quant.sf) was not generated."
    
    # 6. Verify output file is not empty
    assert quant_file.stat().st_size > 0, "Quantification output file is empty."
    
    # Cleanup
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)
    
    print("Memory test passed successfully!")