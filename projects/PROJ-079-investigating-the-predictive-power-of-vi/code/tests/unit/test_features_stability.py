import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_stability, _translate_dna_to_protein, _calculate_hydrophobicity_score

def test_translate_dna_to_protein():
    """Test basic DNA to protein translation."""
    # ATG (M) - GCT (A) - GCT (A) - TAA (Stop)
    dna = "ATGGCTGCTTAA"
    protein = _translate_dna_to_protein(dna)
    assert protein == "MAA"

def test_translate_dna_to_protein_lowercase():
    """Test translation with lowercase input."""
    dna = "atggctgcttaa"
    protein = _translate_dna_to_protein(dna)
    assert protein == "MAA"

def test_translate_dna_to_protein_with_invalid():
    """Test translation with invalid bases."""
    dna = "ATGXXXGCT"
    protein = _translate_dna_to_protein(dna)
    # Should skip invalid bases
    assert len(protein) >= 1

def test_calculate_hydrophobicity_score():
    """Test hydrophobicity calculation."""
    # All Leucine (L) which has a high hydrophobicity (3.8)
    protein = "LLLLL"
    score = _calculate_hydrophobicity_score(protein)
    assert abs(score - 3.8) < 0.01

def test_calculate_stability_valid_fasta():
    """Test stability calculation with a valid FASTA file."""
    dna_seq = "ATGGCTGCTGCTGCTGCTGCT"  # Encodes MAAAAAA
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_seq\n")
        f.write(dna_seq + "\n")
        temp_path = f.name
    
    try:
        score = calculate_stability(temp_path)
        assert isinstance(score, float)
        # The score should be reasonable (not NaN or inf)
        assert not (score != score)  # Check for NaN
    finally:
        os.unlink(temp_path)

def test_calculate_stability_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_stability("/nonexistent/path.fasta")

def test_calculate_stability_empty_sequence():
    """Test stability calculation with empty sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_seq\n")
        f.write("\n")
        temp_path = f.name
    
    try:
        # Should handle empty sequence gracefully
        score = calculate_stability(temp_path)
        assert score == 0.0
    finally:
        os.unlink(temp_path)

def test_calculate_stability_no_valid_protein():
    """Test stability calculation when translation fails."""
    # Sequence with only stop codons
    dna_seq = "TAATAATAA"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test_seq\n")
        f.write(dna_seq + "\n")
        temp_path = f.name
    
    try:
        # Should return 0.0 and log a warning
        score = calculate_stability(temp_path)
        assert score == 0.0
    finally:
        os.unlink(temp_path)