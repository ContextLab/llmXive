import pytest
from analysis.anova import compute_two_way_anova, prepare_data_for_anova

def test_prepare_data():
    # Minimal dummy data
    data = [
        {"context_condition": "full", "specialization_index": 2, "retrieval_efficiency": 0.8},
        {"context_condition": "limited", "specialization_index": 1, "retrieval_efficiency": 0.6},
    ]
    df = prepare_data_for_anova(data)
    assert not df.empty
    assert "context_condition" in df.columns

def test_two_way_anova():
    data = [
        {"context_condition": "full", "specialization_index": 2, "retrieval_efficiency": 0.8},
        {"context_condition": "limited", "specialization_index": 1, "retrieval_efficiency": 0.6},
    ]
    result = compute_two_way_anova(data)
    assert result is not None
