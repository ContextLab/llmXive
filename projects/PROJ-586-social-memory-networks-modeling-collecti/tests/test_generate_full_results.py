import pytest
from generate_full_results import simulate_one_game

@pytest.mark.parametrize(
    "context,agent_count,expected_spec,expected_ret",
    [
        ("full", 4, pytest.approx(2.0), pytest.approx(0.25)),
        ("limited", 4, pytest.approx(1.6), pytest.approx(0.175)),
    ],
)
def test_simulate_one_game(context, agent_count, expected_spec, expected_ret):
    spec, ret = simulate_one_game(context=context, agent_count=agent_count)
    assert spec == expected_spec
    assert ret == expected_ret