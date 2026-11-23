"""
Unit tests for lifecycle_manager.py.
These tests verify the logic of compression and file age checking
without actually uploading to Zenodo.
"""
import os
import json
import tempfile
import gzip
from pathlib import Path
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock

# Import the module functions
from code.pipeline.lifecycle_manager import compress_fastqs, run_lifecycle_cycle

@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "raw"
        data_dir.mkdir(parents=True)
        yield data_dir

def test_compress_fastqs(temp_data_dir):
    """Test that compress_fastqs creates .gz files correctly."""
    # Create a dummy FASTQ file
    fastq_file = temp_data_dir / "sample_1.fastq"
    content = b"@read1\nACGT\n+\n!!!!\n"
    fastq_file.write_bytes(content)
    
    output_dir = temp_data_dir / "compressed"
    
    # Run compression
    result = compress_fastqs([fastq_file], output_dir)
    
    assert len(result) == 1
    assert result[0].suffix == ".gz"
    assert result[0].exists()
    
    # Verify content
    with gzip.open(result[0], 'rb') as f:
        assert f.read() == content

def test_compress_fastqs_missing_file(temp_data_dir, caplog):
    """Test that compress_fastqs handles missing files gracefully."""
    missing_file = temp_data_dir / "missing.fastq"
    output_dir = temp_data_dir / "compressed"
    
    result = compress_fastqs([missing_file], output_dir)
    
    assert len(result) == 0
    assert "File not found" in caplog.text

@patch('code.pipeline.lifecycle_manager.deposit_to_zenodo')
@patch('code.pipeline.lifecycle_manager.load_environment_config')
def test_run_lifecycle_cycle_skips_recent(mock_config, mock_deposit, temp_data_dir, caplog):
    """Test that recent files are not processed."""
    # Create a recent file
    recent_file = temp_data_dir / "recent.fastq"
    recent_file.write_bytes(b"@read\nACGT\n+\n!!!!\n")
    # Ensure it's "new" (default touch is now)
    
    mock_config.return_value = {}
    
    # Run with 30 days retention
    run_lifecycle_cycle(retention_days=30, data_dir=str(temp_data_dir), metadata_path="/tmp/test_meta.json")
    
    # Check that no files were processed
    assert "No FASTQ files found older than the retention period" in caplog.text
    mock_deposit.assert_not_called()

@patch('code.pipeline.lifecycle_manager.deposit_to_zenodo')
@patch('code.pipeline.lifecycle_manager.load_environment_config')
@patch('code.pipeline.lifecycle_manager.os.getenv')
def test_run_lifecycle_cycle_processes_old(mock_getenv, mock_config, mock_deposit, temp_data_dir, caplog):
    """Test that old files are compressed, 'uploaded', and deleted."""
    # Create an old file
    old_file = temp_data_dir / "old.fastq"
    old_file.write_bytes(b"@read\nACGT\n+\n!!!!\n")
    
    # Modify mtime to be 60 days ago
    old_time = (datetime.now() - timedelta(days=60)).timestamp()
    os.utime(old_file, (old_time, old_time))
    
    # Mock env
    mock_getenv.side_effect = lambda key, default=None: {
        "ZENODO_TOKEN": "fake_token_123",
        "DATA_DIR": str(temp_data_dir),
        "METADATA_PATH": "/tmp/test_meta.json"
    }.get(key, default)
    
    mock_config.return_value = {}
    mock_deposit.return_value = "10.5072/zenodo.123456"
    
    # Run cycle
    run_lifecycle_cycle(retention_days=30, data_dir=str(temp_data_dir), metadata_path="/tmp/test_meta.json")
    
    # Verify deposit was called
    assert mock_deposit.called
    
    # Verify old file is deleted
    assert not old_file.exists()
    
    # Verify log messages
    assert "Successfully deposited" in caplog.text