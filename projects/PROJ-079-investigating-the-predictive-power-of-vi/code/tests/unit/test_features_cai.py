import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_cai

def test_calculate_cai_valid_fasta():
    """Test CAI calculation with a valid synthetic FASTA file."""
    # Create a synthetic sequence that is optimized for human codons
    # Using codons with high frequency in human table: CTG (L), GCC (A), GGT (G), etc.
    # Sequence: CTG GCC GGT CTG GCC GGT (Leu-Ala-Gly repeated)
    synthetic_seq = "CTGGCCGGTCTGGCCGGT"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_sequence\n")
        f.write(synthetic_seq + "\n")
        temp_path = f.name
    
    try:
        cai = calculate_cai(temp_path)
        # CAI should be high for optimized sequence (close to 1.0)
        assert 0.0 < cai <= 1.0, f"CAI should be between 0 and 1, got {cai}"
        # For a perfectly optimized sequence, it should be very high
        # Note: exact value depends on the normalization in _calculate_adaptation_index
        assert cai > 0.5, f"Optimized sequence should have high CAI, got {cai}"
    finally:
        os.unlink(temp_path)

def test_calculate_cai_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_cai("non_existent_file.fasta")

def test_calculate_cai_empty_sequence():
    """Test CAI calculation with an empty sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">empty_sequence\n")
        f.write("\n")
        temp_path = f.name
    
    try:
        cai = calculate_cai(temp_path)
        # Should return 0.0 for empty or invalid sequence
        assert cai == 0.0, f"Empty sequence should have CAI 0.0, got {cai}"
    finally:
        os.unlink(temp_path)

def test_calculate_cai_short_sequence():
    """Test CAI calculation with a sequence shorter than 3 bases."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">short_sequence\n")
        f.write("AT\n")
        temp_path = f.name
    
    try:
        cai = calculate_cai(temp_path)
        # Should return 0.0 for sequence too short
        assert cai == 0.0, f"Short sequence should have CAI 0.0, got {cai}"
    finally:
        os.unlink(temp_path)

def test_calculate_cai_mixed_case():
    """Test CAI calculation with mixed case sequence."""
    synthetic_seq = "ctgGccgGT"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">mixed_case\n")
        f.write(synthetic_seq + "\n")
        temp_path = f.name
    
    try:
        cai = calculate_cai(temp_path)
        assert 0.0 < cai <= 1.0, f"Mixed case should work, got {cai}"
    finally:
        os.unlink(temp_path)