"""
Unit tests for HISAT2 preprocessing wrapper (T012b).
"""

import os
import sys
import tempfile
import gzip
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocess_hisat2 import (
    check_hisat2_available,
    run_hisat2,
    process_study_hisat2,
    is_synthetic_mode,
    main
)


@pytest.fixture
def temp_fastq_file(tmp_path):
    """Create a temporary fake FASTQ file."""
    fastq_path = tmp_path / "test_R1.fastq.gz"
    with gzip.open(fastq_path, "wt") as f:
        f.write("@read1\nACGTACGT\n+\nIIIIIIII\n")
    return fastq_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def temp_genome_index(tmp_path):
    """Create a fake genome index file."""
    # HISAT2 index files have specific extensions, we just need them to exist for the test
    index_prefix = tmp_path / "genome"
    index_prefix.touch()
    return index_prefix


@pytest.fixture
def synthetic_mode_marker(tmp_path):
    """Create a marker file to simulate synthetic mode."""
    marker_dir = tmp_path / "data" / "synthetic"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / ".mode_active"
    marker.touch()
    return marker


def test_check_hisat2_available_with_mock():
    """Test HISAT2 availability check with mocked subprocess."""
    with patch("src.data.preprocess_hisat2.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"hisat2 2.4.4\n",
            stderr=b""
        )
        result = check_hisat2_available()
        assert result is True


def test_check_hisat2_available_not_found():
    """Test HISAT2 availability check when command is not found."""
    with patch("src.data.preprocess_hisat2.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("Command not found")
        result = check_hisat2_available()
        assert result is False


def test_run_hisat2_missing_input(temp_output_dir, temp_genome_index):
    """Test that run_hisat2 returns False when input files are missing."""
    fake_r1 = temp_output_dir / "missing_R1.fastq.gz"
    fake_r2 = temp_output_dir / "missing_R2.fastq.gz"
    output_bam = temp_output_dir / "test.bam"

    result = run_hisat2(
        input_r1=fake_r1,
        input_r2=fake_r2,
        genome_index=temp_genome_index,
        output_bam=output_bam
    )
    assert result is False


def test_run_hisat2_success_with_mock(temp_fastq_file, temp_output_dir, temp_genome_index):
    """Test successful HISAT2 run with mocked subprocess."""
    # Create fake R2 file
    fake_r2 = temp_output_dir / "test_R2.fastq.gz"
    with gzip.open(fake_r2, "wt") as f:
        f.write("@read2\nTGCA TGCA\n+\nIIIIIIII\n")

    output_bam = temp_output_dir / "test.bam"
    output_bam.touch()  # Pretend BAM was created

    with patch("src.data.preprocess_hisat2.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"",
            stderr=b"100.00% overall alignment rate"
        )

        result = run_hisat2(
            input_r1=temp_fastq_file,
            input_r2=fake_r2,
            genome_index=temp_genome_index,
            output_bam=output_bam,
            threads=2
        )

        assert result is True
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert "-p" in cmd_args
        assert "2" in cmd_args


def test_process_study_hisat2_missing_files(temp_output_dir, temp_genome_index):
    """Test process_study_hisat2 when trimmed files are missing."""
    result = process_study_hisat2(
        accession_id="nonexistent",
        trimmed_dir=temp_output_dir,
        output_dir=temp_output_dir,
        genome_index=temp_genome_index
    )
    assert result is None


def test_is_synthetic_mode_false():
    """Test is_synthetic_mode returns False when marker is absent."""
    # Ensure marker doesn't exist in current working directory
    marker = Path("data/synthetic/.mode_active")
    if marker.exists():
        marker.unlink()
    assert is_synthetic_mode() is False


def test_is_synthetic_mode_true(synthetic_mode_marker):
    """Test is_synthetic_mode returns True when marker is present."""
    # Temporarily change CWD to the temp dir where marker exists
    original_cwd = os.getcwd()
    try:
        os.chdir(str(synthetic_mode_marker.parent.parent.parent))
        assert is_synthetic_mode() is True
    finally:
        os.chdir(original_cwd)


@pytest.mark.integration
def test_main_with_mocked_fastp_and_hisat2(tmp_path):
    """Integration test for main() with mocked tools."""
    # Setup temp directories
    trimmed_dir = tmp_path / "trimmed"
    trimmed_dir.mkdir()
    output_dir = tmp_path / "aligned"
    output_dir.mkdir()

    # Create fake trimmed files
    r1_file = trimmed_dir / "GSM123_R1_trimmed.fastq.gz"
    r2_file = trimmed_dir / "GSM123_R2_trimmed.fastq.gz"
    with gzip.open(r1_file, "wt") as f:
        f.write("@read1\nACGT\n+\nIIII\n")
    with gzip.open(r2_file, "wt") as f:
        f.write("@read2\nTGCA\n+\nIIII\n")

    genome_index = tmp_path / "genome_index"
    genome_index.touch()

    # Mock subprocess and file creation
    with patch("src.data.preprocess_hisat2.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"",
            stderr=b"100.00% overall alignment rate"
        )

        # Create fake BAM
        fake_bam = output_dir / "GSM123.bam"
        fake_bam.touch()

        with patch("src.data.preprocess_hisat2.Path.exists") as mock_exists:
            # Mock exists to return True for necessary files
            def side_effect(path):
                path_str = str(path)
                if "genome_index" in path_str or "GSM123" in path_str:
                    return True
                return False

            mock_exists.side_effect = side_effect

            with patch("src.data.preprocess_hisat2.get_data_path") as mock_get_path:
                mock_get_path.return_value = tmp_path

                sys.argv = [
                    "preprocess_hisat2.py",
                    "--genome-index", str(genome_index),
                    "--threads", "2",
                    "--trimmed-dir", str(trimmed_dir),
                    "--output-dir", str(output_dir)
                ]

                result = main()
                assert result == 0