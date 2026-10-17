"""
Tests for the permutation importance analysis (T005).
The test ensures that:
1. ``results/permutation_importance.json`` exists after running the script.
2. All feature columns present in the processed test CSV have an entry
   in the importance JSON.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from config import get_processed_data_dir, get_results_dir

@pytest.fixture(scope="module")
def importance_file():
    """Path to the generated importance JSON."""
    path = Path(get_results_dir()) / "permutation_importance.json"
    if not path.exists():
        pytest.fail(f"Importance file not found at {path}")
    return path

@pytest.fixture(scope="module")
def test_features():
    """Feature columns from the processed test CSV."""
    test_path = Path(get_processed_data_dir()) / "test.csv"
    if not test_path.exists():
        pytest.fail(f"Processed test CSV not found at {test_path}")
    df = pd.read_csv(test_path)
    # Identify target column (same logic as the script)
    target_candidates = ["yield_strength", "ductility"]
    target_cols = [c for c in target_candidates if c in df.columns]
    if not target_cols:
        pytest.fail("No target column found in test CSV.")
    target = target_cols[0]
    return [c for c in df.columns if c != target]

def test_importance_contains_all_features(importance_file, test_features):
    """All features must be present in the importance JSON."""
    with open(importance_file, "r") as f:
        importance = json.load(f)

    missing = set(test_features) - set(importance.keys())
    assert not missing, f"Missing importance entries for features: {missing}"