import pytest
from code.utils.metrics import calculate_bleu, parse_latency_to_ms, calculate_latency_stats

class TestCalculateBLEU:
    def test_bleu_identical(self):
        """BLEU should be 100 for identical strings."""
        ref = ["This is a test."]
        cand = "This is a test."
        score = calculate_bleu(ref, cand)
        assert score == 100.0

    def test_bleu_completely_different(self):
        """BLEU should be low for completely different strings."""
        ref = ["The quick brown fox."]
        cand = "lazy dog jumps over."
        score = calculate_bleu(ref, cand)
        assert score >= 0.0
        # It won't necessarily be 0 due to smoothing, but should be low
        assert score < 50.0 

    def test_bleu_empty_candidate(self):
        """Should handle empty candidate gracefully."""
        ref = ["test"]
        score = calculate_bleu(ref, "")
        assert score == 0.0

    def test_bleu_empty_references(self):
        """Should handle empty references gracefully."""
        score = calculate_bleu([], "test")
        assert score == 0.0

class TestParseLatencyToMs:
    def test_parse_ms(self):
        assert parse_latency_to_ms("150 ms") == 150
        assert parse_latency_to_ms("150ms") == 150

    def test_parse_s(self):
        assert parse_latency_to_ms("2 s") == 2000
        assert parse_latency_to_ms("1.5s") == 1500

    def test_parse_min(self):
        assert parse_latency_to_ms("1 min") == 60000
        assert parse_latency_to_ms("0.5 min") == 30000

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            parse_latency_to_ms("invalid")
        with pytest.raises(ValueError):
            parse_latency_to_ms("")

class TestCalculateLatencyStats:
    def test_stats_basic(self):
        data = [100, 200, 300]
        stats = calculate_latency_stats(data)
        assert stats["mean"] == 200.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        # Median of [100, 200, 300] is 200
        assert stats["median"] == 200.0
        # Std dev calculation check
        # mean=200, diffs: -100, 0, 100 -> sq: 10000, 0, 10000 -> sum=20000 -> var=6666.66 -> std=81.649
        assert abs(stats["std"] - 81.649658) < 0.01

    def test_stats_single(self):
        data = [500]
        stats = calculate_latency_stats(data)
        assert stats["mean"] == 500.0
        assert stats["std"] == 0.0

    def test_stats_empty(self):
        stats = calculate_latency_stats([])
        assert stats["mean"] == 0.0
        assert stats["median"] == 0.0