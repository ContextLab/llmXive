"""
Contract test for benchmark results schema.

This test validates that the output of code/evaluation/benchmark.py
conforms strictly to contracts/benchmark_results.schema.yaml.

It ensures that for every trace in the held-out set, the benchmark
results contain:
- trace_id (string)
- baseline_metrics: { edit_accuracy, retrieval_latency, latency_std_dev, latency_p95 }
- compressed_metrics: { edit_accuracy, retrieval_latency, latency_std_dev, latency_p95 }
- delta_metrics: { edit_accuracy_difference, fidelity_loss }

The test loads the actual generated artifact (data/processed/benchmark_results.json)
and validates it against the schema definition.
"""

import json
import os
import pytest
from pathlib import Path

# Import the schema validator from the project's utility layer
# Based on the API surface, utils.validators contains BenchmarkValidator
from utils.validators import BenchmarkValidator

# Import the config to get paths
from config import get_config

class TestBenchmarkResultsSchema:
    """Contract tests for benchmark_results.json schema compliance."""

    @pytest.fixture
    def config(self):
        """Load project configuration."""
        return get_config()

    @pytest.fixture
    def schema_path(self, config):
        """Path to the benchmark results schema."""
        return Path(config.PROJECT_ROOT) / "contracts" / "benchmark_results.schema.yaml"

    @pytest.fixture
    def results_path(self, config):
        """Path to the generated benchmark results."""
        return Path(config.PROJECT_ROOT) / "data" / "processed" / "benchmark_results.json"

    def test_schema_file_exists(self, schema_path):
        """Verify the schema definition file exists."""
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_results_file_exists(self, results_path):
        """Verify the benchmark results file was generated."""
        assert results_path.exists(), (
            f"Benchmark results file not found: {results_path}. "
            "Ensure code/evaluation/benchmark.py has been executed successfully."
        )

    def test_results_is_valid_json(self, results_path):
        """Verify the results file is valid JSON."""
        try:
            with open(results_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"benchmark_results.json is not valid JSON: {e}")

    def test_results_conforms_to_schema(self, schema_path, results_path):
        """
        Validate the benchmark results structure against the schema.
        
        Uses the project's BenchmarkValidator to ensure:
        1. Top-level structure matches the schema.
        2. Every trace entry has required metrics.
        3. Numeric fields are within expected ranges (e.g., accuracy in [0,1]).
        """
        validator = BenchmarkValidator(schema_path=str(schema_path))
        
        with open(results_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)

        # Run validation
        is_valid, errors = validator.validate(results_data)
        
        if not is_valid:
            error_details = "\n".join(errors)
            pytest.fail(f"Benchmark results do not conform to schema:\n{error_details}")

    def test_required_fields_present(self, results_path):
        """
        Explicit check for the specific fields required by the research pipeline.
        
        This complements the schema validation by checking for the exact
        metric names defined in T032b and T062.
        """
        with open(results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure it's a list of trace results
        assert isinstance(data, list), "Root element must be a list of trace results"
        assert len(data) > 0, "Results list cannot be empty"

        required_fields = [
            "trace_id",
            "baseline_metrics",
            "compressed_metrics",
            "delta_metrics"
        ]

        baseline_fields = ["edit_accuracy", "retrieval_latency", "latency_std_dev", "latency_p95"]
        compressed_fields = ["edit_accuracy", "retrieval_latency", "latency_std_dev", "latency_p95"]
        delta_fields = ["edit_accuracy_difference", "fidelity_loss"]

        for i, entry in enumerate(data):
            # Check top-level fields
            for field in required_fields:
                assert field in entry, f"Missing '{field}' in entry {i}"
            
            # Check baseline metrics
            for field in baseline_fields:
                assert field in entry["baseline_metrics"], f"Missing '{field}' in baseline_metrics (entry {i})"
                assert isinstance(entry["baseline_metrics"][field], (int, float)), f"'{field}' must be numeric"
            
            # Check compressed metrics
            for field in compressed_fields:
                assert field in entry["compressed_metrics"], f"Missing '{field}' in compressed_metrics (entry {i})"
                assert isinstance(entry["compressed_metrics"][field], (int, float)), f"'{field}' must be numeric"
            
            # Check delta metrics
            for field in delta_fields:
                assert field in entry["delta_metrics"], f"Missing '{field}' in delta_metrics (entry {i})"
                assert isinstance(entry["delta_metrics"][field], (int, float)), f"'{field}' must be numeric"

    def test_accuracy_ranges(self, results_path):
        """Verify accuracy metrics are within valid probability range [0, 1]."""
        with open(results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, entry in enumerate(data):
            # Baseline accuracy
            base_acc = entry["baseline_metrics"]["edit_accuracy"]
            assert 0.0 <= base_acc <= 1.0, f"Baseline accuracy out of range [{base_acc}] in entry {i}"

            # Compressed accuracy
            comp_acc = entry["compressed_metrics"]["edit_accuracy"]
            assert 0.0 <= comp_acc <= 1.0, f"Compressed accuracy out of range [{comp_acc}] in entry {i}"

            # Fidelity loss (should be 1 - compressed_acc, so also in [0, 1])
            fid_loss = entry["delta_metrics"]["fidelity_loss"]
            assert 0.0 <= fid_loss <= 1.0, f"Fidelity loss out of range [{fid_loss}] in entry {i}"

    def test_latency_non_negative(self, results_path):
        """Verify latency metrics are non-negative."""
        with open(results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for i, entry in enumerate(data):
            for key in ["baseline_metrics", "compressed_metrics"]:
                latency = entry[key]["retrieval_latency"]
                assert latency >= 0.0, f"Negative latency [{latency}] found in {key} (entry {i})"
                
                std_dev = entry[key]["latency_std_dev"]
                assert std_dev >= 0.0, f"Negative std_dev [{std_dev}] found in {key} (entry {i})"
                
                p95 = entry[key]["latency_p95"]
                assert p95 >= 0.0, f"Negative p95 [{p95}] found in {key} (entry {i})"