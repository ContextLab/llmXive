"""
Unit tests for the descriptor computation module.

The tests cover a few representative molecules:
* Benzene – aromatic ring count should be 1 and the molecule is aromatic.
* 1,3‑Butadiene – conjugation path length should be at least 3.
* Ethanol – a simple non‑aromatic molecule.
"""

import pandas as pd
import pytest

from code.descriptors import compute_all_descriptors

@pytest.fixture
def benzene_df():
    return pd.DataFrame({"smiles": ["c1ccccc1"]})

@pytest.fixture
def butadiene_df():
    return pd.DataFrame({"smiles": ["C=CC=C"]})

@pytest.fixture
def ethanol_df():
    return pd.DataFrame({"smiles": ["CCO"]})

def test_benzene_descriptors(benzene_df):
    result = compute_all_descriptors(benzene_df)
    assert result.iloc[0]["aromatic_ring_count"] == 1
    # Atom count for benzene is 6
    assert result.iloc[0]["atom_count"] == 6

def test_butadiene_conjugation_length(butadiene_df):
    result = compute_all_descriptors(butadiene_df)
    # The conjugated system spans the 4 carbon atoms → path length >= 3
    assert result.iloc[0]["conjugation_path_length"] >= 3

def test_ethanol_descriptors(ethanol_df):
    result = compute_all_descriptors(ethanol_df)
    # No aromatic rings, simple molecule
    assert result.iloc[0]["aromatic_ring_count"] == 0
    assert result.iloc[0]["atom_count"] == 3
