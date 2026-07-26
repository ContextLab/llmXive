"""
Unit tests for fastp preprocessing wrapper (T012a).

Tests cover:
- fastp availability checking
- Running fastp with mocked subprocess
- Processing single FASTQ files
- Main entry point with mocked fastp
"""

import pytest
import os
import tempfile
import gzip
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocess_fastp import (
    check_fastp_available,
    run_fastp,
    process_fastq_file,
    main
)


@pytest.fixture
def temp_fastq_file():
    """Create a temporary FASTQ file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.fastq.gz',
        delete=False
    ) as f:
        # Write minimal valid FASTQ content (gzipped)
        fastq_content = b"""@read1
        ACGTACGTACGT
        +
        IIIIIIIIIIII
        @read2
        TGCATGCATGCA
        +
        IIIIIIIIIIII
        """
        with gzip.open(f.name, 'wb') as gz:
            gz.write(fastq_content)
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_check_fastp_available_with_mock():
    """Test fastp availability check when fastp is available."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="0.23.1\n",
            stderr=""
        )
        
        is_available, version = check_fastp_available()
        
        assert is_available is True
        assert version == "0.23.1"
        mock_run.assert_called_once_with(
            ["fastp", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

def test_check_fastp_available_not_found():
    """Test fastp availability check when fastp is not installed."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("fastp not found")
        
        is_available, version = check_fastp_available()
        
        assert is_available is False
        assert version is None

def test_run_fastp_success(temp_fastq_file, temp_output_dir):
    """Test successful run of fastp with mocked subprocess."""
    output_fastq = temp_output_dir / "test_trimmed.fastq.gz"
    output_json = temp_output_dir / "test_report.json"
    
    # Create a mock fastp report
    mock_report = {
        "summary": {
            "before_filtering": {"total_reads": 2},
            "after_filtering": {
                "total_reads": 2,
                "read1_filtered": 0,
                "quality_filtered": 0,
                "adapter_filtered": 0
            }
        }
    }
    
    # Create the output file to simulate success
    output_fastq.touch()
    with open(output_json, 'w') as f:
        json.dump(mock_report, f)
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        success = run_fastp(
            input_fastq=temp_fastq_file,
            output_fastq=output_fastq,
            output_json=output_json,
            threads=2
        )
        
        assert success is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "fastp" in cmd
        assert "-i" in cmd
        assert "-o" in cmd
        assert "-j" in cmd

def test_run_fastp_missing_input(temp_output_dir):
    """Test fastp fails with missing input file."""
    output_fastq = temp_output_dir / "test_trimmed.fastq.gz"
    output_json = temp_output_dir / "test_report.json"
    
    non_existent = Path("/non/existent/file.fastq.gz")
    
    success = run_fastp(
        input_fastq=non_existent,
        output_fastq=output_fastq,
        output_json=output_json,
        threads=2
    )
    
    # Should fail because input doesn't exist
    assert success is False

def test_process_fastq_file(temp_fastq_file, temp_output_dir):
    """Test processing a single FASTQ file."""
    # Mock the run_fastp function and file operations
    mock_report = {
        "summary": {
            "before_filtering": {"total_reads": 2},
            "after_filtering": {
                "total_reads": 2,
                "read1_filtered": 0,
                "quality_filtered": 0,
                "adapter_filtered": 0
            }
        }
    }
    
    with patch('src.data.preprocess_fastp.run_fastp') as mock_run:
        mock_run.return_value = True
        
        # Mock file existence check
        with patch.object(Path, 'exists') as mock_exists:
            mock_exists.return_value = True
            
            # Mock file reading for checksum
            with patch('builtins.open', MagicMock()) as mock_open:
                mock_open.return_value.__enter__ = MagicMock()
                mock_open.return_value.__exit__ = MagicMock()
                
                # Mock hashlib
                with patch('src.data.preprocess_fastp.hashlib') as mock_hashlib:
                    mock_hash = MagicMock()
                    mock_hash.hexdigest.return_value = "abc123"
                    mock_hashlib.sha256.return_value = mock_hash
                    
                    # Mock json load
                    with patch('builtins.open', MagicMock()) as mock_json_open:
                        mock_json_open.return_value.__enter__ = MagicMock(
                            return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_report)))
                        )
                        mock_json_open.return_value.__exit__ = MagicMock(return_value=False)
                        
                        result = process_fastq_file(
                            input_path=temp_fastq_file,
                            output_dir=temp_output_dir,
                            threads=2
                        )
                        
                        assert result is not None
                        assert "accession_id" in result
                        assert result["output_file"].endswith("_R1_trimmed.fastq.gz")
                        assert "checksum" in result
                        assert "metrics" in result

def test_main_with_mocked_fastp(temp_fastq_file, temp_output_dir, caplog):
    """Test main entry point with mocked fastp."""
    with patch('src.data.preprocess_fastp.check_fastp_available') as mock_check:
        mock_check.return_value = (True, "0.23.1")
        
        with patch('src.data.preprocess_fastp.process_fastq_file') as mock_process:
            mock_process.return_value = {
                "accession_id": "test123",
                "input_file": str(temp_fastq_file),
                "output_file": str(temp_output_dir / "test_trimmed.fastq.gz"),
                "checksum": "abc123",
                "metrics": {}
            }
            
            with patch('sys.argv', [
                'preprocess_fastp.py',
                '--input', str(temp_fastq_file),
                '--output-dir', str(temp_output_dir),
                '--threads', '2'
            ]):
                main()
                
                mock_check.assert_called_once()
                mock_process.assert_called_once()