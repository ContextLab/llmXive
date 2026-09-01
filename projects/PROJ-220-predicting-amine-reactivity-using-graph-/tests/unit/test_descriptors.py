"""
Unit tests for src/data/descriptors.py
"""
import pytest
from src.data.descriptors import compute_descriptors, DescriptorVector

def test_compute_descriptors_methyl():
    """Test descriptor computation for Methyl group."""
    smiles = "CC"
    vec = compute_descriptors(smiles)

    assert isinstance(vec, DescriptorVector)
    assert vec.molecular_weight is not None
    assert vec.molar_refractivity is not None
    assert vec.logp is not None

    # Check lookup values
    # Methyl is in the tables
    assert vec.taft_es == 0.00
    assert vec.charton_nu == 1.24
    assert vec.verloop_b1 == 1.52
    assert vec.hammett_sigma == -0.17  # Para

def test_compute_descriptors_phenyl():
    """Test descriptor computation for Phenyl group."""
    smiles = "c1ccccc1"
    vec = compute_descriptors(smiles)

    assert vec.molecular_weight is not None
    assert vec.taft_es is None # Phenyl not in Taft table (usually defined for alkyls)
    assert vec.charton_nu == 2.00
    assert vec.verloop_b1 == 2.00
    assert vec.hammett_sigma == -0.01 # Wait, H is 0.00, Phenyl is often -0.01 or similar in specific contexts,
    # But our table has "C6H5": -0.01? No, we have "C6H5" in CHARTON and VERLOOP.
    # Let's check the mapping logic.
    # In _identify_substituent, we map "c1ccccc1" to "C6H5".
    # In HAMMETT_SIGMA_PARA, "C6H5" is NOT present. So it should be None.
    # This is expected behavior for a lookup table that isn't exhaustive.
    assert vec.hammett_sigma is None

def test_compute_descriptors_invalid_smiles():
    """Test that invalid SMILES raises an error."""
    with pytest.raises(ValueError):
        compute_descriptors("INVALID_SMILES")

def test_compute_descriptors_tbutyl():
    """Test t-Butyl group."""
    smiles = "CC(C)(C)C"
    vec = compute_descriptors(smiles)

    assert vec.taft_es == -0.36
    assert vec.charton_nu == 2.04
    assert vec.verloop_b1 == 2.04
    # Hammett sigma for t-butyl is -0.20 (Para)
    assert vec.hammett_sigma == -0.20

def test_descriptor_vector_to_dict():
    """Test conversion to dictionary."""
    smiles = "CC"
    vec = compute_descriptors(smiles)
    d = vec.to_dict()

    assert "molecular_weight" in d
    assert "taft_es" in d
    assert isinstance(d["taft_es"], float)
