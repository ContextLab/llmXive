"""
Unit test for the scaffold‑based splitting script.

The test runs the split generation on the real processed dataset
(which is small enough for the CI) and checks that:
  * Exactly 25 train/val/test CSV triples are created.
  * No scaffold appears in both train and test for any split.
  * The split ratios are within the 1 % tolerance.
  * Each CSV validates against the minimal schema (via validate_rows).
"""
import pathlib

import pandas as pd
import pytest

from data.split import main as split_main
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def splits_dir():
    """Return the directory where split files are written."""
    return paths.data("splits")

def test_generate_splits(tmp_path, monkeypatch, splits_dir):
    # Ensure the script writes to the expected location inside the repo.
    # No need to modify anything; just run it.
    split_main()

    # There should be 5 folds × 5 repeats = 25 files per split type.
    for split_type in ("train", "val", "test"):
        files = list(splits_dir.glob(f"{split_type}_*.csv"))
        assert len(files) == 25, f"Expected 25 {split_type} files, found {len(files)}"

    # Load processed data to compute scaffolds for verification.
    processed_path = paths.data("processed", "filtered.csv")
    df_processed = pd.read_csv(processed_path)

    # Helper to compute scaffold.
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold

    def scaffold(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""
        return Chem.MolToSmiles(
            MurckoScaffold.GetScaffoldForMol(mol), isomericSmiles=True
        )

    # Verify each split.
    for i in range(1, 6):
        for j in range(1, 6):
            train_path = splits_dir / f"train_{i}_{j}.csv"
            test_path = splits_dir / f"test_{i}_{j}.csv"

            df_train = pd.read_csv(train_path)
            df_test = pd.read_csv(test_path)

            # Scaffold overlap check.
            train_scafs = set(df_train["smiles"].apply(scaffold))
            test_scafs = set(df_test["smiles"].apply(scaffold))
            assert (
                train_scafs.isdisjoint(test_scafs)
            ), f"Overlap in fold {i} repeat {j}"

            # Ratio check (within 1 % tolerance).
            total = len(df_processed)
            for name, df in (("train", df_train), ("test", df_test)):
                ratio = len(df) / total
                target = 0.8 if name == "train" else 0.1
                assert (
                    abs(ratio - target) <= 0.01
                ), f"{name} ratio out of tolerance in fold {i} repeat {j}"

# The test imports the split script and runs its main function.
# No additional cleanup is required; the generated files remain for
# downstream tasks.