import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.metrics.extract import (
    calculate_sequence_entropy,
    calculate_tool_repetition_frequency,
    calculate_argument_variance,
    extract_metrics_for_trace,
    extract_metrics_from_trace_file,
    process_all_traces,
    MetricExtractionError
)

class TestSequenceEntropy:
    def test_empty_sequence(self):
        assert calculate_sequence_entropy([]) == 0.0

    def test_single_tool(self):
        # Only one unique tool, so probability is 1.0, log(1)=0 -> entropy 0
        assert calculate_sequence_entropy(["tool_a"]) == 0.0

    def test_uniform_distribution(self):
        # Two tools, equal probability -> entropy = 1.0
        sequence = ["tool_a", "tool_b"]
        assert abs(calculate_sequence_entropy(sequence) - 1.0) < 1e-6

    def test_skewed_distribution(self):
        # Three tools, one dominant -> entropy < max
        sequence = ["tool_a", "tool_a", "tool_a", "tool_b", "tool_c"]
        entropy = calculate_sequence_entropy(sequence)
        assert 0.0 < entropy < 1.585  # max for 3 items is log2(3)

class TestToolRepetitionFrequency:
    def test_empty_sequence(self):
        assert calculate_tool_repetition_frequency([]) == 0.0

    def test_no_repetition(self):
        # All unique -> (N - N) / N = 0
        assert calculate_tool_repetition_frequency(["a", "b", "c"]) == 0.0

    def test_all_repetition(self):
        # All same -> (N - 1) / N
        freq = calculate_tool_repetition_frequency(["a", "a", "a"])
        assert abs(freq - (2/3)) < 1e-6

    def test_mixed(self):
        # a, a, b -> (3 - 2) / 3 = 1/3
        freq = calculate_tool_repetition_frequency(["a", "a", "b"])
        assert abs(freq - (1/3)) < 1e-6

class TestArgumentVariance:
    def test_missing_fields(self):
        trace = {"tool_calls": []}
        # Should return 0.0 and log warning
        with patch('code.metrics.extract.logger') as mock_logger:
            result = calculate_argument_variance(trace)
            assert result == 0.0
            # Verify warning was logged
            mock_logger.warning.assert_called()

    def test_insufficient_args(self):
        trace = {
            "tool_calls": [
                {"tool_name": "edit", "arguments": "arg1"}
            ]
        }
        with patch('code.metrics.extract.logger') as mock_logger:
            result = calculate_argument_variance(trace)
            assert result == 0.0

    @patch('code.metrics.extract.SentenceTransformer')
    def test_successful_variance(self, mock_transformer_class):
        mock_model = MagicMock()
        mock_transformer_class.return_value = mock_model
        
        # Mock numpy variance
        import numpy as np
        mock_embeddings = np.array([[1.0, 2.0], [3.0, 4.0]])
        mock_model.encode.return_value = mock_embeddings
        
        trace = {
            "tool_calls": [
                {"tool_name": "edit", "arguments": "arg1"},
                {"tool_name": "edit", "arguments": "arg2"}
            ]
        }
        
        result = calculate_argument_variance(trace)
        assert isinstance(result, float)
        assert result >= 0.0

    @patch('code.metrics.extract.SentenceTransformer')
    def test_import_failure(self, mock_transformer_class):
        mock_transformer_class.side_effect = ImportError("No module 'sentence_transformers'")
        
        trace = {
            "tool_calls": [
                {"tool_name": "edit", "arguments": "arg1"},
                {"tool_name": "edit", "arguments": "arg2"}
            ]
        }
        
        with patch('code.metrics.extract.logger') as mock_logger:
            result = calculate_argument_variance(trace)
            assert result == 0.0
            mock_logger.warning.assert_called()

class TestExtractMetricsForTrace:
    def test_full_extraction(self):
        trace_data = {
            "tool_calls": [
                {"tool_name": "edit", "arguments": "arg1"},
                {"tool_name": "edit", "arguments": "arg2"},
                {"tool_name": "read", "arguments": "arg3"}
            ]
        }
        
        # Mock the variance function to avoid heavy model loading in unit test
        with patch('code.metrics.extract.calculate_argument_variance', return_value=0.5):
            result = extract_metrics_for_trace(trace_data, "test_trace")
            
            assert result["trace_id"] == "test_trace"
            assert "sequence_entropy" in result
            assert "tool_repetition_freq" in result
            assert result["arg_semantic_variance"] == 0.5

class TestExtractMetricsFromFile:
    def test_valid_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"
            data = {
                "trace_id": "from_file",
                "tool_calls": [
                    {"tool_name": "edit", "arguments": "a"},
                    {"tool_name": "edit", "arguments": "b"}
                ]
            }
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            with patch('code.metrics.extract.calculate_argument_variance', return_value=0.1):
                result = extract_metrics_from_trace_file(file_path)
                assert result is not None
                assert result["trace_id"] == "from_file"

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "bad.json"
            with open(file_path, 'w') as f:
                f.write("not valid json")
            
            with patch('code.metrics.extract.logger') as mock_logger:
                result = extract_metrics_from_trace_file(file_path)
                assert result is None
                mock_logger.warning.assert_called()

class TestProcessAllTraces:
    def test_integration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "traces"
            input_dir.mkdir()
            output_file = Path(tmpdir) / "features.csv"
            
            # Create dummy traces
            for i in range(3):
                file_path = input_dir / f"trace_{i}.json"
                data = {
                    "tool_calls": [
                        {"tool_name": "edit", "arguments": f"arg_{i}"}
                    ]
                }
                with open(file_path, 'w') as f:
                    json.dump(data, f)
            
            with patch('code.metrics.extract.calculate_argument_variance', return_value=0.0):
                checksum = process_all_traces([input_dir], output_file)
                
                assert output_file.exists()
                assert len(checksum) == 64  # SHA256 hex length
                
                # Verify CSV content
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) == 4  # header + 3 data rows