import pytest
import tempfile
import os
from pathlib import Path
from src.features import calculate_stability, _translate_dna_to_protein, _calculate_hydrophobicity_score

def test_translate_dna_to_protein():
    """Test translation of a simple DNA sequence to protein."""
    dna = "ATGGCCGCCATGGCC"  # Methionine-Alanine-Alanine-Methionine-Alanine
    protein = _translate_dna_to_protein(dna)
    assert protein == "MAAMA"

def test_translate_dna_to_protein_lowercase():
    """Test translation with lowercase DNA."""
    dna = "atggccgccatggcc"
    protein = _translate_dna_to_protein(dna)
    assert protein == "MAAMA"

def test_translate_dna_to_protein_with_invalid():
    """Test translation with invalid bases (should be ignored or handled)."""
    dna = "ATGXXCC"
    # BioPython will handle invalid bases; we expect a warning or partial translation
    # For this test, we just ensure it doesn't crash
    protein = _translate_dna_to_protein(dna)
    assert isinstance(protein, str)

def test_calculate_hydrophobicity_score():
    """Test hydrophobicity score calculation."""
    # Poly-alanine: A has hydrophobicity 1.8
    protein = "AAAAA"
    score = _calculate_hydrophobicity_score(protein)
    assert abs(score - 1.8) < 0.01

def test_calculate_stability_valid_fasta():
    """Test calculate_stability with a valid FASTA file."""
    dna_seq = "ATGGCCGCCATGGCC"  # MAAMA
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\n")
        f.write(dna_seq)
        f.flush()
        
        result = calculate_stability(f.name)
        
        # Check that all expected keys are present
        assert 'aac' in result
        assert 'hydrophobicity_score' in result
        assert 'sasa_total' in result
        assert 'sasa_per_residue' in result
        assert 'hbond_donors' in result
        assert 'hbond_acceptors' in result
        assert 'net_charge' in result
        assert 'charge_density' in result
        assert 'steric_hindrance_avg_volume' in result
        
        # Check types
        assert isinstance(result['aac'], dict)
        assert isinstance(result['hydrophobicity_score'], float)
        assert isinstance(result['sasa_total'], float)
        assert isinstance(result['sasa_per_residue'], float)
        assert isinstance(result['hbond_donors'], int)
        assert isinstance(result['hbond_acceptors'], int)
        assert isinstance(result['net_charge'], float)
        assert isinstance(result['charge_density'], float)
        assert isinstance(result['steric_hindrance_avg_volume'], float)
        
        os.unlink(f.name)

def test_calculate_stability_file_not_found():
    """Test calculate_stability with a non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_stability("non_existent.fasta")

def test_calculate_stability_empty_sequence():
    """Test calculate_stability with an empty sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\n")
        f.write("")
        f.flush()
        
        with pytest.raises(ValueError):
            calculate_stability(f.name)
        
        os.unlink(f.name)

def test_calculate_stability_no_valid_protein():
    """Test calculate_stability when translation fails."""
    # Sequence that doesn't translate to a valid protein (e.g., too short or no start codon)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">test\n")
        f.write("ATG")  # Only start codon, no stop
        f.flush()
        
        # This should raise an error because the protein is too short or empty
        with pytest.raises(ValueError):
            calculate_stability(f.name)
        
        os.unlink(f.name)