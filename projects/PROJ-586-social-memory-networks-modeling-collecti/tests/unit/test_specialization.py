import pytest
from metrics.specialization import compute_specialization_index as core_compute

from t015_generate_full_results import compute_specialization_index

def test_wrapper_accepts_list():
    agents = [1, 2, 2, 3]
    idx, metrics = compute_specialization_index(agents)
    core_idx, core_metrics = core_compute(agents)
    assert idx == core_idx
    assert metrics == core_metrics

def test_wrapper_legacy_signature():
    # Legacy signature should return just the index (log2 of count)
    idx = compute_specialization_index(5, 0)
    assert idx == pytest.approx(2.321928094887362)  # log2(5)
