"""
Verify that the scaffold splitter keeps molecules with the same scaffold
together and that the overall split respects the requested test fraction.
"""

import pandas as pd
from code.split import scaffold_split

def test_scaffold_split_basic():
    # Two molecules sharing the same scaffold (benzene) and one distinct (ethanol)
    df = pd.DataFrame(
        {
            "smiles": ["c1ccccc1", "c1ccccc1", "CCO"],
            "id": [1, 2, 3],
        }
    )
    train_df, test_df = scaffold_split(df, test_fraction=0.33, seed=123)
    # The two benzene entries must be in the same split
    assert (
        (train_df["smiles"] == "c1ccccc1").all()
        or (test_df["smiles"] == "c1ccccc1").all()
    )
    # Exactly one molecule should be in the test set (≈33% of 3)
    assert len(test_df) == 1
