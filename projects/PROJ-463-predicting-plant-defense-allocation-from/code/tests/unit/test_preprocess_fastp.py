"""
Unit tests for preprocess_fastp.py
"""

import pytest
import os
import tempfile
import gzip
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocess_fastp import (
    check_fastp_available,
    run_fastp,
    process_fastq_file,
    main
)
from src.utils.config import reset_config, get_config


@pytest.fixture
def temp_fastq_file(tmp_path):
    """Create a temporary FASTQ file for testing."""
    fastq_file = tmp_path / "test_sample.fastq.gz"
    
    # Create a minimal valid FASTQ content
    fastq_content = b"""@read1
    ACTGACTGACTG
    +
    IIIIIIIIIIII
    @read2
    TGCA TGCA TGCA
    +
    IIIIIIIIIIII
    """
    
    with gzip.open(fastq_file, 'wb') as f:
        f.write(fastq_content)
    
    return fastq_file

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

def test_check_fastp_available_with_mock():
    """Test fastp availability check with mocked subprocess."""
    with patch('src.data.preprocess_fastp.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="fastp 0.23.0",
            stderr=""
        )
        
        result = check_fastp_available()
        assert result is True
        
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["fastp", "--version"]

def test_check_fastp_available_not_found():
    """Test fastp availability check when not installed."""
    with patch('src.data.preprocess_fastp.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("fastp not found")
        
        result = check_fastp_available()
        assert result is False

@pytest.mark.skipif(
    not check_fastp_available(),
    reason="fastp not installed in environment"
)
def test_run_fastp_success(temp_fastq_file, temp_output_dir):
    """Test successful fastp execution."""
    output_fastq = temp_output_dir / "trimmed.fastq.gz"
    output_html = temp_output_dir / "report.html"
    output_json = temp_output_dir / "report.json"
    
    success, message = run_fastp(
        input_fastq=temp_fastq_file,
        output_fastq=output_fastq,
        output_report_html=output_html,
        output_report_json=output_json,
        threads=2
    )
    
    assert success is True
    assert output_fastq.exists()
    assert output_html.exists()
    assert output_json.exists()

@pytest.mark.skipif(
    not check_fastp_available(),
    reason="fastp not installed in environment"
)
def test_run_fastp_missing_input(temp_output_dir):
    """Test fastp execution with missing input file."""
    output_fastq = temp_output_dir / "trimmed.fastq.gz"
    output_html = temp_output_dir / "report.html"
    output_json = temp_output_dir / "report.json"
    
    non_existent = temp_output_dir / "non_existent.fastq.gz"
    
    success, message = run_fastp(
        input_fastq=non_existent,
        output_fastq=output_fastq,
        output_report_html=output_html,
        output_report_json=output_json,
        threads=2
    )
    
    assert success is False
    assert "not found" in message

def test_process_fastq_file(temp_fastq_file, temp_output_dir):
    """Test processing a single FASTQ file."""
    with patch('src.data.preprocess_fastp.run_fastp') as mock_run:
        mock_run.return_value = (True, "Success")
        
        result = process_fastq_file(
            input_path=temp_fastq_file,
            output_dir=temp_output_dir,
            base_name="test_sample"
        )
        
        assert result["success"] is True
        assert result["output_fastq"] is not None
        assert "test_sample_trimmed" in result["output_fastq"]

def test_main_with_mocked_fastp(temp_path, temp_fastq_file):
    """Test main function with mocked fastp."""
    with patch('src.data.preprocess_fastp.check_fastp_available', return_value=True):
        with patch('src.data.preprocess_fastp.run_fastp') as mock_run:
            mock_run.return_value = (True, "Success")
            
            with patch('sys.argv', ['preprocess_fastp', '--mode', 'synthetic', '--input', str(temp_fastq_file)]):
                # This would normally exit, so we catch it
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Should exit with 0 on success
                assert exc_info.value.code == 0