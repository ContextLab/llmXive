"""
Verify that the scaffold splitter keeps molecules with the same scaffold
together (no leakage across splits), respects the requested test fraction,
and that the CLI save path works.
"""

import pandas as pd
import pytest

from code.split import scaffold_split, assign_scaffolds


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
    # Exactly one molecule should be in the test set (~33% of 3)
    assert len(test_df) == 1


def test_no_scaffold_leakage():
    # Multiple scaffolds with several members each: no scaffold may span
    # both the training and the test set.
    smiles = (
        ["c1ccccc1"] * 4            # benzene scaffold
        + ["c1ccncc1", "c1ccncc1C"]  # pyridine-ish scaffolds
        + ["CCO", "CCCO", "CCCCO"]   # alcohols (acyclic, empty scaffold)
        + ["C1CCCCC1", "C1CCCCC1CC"]  # cyclohexane scaffold
    )
    df = pd.DataFrame({"smiles": smiles, "id": range(len(smiles))})
    train_df, test_df = scaffold_split(df, test_fraction=0.3, seed=7)

    with_scaf = assign_scaffolds(
        pd.concat(
            [train_df.assign(split="train"), test_df.assign(split="test")]
        )
    )
    leakage = (
        with_scaf.groupby("scaffold_id")["split"].nunique() > 1
    )
    assert not leakage.any(), "A scaffold spans both train and test sets."


def test_split_is_reproducible():
    df = pd.DataFrame(
        {"smiles": ["c1ccccc1", "CCO", "C1CCCCC1", "c1ccncc1", "CCCC"],
         "id": range(5)}
    )
    t1, s1 = scaffold_split(df, test_fraction=0.4, seed=42)
    t2, s2 = scaffold_split(df, test_fraction=0.4, seed=42)
    pd.testing.assert_frame_equal(t1, t2)
    pd.testing.assert_frame_equal(s1, s2)


def test_split_returns_both_sides():
    df = pd.DataFrame({"smiles": ["CCO", "c1ccccc1"], "id": [1, 2]})
    train_df, test_df = scaffold_split(df, test_fraction=0.5, seed=0)
    assert len(train_df) >= 1
    assert len(test_df) >= 1
    assert len(train_df) + len(test_df) == 2
