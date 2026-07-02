from metrics.specialization import compute_specialization_index
      
def test_specialization_basic():
    idx, metrics = compute_specialization_index([1, 2, 2, 3], num_agents=4)
    assert isinstance(idx, float)
    assert metrics.distinct_agents == 3
    assert metrics.num_agents == 4
      
def test_specialization_no_agents():
    idx, metrics = compute_specialization_index([], num_agents=0)
    assert idx == 0.0