import pytest
import json
import math
from pathlib import Path
import tempfile
import sys
from collections import Counter

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code.metrics.extract import (
    calculate_sequence_entropy,
    calculate_tool_repetition_frequency,
    calculate_argument_variance,
    extract_metrics_for_trace,
    extract_metrics_from_trace_file
)

class TestSequenceEntropy:
    def test_empty_sequence(self):
        assert calculate_sequence_entropy([]) == 0.0

    def test_single_element(self):
        # Only one unique element, probability = 1, entropy = 0
        assert calculate_sequence_entropy(["tool_a"]) == 0.0

    def test_uniform_distribution(self):
        # Two tools, each appearing once: p=0.5, entropy = -2 * 0.5 * log2(0.5) = 1.0
        seq = ["tool_a", "tool_b"]
        entropy = calculate_sequence_entropy(seq)
        assert math.isclose(entropy, 1.0, rel_tol=1e-9)

    def test_repeated_elements(self):
        # tool_a appears 3 times, tool_b 1 time. Total 4.
        # p(a)=0.75, p(b)=0.25
        # H = - (0.75*log2(0.75) + 0.25*log2(0.25))
        seq = ["tool_a", "tool_a", "tool_a", "tool_b"]
        entropy = calculate_sequence_entropy(seq)
        expected = - (0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        assert math.isclose(entropy, expected, rel_tol=1e-9)

class TestToolRepetitionFrequency:
    def test_empty_sequence(self):
        assert calculate_tool_repetition_frequency([]) == 0.0

    def test_all_unique(self):
        # All unique: (4 - 4) / 4 = 0
        assert calculate_tool_repetition_frequency(["a", "b", "c", "d"]) == 0.0

    def test_all_same(self):
        # All same: (4 - 1) / 4 = 0.75
        assert calculate_tool_repetition_frequency(["a", "a", "a", "a"]) == 0.75

    def test_mixed(self):
        # a, a, b, c -> 4 total, 3 unique -> (4-3)/4 = 0.25
        assert calculate_tool_repetition_frequency(["a", "a", "b", "c"]) == 0.25

class TestArgumentVariance:
    def test_empty_arguments(self):
        assert calculate_argument_variance([]) == 0.0

    def test_single_argument(self):
        assert calculate_argument_variance(["only one"]) == 0.0

    def test_identical_arguments(self):
        # Identical embeddings -> cosine distance = 0 -> mean = 0
        # Note: This test might be slow due to model loading, so we mock or skip if needed
        # For now, we assume the model handles identical strings correctly
        result = calculate_argument_variance(["same", "same"])
        assert result == 0.0 or result < 0.01 # Allow small float error

    def test_different_arguments(self):
        # Different strings should have non-zero distance
        result = calculate_argument_variance(["hello world", "goodbye world"])
        assert result > 0.0

class TestExtractMetricsForTrace:
    def test_basic_extraction(self):
        trace = {
            "trace_id": "test_1",
            "exact_tool_sequence": ["read", "write", "read"],
            "arguments": ["arg1", "arg2"]
        }
        metrics = extract_metrics_for_trace(trace)
        
        assert "sequence_entropy" in metrics
        assert "tool_repetition_frequency" in metrics
        assert "argument_semantic_variance" in metrics
        assert "trace_length" in metrics
        assert metrics["trace_length"] == 3
        assert metrics["tool_repetition_frequency"] > 0.0 # "read" repeats

    def test_missing_arguments(self):
        trace = {
            "trace_id": "test_2",
            "exact_tool_sequence": ["tool_a"]
        }
        metrics = extract_metrics_for_trace(trace)
        assert metrics["argument_semantic_variance"] == 0.0

class TestExtractMetricsFromTraceFile:
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "trace_id": "file_test",
                "exact_tool_sequence": ["tool_a", "tool_b"],
                "arguments": ["arg_a", "arg_b"]
            }, f)
            temp_path = Path(f.name)

        try:
            result = extract_metrics_from_trace_file(temp_path)
            assert result is not None
            assert result["trace_id"] == "file_test"
            assert "sequence_entropy" in result
        finally:
            temp_path.unlink()

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        try:
            result = extract_metrics_from_trace_file(temp_path)
            assert result is None
        finally:
            temp_path.unlink()
