import pytest
from metrics.specialization import compute_specialization_index, validate_specialization_index

def test_specialization_computation():
    idx = compute_specialization_index([1, 2, 2, 3], num_agents=4)
    assert isinstance(idx, int)

def test_validation():
    assert validate_specialization_index(1, num_agents=4)
    assert not validate_specialization_index(5, num_agents=4)
