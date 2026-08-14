"""
Pytest fixtures for integration tests.
Provides mock small FASTQ files and temporary directories to verify
pipeline flow without downloading real data.
"""
import os
import gzip
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def mock_fastq_content():
    """Generate a minimal valid FASTQ content string."""
    # Standard FASTQ format: @header, sequence, +, quality
    return [
        "@mock_read_1",
        "ACGTACGTACGTACGTACGT",
        "+",
        "IIIIIIIIIIIIIIIIIIII",
        "@mock_read_2",
        "TGCATGCATGCATGCATGCA",
        "+",
        "JJJJJJJJJJJJJJJJJJJJ",
    ]

@pytest.fixture
def mock_fastq_file_path(mock_fastq_content):
    """Create a temporary mock FASTQ file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.fastq', delete=False, encoding='utf-8'
    ) as f:
        for line in mock_fastq_content:
            f.write(line + '\n')
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_fastq_gz_path(mock_fastq_content):
    """Create a temporary gzipped mock FASTQ file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode='wb', suffix='.fastq.gz', delete=False
    ) as f:
        content = '\n'.join(mock_fastq_content).encode('utf-8')
        f.write(gzip.compress(content))
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix='test_coral_')
    yield Path(temp_dir)
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def mock_sample_metadata():
    """Return a dictionary simulating parsed sample metadata."""
    return {
        "sample_001": {
            "treatment": "Heat",
            "replicate": 1,
            "file": "mock_001.fastq.gz"
        },
        "sample_002": {
            "treatment": "Control",
            "replicate": 1,
            "file": "mock_002.fastq.gz"
        }
    }
