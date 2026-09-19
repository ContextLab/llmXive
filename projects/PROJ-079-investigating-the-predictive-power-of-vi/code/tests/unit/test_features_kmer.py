import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_kmer_frequencies

def test_calculate_kmer_frequencies_valid_fasta():
    """Test k-mer frequency calculation with a valid FASTA file."""
    # Create a temporary FASTA file with a known sequence
    # Sequence: ACGTACGT (length 8)
    # k=3: ACG, CGT, GTA, TAC, ACG, CGT -> ACG:2, CGT:2, GTA:1, TAC:1 (total 6)
    # k=4: ACGT, CGTA, GTAC, TACG, ACGT -> ACGT:2, CGTA:1, GTAC:1, TACG:1 (total 5)
    fasta_content = """>test_sequence
    ACGTACGT
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(fasta_content)
        temp_path = f.name
    
    try:
        result = calculate_kmer_frequencies(temp_path)
        
        # Check k=3 frequencies
        assert 'k3_ACG' in result
        assert 'k3_CGT' in result
        assert 'k3_GTA' in result
        assert 'k3_TAC' in result
        
        # Verify frequencies (within floating point tolerance)
        assert abs(result['k3_ACG'] - 2/6) < 1e-9
        assert abs(result['k3_CGT'] - 2/6) < 1e-9
        assert abs(result['k3_GTA'] - 1/6) < 1e-9
        assert abs(result['k3_TAC'] - 1/6) < 1e-9
        
        # Check k=4 frequencies
        assert 'k4_ACGT' in result
        assert 'k4_CGTA' in result
        assert 'k4_GTAC' in result
        assert 'k4_TACG' in result
        
        # Verify frequencies
        assert abs(result['k4_ACGT'] - 2/5) < 1e-9
        assert abs(result['k4_CGTA'] - 1/5) < 1e-9
        assert abs(result['k4_GTAC'] - 1/5) < 1e-9
        assert abs(result['k4_TACG'] - 1/5) < 1e-9
        
        # Verify no k=5 or k=6 features (as per spec amendment)
        for key in result:
            assert not key.startswith('k5_'), f"Unexpected k=5 feature: {key}"
            assert not key.startswith('k6_'), f"Unexpected k=6 feature: {key}"
            
    finally:
        os.unlink(temp_path)

def test_calculate_kmer_frequencies_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_kmer_frequencies("/nonexistent/path/to/file.fasta")

def test_calculate_kmer_frequencies_empty_sequence():
    """Test that ValueError is raised for empty sequence."""
    fasta_content = """>empty_sequence
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(fasta_content)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            calculate_kmer_frequencies(temp_path)
    finally:
        os.unlink(temp_path)

def test_calculate_kmer_frequencies_short_sequence():
    """Test behavior with sequence too short for k=4."""
    # Sequence of length 3: only k=3 possible
    fasta_content = """>short_sequence
    ACG
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(fasta_content)
        temp_path = f.name
    
    try:
        result = calculate_kmer_frequencies(temp_path)
        
        # Should have k=3 feature
        assert 'k3_ACG' in result
        assert abs(result['k3_ACG'] - 1.0) < 1e-9
        
        # Should NOT have any k=4 features
        for key in result:
            assert not key.startswith('k4_'), f"Unexpected k=4 feature for short sequence: {key}"
    finally:
        os.unlink(temp_path)

def test_calculate_kmer_frequencies_mixed_case():
    """Test that mixed case sequences are handled correctly."""
    fasta_content = """>mixed_case
    ACGTacgt
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(fasta_content)
        temp_path = f.name
    
    try:
        result = calculate_kmer_frequencies(temp_path)
        
        # Should treat as uppercase
        assert 'k3_ACG' in result
        assert 'k3_CGT' in result
        assert 'k3_GTA' in result
        assert 'k3_TAC' in result
        
        # Frequencies should match the test_calculate_kmer_frequencies_valid_fasta test
        assert abs(result['k3_ACG'] - 2/6) < 1e-9
        assert abs(result['k3_CGT'] - 2/6) < 1e-9
    finally:
        os.unlink(temp_path)

def test_calculate_kmer_frequencies_with_invalid_bases():
    """Test that invalid bases (N, R, etc.) are filtered out."""
    # Sequence with N: ACGNACGT
    # After cleaning: ACGACGT (length 7)
    # k=3: ACG, GCA, CAC, ACG, CGT -> ACG:2, GCA:1, CAC:1, CGT:1 (total 5)
    fasta_content = """>invalid_bases
    ACGNACGT
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(fasta_content)
        temp_path = f.name
    
    try:
        result = calculate_kmer_frequencies(temp_path)
        
        # Should have filtered k-mers
        assert 'k3_ACG' in result
        # Should not have k-mers containing N
        for key in result:
            assert 'N' not in key, f"Found k-mer with invalid base: {key}"
    finally:
        os.unlink(temp_path)