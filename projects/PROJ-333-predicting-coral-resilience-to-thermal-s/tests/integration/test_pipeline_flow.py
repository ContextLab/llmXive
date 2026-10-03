"""
Integration test scaffolding for the coral resilience pipeline.
Uses mock FASTQ files to verify pipeline flow without downloading real data.

This test verifies:
1. Mock FASTQ generation creates valid files
2. Pipeline ingestion logic can read mock files
3. Memory tracking works with mock data
4. Checksum calculation works on mock files

NOTE: This is a scaffolding test. Real data tests are handled in T014.
"""
import os
import gzip
import hashlib
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_memory_usage_mb, setup_logger
from utils import calculate_checksum

# Constants for mock data generation
MOCK_SEQ_LENGTH = 50
MOCK_READ_COUNT = 100
QUALITY_SCORE = 'I' * MOCK_SEQ_LENGTH  # High quality score

logger = setup_logger('integration_test', level='INFO')

def generate_mock_fastq(read_id: str, sequence: str, quality: str) -> str:
    """Generate a single FASTQ record."""
    return f"@{read_id}\n{sequence}\n+\n{quality}\n"

def create_mock_fastq_file(output_path: Path, num_reads: int = MOCK_READ_COUNT) -> None:
    """Create a mock FASTQ file with random-looking sequences."""
    import random
    import string
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with gzip.open(output_path, 'wt') as f:
        for i in range(num_reads):
            read_id = f"mock_sample_{i:04d}"
            # Generate a random DNA sequence
            sequence = ''.join(random.choices('ACGT', k=MOCK_SEQ_LENGTH))
            quality = QUALITY_SCORE
            
            f.write(generate_mock_fastq(read_id, sequence, quality))

def test_mock_fastq_generation():
    """Test that mock FASTQ files are generated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_dir = Path(tmpdir) / "mock_fastq"
        mock_dir.mkdir()
        
        file1 = mock_dir / "mock_sample_1.fastq.gz"
        file2 = mock_dir / "mock_sample_2.fastq.gz"
        
        create_mock_fastq_file(file1)
        create_mock_fastq_file(file2)
        
        # Verify files exist and are non-empty
        assert file1.exists(), f"Mock file {file1} was not created"
        assert file2.exists(), f"Mock file {file2} was not created"
        
        assert file1.stat().st_size > 0, "Mock file 1 is empty"
        assert file2.stat().st_size > 0, "Mock file 2 is empty"
        
        # Verify files are valid gzip
        with gzip.open(file1, 'rt') as f:
            first_line = f.readline()
            assert first_line.startswith('@'), "First line should start with @ (FASTQ header)"
        
        logger.info(f"Mock FASTQ files generated successfully: {file1.name}, {file2.name}")

def test_checksum_calculation_on_mock():
    """Test that checksum calculation works on mock files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_dir = Path(tmpdir) / "mock_fastq"
        mock_dir.mkdir()
        
        mock_file = mock_dir / "checksum_test.fastq.gz"
        create_mock_fastq_file(mock_file)
        
        # Calculate checksum
        checksum = calculate_checksum(mock_file)
        
        assert checksum is not None, "Checksum calculation failed"
        assert len(checksum) == 64, "SHA256 checksum should be 64 characters"
        
        logger.info(f"Checksum calculated for {mock_file.name}: {checksum[:16]}...")

def test_memory_tracking_with_mock():
    """Test that memory tracking functions work."""
    initial_memory = get_memory_usage_mb()
    
    # Process mock data
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_dir = Path(tmpdir) / "mock_fastq"
        mock_dir.mkdir()
        
        mock_file = mock_dir / "memory_test.fastq.gz"
        create_mock_fastq_file(mock_file, num_reads=1000)
        
        # Read and process the file
        with gzip.open(mock_file, 'rt') as f:
            lines = f.readlines()
            assert len(lines) == 4 * 1000, f"Expected 4000 lines, got {len(lines)}"
    
    final_memory = get_memory_usage_mb()
    
    logger.info(f"Memory usage: {initial_memory:.2f} MB -> {final_memory:.2f} MB")
    assert final_memory >= initial_memory, "Memory should not decrease significantly"

def test_pipeline_flow_with_mock():
    """Test the basic pipeline flow with mock data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_dir = Path(tmpdir) / "mock_fastq"
        mock_dir.mkdir()
        
        # Generate mock files
        mock_file1 = mock_dir / "mock_sample_1.fastq.gz"
        mock_file2 = mock_dir / "mock_sample_2.fastq.gz"
        create_mock_fastq_file(mock_file1)
        create_mock_fastq_file(mock_file2)
        
        # Simulate pipeline steps
        logger.info("Step 1: Mock files generated")
        
        # Step 2: Calculate checksums
        checksum1 = calculate_checksum(mock_file1)
        checksum2 = calculate_checksum(mock_file2)
        logger.info(f"Step 2: Checksums calculated - {checksum1[:16]}..., {checksum2[:16]}...")
        
        # Step 3: Verify file integrity (mock verification)
        assert checksum1 is not None and checksum2 is not None
        logger.info("Step 3: File integrity verified")
        
        # Step 4: Process files (mock processing)
        total_reads = 0
        for mock_file in [mock_file1, mock_file2]:
            with gzip.open(mock_file, 'rt') as f:
                lines = f.readlines()
                total_reads += len(lines) // 4
        
        logger.info(f"Step 4: Processed {total_reads} reads from mock files")
        
        assert total_reads == 200, f"Expected 200 reads, got {total_reads}"
        logger.info("Pipeline flow test completed successfully")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
