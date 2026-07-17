"""
Tests for code/utils/metrics.py
"""
import pytest
from code.utils.metrics import calculate_bleu, parse_latency_to_ms, calculate_latency_stats

class TestCalculateBLEU:
    def test_bleu_identical_single_reference(self):
        ref = "The quick brown fox jumps over the lazy dog"
        hyp = "The quick brown fox jumps over the lazy dog"
        score = calculate_bleu(ref, hyp)
        # Identical text should give high BLEU (likely 100.0)
        assert score == 100.0
    
    def test_bleu_different_text(self):
        ref = "The quick brown fox"
        hyp = "A slow black cat"
        score = calculate_bleu(ref, hyp)
        # Completely different should be low
        assert score < 50.0
    
    def test_bleu_multiple_references(self):
        refs = ["The quick brown fox", "A fast brown fox"]
        hyp = "The quick brown fox"
        score = calculate_bleu(refs, hyp)
        assert score == 100.0
    
    def test_bleu_empty_reference_raises(self):
        with pytest.raises(ValueError):
            calculate_bleu("", "hyp")
    
    def test_bleu_empty_hypothesis_raises(self):
        with pytest.raises(ValueError):
            calculate_bleu("ref", "")

class TestParseLatencyToMs:
    def test_parse_integer_seconds(self):
        assert parse_latency_to_ms(2) == 2000
    
    def test_parse_float_seconds(self):
        assert parse_latency_to_ms(1.5) == 1500
    
    def test_parse_integer_large_ms(self):
        # Heuristic: >= 1000 assumed ms
        assert parse_latency_to_ms(1500) == 1500
    
    def test_parse_string_with_s(self):
        assert parse_latency_to_ms("2s") == 2000
        assert parse_latency_to_ms("1.5s") == 1500
    
    def test_parse_string_with_ms(self):
        assert parse_latency_to_ms("1500ms") == 1500
        assert parse_latency_to_ms("500ms") == 500
    
    def test_parse_string_with_min(self):
        assert parse_latency_to_ms("2min") == 120000
        assert parse_latency_to_ms("0.5min") == 30000
    
    def test_parse_string_with_h(self):
        assert parse_latency_to_ms("1h") == 3600000
        assert parse_latency_to_ms("0.5h") == 1800000
    
    def test_parse_string_number_only_small(self):
        # < 1000 assumed seconds
        assert parse_latency_to_ms("2") == 2000
    
    def test_parse_string_number_only_large(self):
        # >= 1000 assumed ms
        assert parse_latency_to_ms("1500") == 1500
    
    def test_parse_invalid_string_raises(self):
        with pytest.raises(ValueError):
            parse_latency_to_ms("abc")
    
    def test_parse_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_latency_to_ms("")
    
    def test_parse_unsupported_type_raises(self):
        with pytest.raises(ValueError):
            parse_latency_to_ms([1, 2, 3])

class TestCalculateLatencyStats:
    def test_stats_empty_list(self):
        stats = calculate_latency_stats([])
        assert stats['count'] == 0
        assert stats['min_ms'] == 0
    
    def test_stats_single_value(self):
        stats = calculate_latency_stats([2])
        assert stats['count'] == 1
        assert stats['min_ms'] == 2000
        assert stats['max_ms'] == 2000
        assert stats['mean_ms'] == 2000
        assert stats['median_ms'] == 2000
    
    def test_stats_multiple_values(self):
        latencies = [1, 2, 3]  # seconds
        stats = calculate_latency_stats(latencies)
        assert stats['count'] == 3
        assert stats['min_ms'] == 1000
        assert stats['max_ms'] == 3000
        assert stats['mean_ms'] == 2000.0
        assert stats['median_ms'] == 2000
    
    def test_stats_with_string_inputs(self):
        latencies = ["1s", "2s", "3s"]
        stats = calculate_latency_stats(latencies)
        assert stats['count'] == 3
        assert stats['min_ms'] == 1000
        assert stats['max_ms'] == 3000
        assert stats['mean_ms'] == 2000.0