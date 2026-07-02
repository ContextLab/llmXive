from metrics.retrieval import compute_retrieval_efficiency
      
def test_retrieval_basic():
    metrics, eff = compute_retrieval_efficiency(5, 10, [0, 1, 2])
    assert 0.0 <= eff <= 1.0
    assert metrics.retrieved == 5

def test_retrieval_zero_total():
    metrics, eff = compute_retrieval_efficiency(0, 0, 3)
    assert eff == 0.0