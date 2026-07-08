"""
Unit test for the CV strategy integration used by ``code/training/train.py``.

The test creates a synthetic DataFrame with 40 samples (below the 50‑sample
threshold) and verifies that the splitter returned by ``get_cv_splitter``
implements Leave‑One‑Out (i.e., number of folds equals number of samples).
"""

import pandas as pd
import pytest

from training.cv_strategy import get_cv_splitter, ConfigurationError


@pytest.fixture
def tiny_dataset() -> pd.DataFrame:
    # 40 samples, two solvent types to allow stratification attempts.
    data = {
        "index": list(range(40)),
        "solvent": ["water"] * 20 + ["ethanol"] * 20,
    }
    return pd.DataFrame(data)


def test_looo_selected_for_small_dataset(tiny_dataset):
    splitter = get_cv_splitter(tiny_dataset, force_5fold=False)
    # ``LeaveOneOut`` yields exactly N splits.
    folds = list(splitter.split(tiny_dataset))
    assert len(folds) == len(tiny_dataset), "Expected LOO for <50 samples"


def test_force_5fold_raises_on_small_dataset(tiny_dataset):
    with pytest.raises(ConfigurationError):
        # For a dataset with <50 rows forcing 5‑fold is invalid.
        get_cv_splitter(tiny_dataset, force_5fold=True)