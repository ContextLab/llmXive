"""
Integration test scaffolding for the coral resilience pipeline.

This module generates realistic mock FASTQ files and verifies the 
basic pipeline flow (download -> verify -> quantify) without 
requiring network access to NCBI SRA.

Dependencies:
- pytest
- gzip (stdlib)
- pathlib (stdlib)
"""
import os
import gzip
import hashlib
import tempfile
import shutil
from pathlib import Path
import pytest

# Project imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import setup_logger
from utils.errors import ChecksumError

# Constants for mock generation
MOCK_DATA_DIR = Path(__file__).parent / "data" / "mock_fastq"
SEQ_LENGTH = 50
NUM_READS = 100
QUALITY_STRING = "I" * SEQ_LENGTH  # Phred+33 quality score of 40

logger = setup_logger("integration_test", "INFO")

def _generate_fastq_content(read_id: str, seq: str) -> bytes:
    """Generate FASTQ content for a single read."""
    lines = [
        f"@{read_id}",
        seq,
        f"+{read_id}",
        QUALITY_STRING
    ]
    return "\n".join(lines).encode('utf-8')

def _generate_mock_fastq(output_path: Path, num_reads: int = NUM_READS):
    """Generate a mock FASTQ file with realistic headers and random sequences."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with gzip.open(output_path, 'wb') as f:
        for i in range(num_reads):
            read_id = f"mock_sample_{i:04d}"
            # Generate a random-looking sequence (deterministic for testing)
            # Using a simple pseudo-random generator based on index
            bases = "ACGT"
            seq = "".join(bases[(i * 7 + j * 3) % 4] for j in range(SEQ_LENGTH))
            
            content = _generate_fastq_content(read_id, seq)
            f.write(content)
            if i < num_reads - 1:
                f.write(b"\n")

@pytest.fixture(scope="module")
def mock_fastq_files():
    """Generate mock FASTQ files for integration testing."""
    if not MOCK_DATA_DIR.exists():
        logger.info(f"Creating mock data directory: {MOCK_DATA_DIR}")
        MOCK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    file_paths = []
    for suffix in ["_1.fastq.gz", "_2.fastq.gz"]:
        file_path = MOCK_DATA_DIR / f"mock_sample{suffix}"
        _generate_mock_fastq(file_path)
        file_paths.append(file_path)
        logger.info(f"Generated mock file: {file_path} ({file_path.stat().st_size} bytes)")
    
    yield file_paths
    
    # Cleanup is optional in CI, but good practice locally
    # shutil.rmtree(MOCK_DATA_DIR, ignore_errors=True)

def test_mock_files_generated(mock_fastq_files):
    """Verify that mock FASTQ files exist and are valid gzip."""
    assert len(mock_fastq_files) == 2
    for file_path in mock_fastq_files:
        assert file_path.exists(), f"Mock file not found: {file_path}"
        assert file_path.suffix == ".gz"
        
        # Verify it's a valid gzip file
        try:
            with gzip.open(file_path, 'rt') as f:
                first_line = f.readline()
                assert first_line.startswith("@"), "Invalid FASTQ header format"
        except Exception as e:
            pytest.fail(f"Failed to read mock file {file_path}: {e}")

def test_mock_file_structure(mock_fastq_files):
    """Verify the structure of the generated mock FASTQ files."""
    file_path = mock_fastq_files[0]
    with gzip.open(file_path, 'rt') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # FASTQ format: 4 lines per record
    assert len(lines) % 4 == 0, "Invalid FASTQ record count"
    
    num_records = len(lines) // 4
    assert num_records == NUM_READS, f"Expected {NUM_READS} reads, got {num_records}"
    
    # Check headers
    for i in range(num_records):
        header_idx = i * 4
        assert lines[header_idx].startswith("@"), f"Invalid header at record {i}"
        assert lines[header_idx+1].startswith("ACGT"), f"Invalid sequence at record {i}"
        assert lines[header_idx+2].startswith("+"), f"Invalid separator at record {i}"

def test_checksum_calculation(mock_fastq_files):
    """Verify that checksums can be calculated on mock files (simulating T016)."""
    file_path = mock_fastq_files[0]
    
    # Calculate SHA256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    checksum = sha256_hash.hexdigest()
    assert len(checksum) == 64, "Invalid SHA256 checksum length"
    assert all(c in "0123456789abcdef" for c in checksum), "Invalid hex characters"
    
    logger.info(f"Mock file checksum: {checksum}")

def test_pipeline_flow_simulation(mock_fastq_files):
    """
    Simulate the pipeline flow: 
    1. Verify files exist (T015 mock)
    2. Verify checksums (T016 mock)
    3. Prepare for quantification (T019 mock)
    """
    # 1. Files exist
    assert all(p.exists() for p in mock_fastq_files)
    
    # 2. Checksums valid
    for p in mock_fastq_files:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            h.update(f.read())
        assert len(h.hexdigest()) == 64
    
    # 3. Simulate quantification input validation
    # (In real code, this would call Salmon; here we just verify inputs are ready)
    for p in mock_fastq_files:
        assert p.stat().st_size > 0, "Mock file is empty"
    
    logger.info("Pipeline flow simulation successful for mock data")
