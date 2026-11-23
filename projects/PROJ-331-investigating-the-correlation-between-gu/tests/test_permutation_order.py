"""Additional test to ensure patient‑level temporal order is preserved after permutation.

The existing ``test_permutation.py`` checks CSV creation and p‑value bounds.
This test explicitly verifies that the permutation routine does not disturb the
intra‑patient ordering of ``visit_date``.
"""
from __future__ import annotations

import pandas as pd
import pytest

from code.src.pipeline.permutation import _permute_clinical


@pytest.fixture
def clinical_df():
    """Create a tiny clinical dataframe with two visits per patient."""
    data = [
        {"patient_id": "p1", "visit_date": "2020-01-01", "MDS_UPDRS_Total": 30, "age": 60, "sex": "M", "levodopa_eq_dose": 100},
        {"patient_id": "p1", "visit_date": "2021-01-01", "MDS_UPDRS_Total": 35, "age": 61, "sex": "M", "levodopa_eq_dose": 110},
        {"patient_id": "p2", "visit_date": "2020-01-01", "MDS_UPDRS_Total": 28, "age": 65, "sex": "F", "levodopa_eq_dose": 0},
        {"patient_id": "p2", "visit_date": "2021-01-01", "MDS_UPDRS_Total": 32, "age": 66, "sex": "F", "levodopa_eq_dose": 10},
    ]
    df = pd.DataFrame(data)
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    return df


def test_permutation_preserves_visit_order(clinical_df):
    rng = __import__("numpy").random.default_rng(42)
    permuted = _permute_clinical(clinical_df, rng)

    # For each original patient, collect the sorted visit dates.
    for pid in clinical_df["patient_id"].unique():
        original_dates = clinical_df[clinical_df["patient_id"] == pid]["visit_date"].tolist()
        permuted_dates = permuted[permuted["patient_id"] == pid]["visit_date"].tolist()
        # The set of dates should be identical and in the same order.
        assert original_dates == permuted_dates