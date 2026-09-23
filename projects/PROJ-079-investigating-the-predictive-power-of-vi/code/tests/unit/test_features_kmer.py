"""
Unit tests for k-mer frequency calculation.

Tests cover:
- Valid FASTA input
- File not found
- Empty sequence
- Short sequence
- Mixed case
- Invalid bases
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_kmer_frequencies


def test_calculate_kmer_frequencies_valid_fasta():
    """Test k-mer calculation with a valid FASTA file."""
    # Create a temporary FASTA file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        f.write("ACGTACGTACGTACGT\n")  # 16 bases
        temp_path = f.name

    try:
        result = calculate_kmer_frequencies(temp_path)

        # Check that we have k=3 and k=4 k-mers
        assert 'ACG' in result  # k=3
        assert 'ACGT' in result  # k=4

        # Check that frequencies sum to 1 for each k
        k3_sum = sum(v for k, v in result.items() if len(k) == 3)
        k4_sum = sum(v for k, v in result.items() if len(k) == 4)

        assert abs(k3_sum - 1.0) < 1e-6, f"K=3 frequencies sum to {k3_sum}, expected 1.0"
        assert abs(k4_sum - 1.0) < 1e-6, f"K=4 frequencies sum to {k4_sum}, expected 1.0"

        # Check specific values for our test sequence
        # Sequence: ACGTACGTACGTACGT
        # K=3: ACG, CGT, GTA, TAC, ACG, CGT, GTA, TAC, ACG, CGT
        # Counts: ACG=3, CGT=3, GTA=2, TAC=2 -> Total=10
        assert abs(result['ACG'] - 0.3) < 1e-6
        assert abs(result['CGT'] - 0.3) < 1e-6
        assert abs(result['GTA'] - 0.2) < 1e-6
        assert abs(result['TAC'] - 0.2) < 1e-6

    finally:
        os.unlink(temp_path)


def test_calculate_kmer_frequencies_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_kmer_frequencies("/nonexistent/path/to/file.fasta")


def test_calculate_kmer_frequencies_empty_sequence():
    """Test that ValueError is raised for empty sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        # No sequence
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Sequence is empty"):
            calculate_kmer_frequencies(temp_path)
    finally:
        os.unlink(temp_path)


def test_calculate_kmer_frequencies_short_sequence():
    """Test behavior with sequence shorter than k=3."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        f.write("AC\n")  # Only 2 bases
        temp_path = f.name

    try:
        # Should raise ValueError because no k-mers can be extracted
        with pytest.raises(ValueError, match="No k-mers could be extracted"):
            calculate_kmer_frequencies(temp_path)
    finally:
        os.unlink(temp_path)


def test_calculate_kmer_frequencies_mixed_case():
    """Test that mixed case sequences are handled correctly."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        f.write("AcGtAcGt\n")  # Mixed case
        temp_path = f.name

    try:
        result = calculate_kmer_frequencies(temp_path)

        # Should be normalized to uppercase
        assert 'ACG' in result
        assert 'CGT' in result

        # Frequencies should match the lowercase version
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f2:
            f2.write(">test_sequence\n")
            f2.write("acgtacgt\n")
            temp_path2 = f2.name

        try:
            result2 = calculate_kmer_frequencies(temp_path2)
            assert result == result2
        finally:
            os.unlink(temp_path2)

    finally:
        os.unlink(temp_path)


def test_calculate_kmer_frequencies_with_invalid_bases():
    """Test that ValueError is raised for invalid bases."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        f.write("ACGTXACGT\n")  # X is invalid
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Invalid characters in sequence"):
            calculate_kmer_frequencies(temp_path)
    finally:
        os.unlink(temp_path)