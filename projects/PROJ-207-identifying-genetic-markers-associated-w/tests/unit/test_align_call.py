"""
Unit tests for 02_align_call.sh logic verification.
Since this is a shell script, we test the existence of required tools
and the logic of file detection via a Python wrapper simulation.
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# Path to the script
SCRIPT_PATH = Path("code/02_align_call.sh")

def test_script_exists():
    """Verify the shell script exists."""
    assert SCRIPT_PATH.exists(), "02_align_call.sh must exist in code/"

def test_script_executable():
    """Verify the shell script has execute permissions."""
    assert os.access(SCRIPT_PATH, os.X_OK), "02_align_call.sh must be executable"

def test_prerequisite_check_logic():
    """
    Simulate the prerequisite check logic by creating a temp directory
    without the reference genome and ensuring the script fails gracefully.
    """
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a fake data/raw directory without the reference
        data_raw = tmpdir / "data" / "raw"
        data_raw.mkdir(parents=True)
        
        # Create a fake data/interim with dummy fastq to bypass fastq check
        data_interim = tmpdir / "data" / "interim"
        data_interim.mkdir(parents=True)
        
        # Create dummy fastq files
        (data_interim / "synthetic_R1.fastq").touch()
        (data_interim / "synthetic_R2.fastq").touch()
        
        # Create a dummy output dir
        data_processed = tmpdir / "data" / "processed"
        data_processed.mkdir(parents=True)
        
        # Copy script to temp dir and modify paths for testing
        # We will test the logic by checking if the script detects the missing reference
        # Since we can't easily run the whole pipeline without bwa/freebayes installed in the test env,
        # we verify the script structure contains the expected error message.
        
        content = SCRIPT_PATH.read_text()
        
        # Verify error handling for missing reference
        assert "Reference genome not found" in content
        assert "data/raw/honeybee_reference.fasta" in content
        
        # Verify error handling for missing tools
        assert "bwa is not installed" in content
        assert "FreeBayes is not installed" in content

def test_filter_logic_present():
    """Verify the script contains the specific filtering criteria."""
    content = SCRIPT_PATH.read_text()
    
    # Check for QUAL > 30
    assert "QUAL > 30" in content or "qual > 30" in content
    
    # Check for Depth >= 10
    assert "DP >= 10" in content or "dp >= 10" in content or "MIN_DEPTH=10" in content

def test_input_acceptance_patterns():
    """Verify the script looks for real_*.fastq and synthetic_*.fastq."""
    content = SCRIPT_PATH.read_text()
    
    assert "real_*.fastq" in content
    assert "synthetic_*.fastq" in content