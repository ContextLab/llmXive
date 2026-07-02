import pytest
from metrics.retrieval import compute_retrieval_efficiency as core_compute

from t015_generate_full_results import compute_retrieval_efficiency

def test_wrapper_full_signature():
    retrieved, total, agents = 3, 5, [1, 2, 3]
    metrics, eff = compute_retrieval_efficiency(retrieved, total, agents)
    core_metrics, core_eff = core_compute(retrieved, total, agents)
    assert metrics == core_metrics
    assert eff == core_eff

def test_wrapper_legacy_signature():
    # Legacy signature returns only efficiency = 1 / agent_count
    eff = compute_retrieval_efficiency(4, 0)
    assert eff == pytest.approx(0.25)