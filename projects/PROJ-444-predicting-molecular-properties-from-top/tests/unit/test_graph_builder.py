import pandas as pd
from utils import graph_builder as gb

def test_is_valid_molecule_true():
    smiles = "CCO"  # ethanol, valid
    assert gb.is_valid_molecule(smiles) is True

def test_is_valid_molecule_false():
    smiles = "invalid_smiles"
    assert gb.is_valid_molecule(smiles) is False