import pytest
import math
from benchmark.metrics import calculate_exact_match, calculate_f1_score, compute_mcnemar_test, calculate_latency_stats

class TestExactMatch:
    def test_strings_match(self):
        assert calculate_exact_match("A", "A") is True
        assert calculate_exact_match("A", "a") is True # case insensitive
        assert calculate_exact_match("  A  ", "A") is True

    def test_strings_mismatch(self):
        assert calculate_exact_match("A", "B") is False
        assert calculate_exact_match("A", "B ") is False

    def test_types(self):
        assert calculate_exact_match(1, "1") is True
        assert calculate_exact_match(1, 2) is False

class TestF1Score:
    def test_f1_match(self):
        assert calculate_f1_score("A", "A") == 1.0

    def test_f1_mismatch(self):
        assert calculate_f1_score("A", "B") == 0.0

class TestMcNemar:
    def test_perfect_agreement(self):
        # Both correct or both incorrect in all cases -> b=0, c=0
        results = [
            {'symbolic_pred': 'A', 'vlm_pred': 'A', 'ground_truth': 'A'},
            {'symbolic_pred': 'B', 'vlm_pred': 'B', 'ground_truth': 'C'}
        ]
        chi2, p = compute_mcnemar_test(results)
        assert chi2 == 0.0
        assert p == 1.0

    def test_discordant_pairs(self):
        # b=1 (Sym correct, VLM wrong), c=1 (Sym wrong, VLM correct)
        # Chi2 = (|1-1|-1)^2 / (1+1) = 1/2 = 0.5
        results = [
            {'symbolic_pred': 'A', 'vlm_pred': 'B', 'ground_truth': 'A'}, # b
            {'symbolic_pred': 'B', 'vlm_pred': 'A', 'ground_truth': 'A'}  # c
        ]
        chi2, p = compute_mcnemar_test(results)
        # (0-1)^2 / 2 = 0.5
        assert math.isclose(chi2, 0.5)
        # p-value for chi2=0.5, df=1
        assert 0 < p < 1.0

class TestLatencyStats:
    def test_empty(self):
        stats = calculate_latency_stats([])
        assert stats['median'] == 0.0

    def test_single(self):
        stats = calculate_latency_stats([{'latency_ms': 100}])
        assert stats['median'] == 100.0
        assert stats['mean'] == 100.0

    def test_multiple(self):
        data = [{'latency_ms': 10}, {'latency_ms': 20}, {'latency_ms': 30}]
        stats = calculate_latency_stats(data)
        assert stats['median'] == 20.0
        assert stats['mean'] == 20.0
        assert math.isclose(stats['std'], math.sqrt(((10-20)**2 + (20-20)**2 + (30-20)**2)/3))