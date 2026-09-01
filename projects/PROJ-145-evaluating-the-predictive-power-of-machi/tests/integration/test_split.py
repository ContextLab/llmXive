import pytest
import pandas as pd
from pathlib import Path
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from config import DATA_PROCESSED

def test_no_overlap_between_splits():
    """
    Integration test to verify no overlap between train, holdout, and novel sets.
    """
    # Load the datasets
    train_path = DATA_PROCESSED / 'heas_train.csv'
    holdout_path = DATA_PROCESSED / 'holdout_known.csv'
    novel_path = DATA_PROCESSED / 'true_novel.csv'

    # Check if files exist
    if not train_path.exists() or not holdout_path.exists() or not novel_path.exists():
        pytest.skip("Data files not found. Run data_ingestion.py first.")

    train_df = pd.read_csv(train_path)
    holdout_df = pd.read_csv(holdout_path)
    novel_df = pd.read_csv(novel_path)

    # Get composition sets
    train_comps = set(train_df['composition'].str.strip().str.lower())
    holdout_comps = set(holdout_df['composition'].str.strip().str.lower())
    novel_comps = set(novel_df['composition'].str.strip().str.lower())

    # Check for overlaps
    assert len(train_comps & holdout_comps) == 0, "Overlap between train and holdout sets!"
    assert len(train_comps & novel_comps) == 0, "Overlap between train and novel sets!"
    assert len(holdout_comps & novel_comps) == 0, "Overlap between holdout and novel sets!"

    print("All splits are disjoint. Test passed.")
