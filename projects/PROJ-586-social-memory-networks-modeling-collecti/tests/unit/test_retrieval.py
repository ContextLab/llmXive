import pytest
from metrics.retrieval import compute_retrieval_efficiency

@pytest.mark.parametrize(
    "correct,total,agents,expected",
    [
        (10, 10, 3, 30.0),   # perfect hits, baseline 1/3 -> efficiency 10/10/(1/3)=3
        (1, 3, 3, 1.0),     # 1/3 divided by 1/3 = 1
        (0, 10, 3, 0.0),    # zero correct hits
    ],
)
def test_retrieval_efficiency_valid(correct, total, agents, expected):
    _, eff = compute_retrieval_efficiency(correct, total, agents)
    assert pytest.approx(eff) == expected

def test_retrieval_efficiency_invalid():
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(-1, 10, 3)
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(5, -1, 3)
    with pytest.raises(ValueError):
        compute_retrieval_efficiency(5, 10, 0)