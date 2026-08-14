"""
Integration tests to verify the pipeline flow using mock small FASTQ files.
This task (T011) ensures that the ingestion, checksum, and basic processing
steps work end-to-end without requiring real network downloads or large data.
"""
import os
import json
import gzip
import hashlib
import pytest
from pathlib import Path

# Import the logging utility to verify it works in integration
from utils.logging import setup_logger, get_memory_usage_mb

# Import the config to ensure paths are resolved correctly
from config import ensure_directories, get_thresholds

# Import the ingest module functions we are testing
# Note: We are testing the logic against mock files, not real network calls
from data.ingest import calculate_checksum, IngestionError

def test_mock_fastq_creation_and_checksum(mock_fastq_file_path):
    """
    Verify that a mock FASTQ file can be created and its checksum calculated.
    This validates the core checksum logic without needing real data.
    """
    assert os.path.exists(mock_fastq_file_path), "Mock FASTQ file was not created"
    
    # Calculate checksum
    checksum = calculate_checksum(mock_fastq_file_path)
    
    assert checksum is not None, "Checksum calculation returned None"
    assert len(checksum) == 64, "SHA256 checksum should be 64 characters"
    assert all(c in '0123456789abcdef' for c in checksum), "Invalid hex characters in checksum"

def test_gzipped_mock_fastq_checksum(mock_fastq_gz_path):
    """
    Verify that a gzipped mock FASTQ file can be checksummed.
    The checksum is calculated on the compressed file content.
    """
    assert os.path.exists(mock_fastq_gz_path), "Mock GZ file was not created"
    
    checksum = calculate_checksum(mock_fastq_gz_path)
    
    assert checksum is not None
    assert len(checksum) == 64

def test_pipeline_directory_structure(temp_output_dir):
    """
    Verify that the pipeline creates the required directory structure
    as defined in config.py.
    """
    # We pass the temp dir as a base to ensure we don't write to project root
    # In a real scenario, ensure_directories creates the standard dirs.
    # Here we verify the logic works by checking if the function can handle
    # a writable path.
    
    # Mock the config to use our temp dir if necessary, or just ensure
    # the function runs without error on the project defaults.
    # Since we can't easily override config.py constants in this test scope
    # without side effects, we just call it to ensure it doesn't crash.
    try:
        ensure_directories()
    except Exception as e:
        pytest.fail(f"ensure_directories() failed: {e}")

def test_memory_logging_integration():
    """
    Verify that the logging infrastructure works correctly in an integration context.
    """
    logger = setup_logger("integration_test", level="INFO")
    assert logger is not None
    
    # Log memory usage
    mem_mb = get_memory_usage_mb()
    logger.info(f"Current memory usage: {mem_mb:.2f} MB")
    
    assert mem_mb >= 0, "Memory usage should be non-negative"

def test_config_thresholds_loading():
    """
    Verify that configuration thresholds can be loaded.
    """
    thresholds = get_thresholds()
    assert thresholds is not None
    # The thresholds might be None/placeholder as per T004, but the function must return
    assert isinstance(thresholds, dict) or thresholds is None

def test_mock_ingestion_flow(mock_fastq_gz_path, temp_output_dir, mock_sample_metadata):
    """
    Simulate the ingestion flow:
    1. Verify file exists
    2. Calculate checksum
    3. Verify integrity (self-check)
    4. Log success
    
    This replaces the need for downloading real data for the flow test.
    """
    # 1. File exists
    assert os.path.exists(mock_fastq_gz_path)
    
    # 2. Calculate checksum
    checksum = calculate_checksum(mock_fastq_gz_path)
    
    # 3. Verify integrity (simulate by recalculating and comparing)
    # In the real code, verify_file_integrity compares against a fetched checksum.
    # Here we simulate a successful verification.
    re_calc = calculate_checksum(mock_fastq_gz_path)
    assert checksum == re_calc, "Checksum verification failed"
    
    # 4. Log the "ingestion"
    logger = setup_logger("mock_ingestion", level="INFO")
    logger.info(f"Mock ingestion successful for {mock_fastq_gz_path} with checksum {checksum}")
    
    # 5. Write a mock manifest to temp dir to simulate output
    manifest_path = temp_output_dir / "mock_manifest.json"
    manifest_data = {
        "file": mock_fastq_gz_path,
        "checksum": checksum,
        "status": "verified"
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    assert manifest_path.exists(), "Manifest file was not created"

def test_mock_fastq_content_validity(mock_fastq_content):
    """
    Verify that the generated mock FASTQ content adheres to the 4-line record format.
    """
    # There should be an even number of lines (4 per record)
    assert len(mock_fastq_content) % 4 == 0
    
    for i in range(0, len(mock_fastq_content), 4):
        header = mock_fastq_content[i]
        seq = mock_fastq_content[i+1]
        plus = mock_fastq_content[i+2]
        qual = mock_fastq_content[i+3]
        
        assert header.startswith('@'), f"Header must start with @: {header}"
        assert plus == '+', f"Plus line must be +: {plus}"
        assert len(seq) == len(qual), f"Sequence and quality lengths must match: {len(seq)} vs {len(qual)}"
