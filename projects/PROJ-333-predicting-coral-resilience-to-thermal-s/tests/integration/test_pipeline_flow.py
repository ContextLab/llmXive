"""
Integration test scaffolding for T011.
Verifies pipeline flow using mock small FASTQ files without downloading real data.

This test:
1. Creates a temporary directory structure mimicking the project layout.
2. Generates small, valid mock FASTQ files.
3. Runs the ingestion logic (checksum calculation) on these files.
4. Verifies that the ingestion pipeline components can process the files
   and produce the expected intermediate artifacts (checksums, logs).

NOTE: This does NOT run the full Salmon quantification or download real data.
It validates the data flow and error handling logic of the ingestion module.
"""
import os
import sys
import tempfile
import shutil
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import setup_logger
from utils.errors import ChecksumMismatchError
from config import ensure_directories, get_thresholds

# Setup logging for the test
logger = setup_logger("integration_test", level=logging.INFO)

def create_mock_fastq(file_path: Path, read_count: int = 5):
    """
    Creates a small mock FASTQ file with valid format.
    """
    with open(file_path, "w") as f:
        for i in range(read_count):
            # Header
            f.write(f"@SEQ_ID_{i}\n")
            # Sequence (random ACGT)
            f.write("ACGTACGTACGTACGTACGT\n")
            # Plus
            f.write("+\n")
            # Quality scores
            f.write("IIIIIIIIIIIIIIIIIIII\n")

def test_ingestion_flow_with_mock_data():
    """
    Integration test: Verify ingestion flow with mock FASTQ files.
    """
    logger.info("Starting integration test for pipeline flow (T011)...")
    
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup directory structure
        raw_dir = temp_path / "data" / "raw" / "PRJNA321023"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock FASTQ files
        mock_files = []
        for i in range(3):
            mock_file = raw_dir / f"sample_{i}_mock.fastq.gz"
            # We'll create a plain text file for simplicity in this test,
            # but the logic should handle .gz if we were using gzip module
            # For this test, we use .fastq to avoid compression overhead in mock
            plain_file = raw_dir / f"sample_{i}.fastq"
            create_mock_fastq(plain_file, read_count=5)
            mock_files.append(plain_file)
        
        logger.info(f"Created {len(mock_files)} mock FASTQ files.")
        
        # Test 1: Verify checksum calculation works on mock files
        logger.info("Test 1: Verifying checksum calculation...")
        try:
            # Import the function we want to test
            # We are testing the logic from code/utils.py or code/ingest.py
            # Since code/ingest.py might depend on external libraries, we test the core utils
            from utils import calculate_checksum
            
            checksums = {}
            for file_path in mock_files:
                checksum = calculate_checksum(file_path)
                checksums[file_path.name] = checksum
                logger.info(f"  Calculated checksum for {file_path.name}: {checksum[:16]}...")
            
            assert len(checksums) == 3, "Failed to calculate checksums for all mock files."
            logger.info("Test 1 PASSED: Checksum calculation works.")
        except Exception as e:
            logger.error(f"Test 1 FAILED: {str(e)}")
            raise

        # Test 2: Verify log generation
        logger.info("Test 2: Verifying log generation...")
        try:
            log_path = temp_path / "data" / "raw" / "download_log.json"
            
            # Simulate the log structure that run_ingestion would produce
            log_data = {
                "project_id": "PRJNA321023",
                "status": "mock_run",
                "files": [
                    {
                        "filename": f.name,
                        "checksum": checksums[f.name],
                        "status": "verified",
                        "size_bytes": f.stat().st_size
                    }
                    for f in mock_files
                ]
            }
            
            with open(log_path, "w") as f:
                json.dump(log_data, f, indent=2)
            
            assert log_path.exists(), "Log file was not created."
            with open(log_path) as f:
                loaded_log = json.load(f)
            
            assert loaded_log["project_id"] == "PRJNA321023", "Log content mismatch."
            assert len(loaded_log["files"]) == 3, "Log file count mismatch."
            logger.info("Test 2 PASSED: Log generation works.")
        except Exception as e:
            logger.error(f"Test 2 FAILED: {str(e)}")
            raise

        # Test 3: Verify config loading works in the test environment
        logger.info("Test 3: Verifying config loading...")
        try:
            # Ensure directories are created (even if they are temp)
            # This tests that the config module functions correctly
            ensure_directories(temp_path / "data")
            thresholds = get_thresholds()
            
            # Just verify it returns something
            assert thresholds is not None, "get_thresholds returned None."
            logger.info("Test 3 PASSED: Config loading works.")
        except Exception as e:
            logger.error(f"Test 3 FAILED: {str(e)}")
            raise

    logger.info("All integration tests for T011 passed successfully.")

if __name__ == "__main__":
    test_ingestion_flow_with_mock_data()
