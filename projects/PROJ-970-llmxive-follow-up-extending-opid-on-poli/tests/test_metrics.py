import pytest
from typing import List, Dict, Any
from utils.metrics import (
    calculate_success_rate,
    calculate_raw_entropy,
    calculate_mean_entropy,
    calculate_variance,
    calculate_mean_log_prob_shift,
    calculate_distillation_cost_benefit_ratio
)

class TestMeanLogProbShift:
    def test_empty_logs(self):
        assert calculate_mean_log_prob_shift([]) == 0.0

    def test_single_entry(self):
        logs = [{"tier": "Tier1", "threshold": 0.5, "log_prob_shift": 0.8}]
        assert calculate_mean_log_prob_shift(logs, tier="Tier1", threshold=0.5) == 0.8

    def test_multiple_entries_filter_by_tier(self):
        logs = [
            {"tier": "Tier1", "threshold": 0.5, "log_prob_shift": 0.8},
            {"tier": "Tier2", "threshold": 0.5, "log_prob_shift": 1.2},
            {"tier": "Tier1", "threshold": 0.5, "log_prob_shift": 0.4}
        ]
        # Filter for Tier1 only: (0.8 + 0.4) / 2 = 0.6
        result = calculate_mean_log_prob_shift(logs, tier="Tier1", threshold=0.5)
        assert result == 0.6

    def test_multiple_entries_filter_by_threshold(self):
        logs = [
            {"tier": "Tier1", "threshold": 0.5, "log_prob_shift": 0.8},
            {"tier": "Tier1", "threshold": 0.8, "log_prob_shift": 1.0},
            {"tier": "Tier1", "threshold": 0.5, "log_prob_shift": 0.2}
        ]
        # Filter for threshold 0.5: (0.8 + 0.2) / 2 = 0.5
        result = calculate_mean_log_prob_shift(logs, tier="Tier1", threshold=0.5)
        assert result == 0.5

    def test_no_matching_filters(self):
        logs = [
            {"tier": "Tier1", "threshold": 0.5, "log_prob_shift": 0.8},
            {"tier": "Tier2", "threshold": 0.5, "log_prob_shift": 1.2}
        ]
        # Filter for Tier3: no matches
        result = calculate_mean_log_prob_shift(logs, tier="Tier3", threshold=0.5)
        assert result == 0.0

    def test_missing_key_raises(self):
        logs = [{"tier": "Tier1", "threshold": 0.5}] # Missing log_prob_shift
        with pytest.raises(ValueError):
            calculate_mean_log_prob_shift(logs, tier="Tier1", threshold=0.5)

class TestDistillationCostBenefitRatio:
    def test_normal_case(self):
        # Shift = 10.0, Improvement = 0.5 -> Ratio = 20.0
        ratio = calculate_distillation_cost_benefit_ratio(10.0, 0.5)
        assert ratio == 20.0

    def test_zero_improvement(self):
        # Should return 0.0 to avoid division by zero
        ratio = calculate_distillation_cost_benefit_ratio(10.0, 0.0)
        assert ratio == 0.0

    def test_negative_improvement(self):
        # Negative improvement (worsening) should still calculate
        ratio = calculate_distillation_cost_benefit_ratio(10.0, -0.5)
        assert ratio == -20.0