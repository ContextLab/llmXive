import numpy as np
import pandas as pd
import pytest

from code.data.extract_2d_descriptors import generate_2d_descriptors

@pytest.mark.parametrize(
    "smiles,expected_atoms",
    [
        ("O", 3),   # water: O + 2 H
        ("C", 5),   # methane: C + 4 H
    ],
)
def test_generate_2d_descriptors_basic(smiles, expected_atoms):
    """Check that fingerprint and Coulomb matrix are generated with correct shapes."""
    df = pd.DataFrame({"smiles": [smiles]})
    out_df = generate_2d_descriptors(df)

    # One row should be returned
    assert len(out_df) == 1

    # Fingerprint should be a numpy array of length 2048
    fp = out_df.iloc[0]["fingerprint"]
    assert isinstance(fp, np.ndarray)
    assert fp.shape == (2048,)

    # Coulomb matrix should be square with size equal to number of atoms (including H)
    cm = out_df.iloc[0]["coulomb_matrix"]
    assert isinstance(cm, np.ndarray)
    assert cm.shape == (expected_atoms, expected_atoms)
