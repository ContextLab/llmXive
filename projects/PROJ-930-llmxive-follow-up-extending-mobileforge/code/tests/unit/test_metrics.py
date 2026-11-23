import pytest
from utils.metrics import SuccessRate, StepEfficiency


class TestSuccessRateCalculator:
    @pytest.mark.parametrize(
        "flags,expected",
        [
            ([], 0.0),
            ([True, True, True], 1.0),
            ([True, False, True, False], 0.5),
            ([False, False], 0.0),
        ],
    )
    def test_compute(self, flags, expected):
        sr = SuccessRate()
        assert sr.compute(flags) == pytest.approx(expected)


class TestStepEfficiencyCalculator:
    @pytest.mark.parametrize(
        "taken,optimal,expected",
        [
            ([], [], 0.0),
            ([5, 10], [5, 10], 1.0),
            ([4, 8], [8, 8], 0.75),
            ([0, 0], [1, 1], 0.0),
        ],
    )
    def test_compute(self, taken, optimal, expected):
        se = StepEfficiency()
        assert se.compute(taken, optimal) == pytest.approx(expected)

    def test_mismatched_lengths(self):
        se = StepEfficiency()
        with pytest.raises(ValueError):
            se.compute([1, 2], [1])