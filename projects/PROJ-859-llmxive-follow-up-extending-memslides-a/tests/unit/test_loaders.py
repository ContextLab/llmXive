"""
Unit tests for data loaders.
"""
import json
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from code.utils.loaders import TraceLoader, MetricsLoader
from code.config import Config


@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory with sample trace files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()
        
        # Create sample trace files
        sample_trace = {
            "trace_id": "test-001",
            "exact_tool_sequence": [
                {"tool_name": "edit", "arguments": {"x": 1}},
                {"tool_name": "slide", "arguments": {"y": 2}}
            ],
            "raw_arg_variance": 0.5,
            "metadata": {"created": "2024-01-01"}
        }
        
        with open(raw_dir / "session_001.json", "w") as f:
            json.dump(sample_trace, f)
        
        with open(raw_dir / "session_002.json", "w") as f:
            json.dump(sample_trace, f)
        
        yield raw_dir


@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory with sample metrics files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        processed_dir.mkdir()
        
        # Create feature_matrix.csv
        with open(processed_dir / "feature_matrix.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["trace_id", "sequence_entropy", "tool_repetition_freq"])
            writer.writeheader()
            writer.writerow({
                "trace_id": "test-001",
                "sequence_entropy": 1.2,
                "tool_repetition_freq": 0.8
            })
        
        # Create per_trace_scores.csv
        with open(processed_dir / "per_trace_scores.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["trace_id", "compressibility_score", "fidelity"])
            writer.writeheader()
            writer.writerow({
                "trace_id": "test-001",
                "compressibility_score": 0.7,
                "fidelity": 0.95
            })
        
        # Create benchmark_results.json
        benchmark_data = {
            "baseline_accuracy": 0.85,
            "compressed_accuracy": 0.82,
            "latency_improvement": 0.4
        }
        with open(processed_dir / "benchmark_results.json", "w") as f:
            json.dump(benchmark_data, f)
        
        yield processed_dir


class TestTraceLoader:
    def test_load_trace(self, temp_raw_dir):
        config = MagicMock()
        config.paths = {"raw": str(temp_raw_dir)}
        loader = TraceLoader(config)
        
        trace = loader.load_trace("session_001.json")
        assert trace["trace_id"] == "test-001"
        assert len(trace["exact_tool_sequence"]) == 2

    def test_load_trace_not_found(self, temp_raw_dir):
        config = MagicMock()
        config.paths = {"raw": str(temp_raw_dir)}
        loader = TraceLoader(config)
        
        with pytest.raises(FileNotFoundError):
            loader.load_trace("nonexistent.json")

    def test_load_all_traces(self, temp_raw_dir):
        config = MagicMock()
        config.paths = {"raw": str(temp_raw_dir)}
        loader = TraceLoader(config)
        
        traces = list(loader.load_all_traces())
        assert len(traces) == 2
        assert all("exact_tool_sequence" in t for t in traces)

    def test_load_trace_ids(self, temp_raw_dir):
        config = MagicMock()
        config.paths = {"raw": str(temp_raw_dir)}
        loader = TraceLoader(config)
        
        ids = loader.load_trace_ids()
        assert len(ids) == 2
        assert "session_001.json" in ids


class TestMetricsLoader:
    def test_load_feature_matrix(self, temp_processed_dir):
        config = MagicMock()
        config.paths = {"processed": str(temp_processed_dir)}
        loader = MetricsLoader(config)
        
        matrix = loader.load_feature_matrix()
        assert len(matrix) == 1
        assert matrix[0]["trace_id"] == "test-001"
        assert float(matrix[0]["sequence_entropy"]) == 1.2

    def test_load_per_trace_scores(self, temp_processed_dir):
        config = MagicMock()
        config.paths = {"processed": str(temp_processed_dir)}
        loader = MetricsLoader(config)
        
        scores = loader.load_per_trace_scores()
        assert len(scores) == 1
        assert float(scores[0]["compressibility_score"]) == 0.7

    def test_load_benchmark_results(self, temp_processed_dir):
        config = MagicMock()
        config.paths = {"processed": str(temp_processed_dir)}
        loader = MetricsLoader(config)
        
        results = loader.load_benchmark_results()
        assert results["baseline_accuracy"] == 0.85
        assert results["compressed_accuracy"] == 0.82

    def test_load_feature_matrix_not_found(self):
        config = MagicMock()
        config.paths = {"processed": "/nonexistent"}
        loader = MetricsLoader(config)
        
        with pytest.raises(FileNotFoundError):
            loader.load_feature_matrix()
