"""
Unit tests for the data aggregation module (T030).

Tests verify that:
1. Results are correctly collected from the results directory
2. Run counts are accurately calculated per condition
3. SC-004 validation (N ≥ 30) works correctly
4. Aggregation fails appropriately when requirements are not met
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.data_aggregator import (
    load_single_result_file,
    collect_results_from_directory,
    validate_run_counts,
    aggregate_batch_results,
    save_aggregated_results,
    MIN_RUNS_REQUIRED
)


class TestDataAggregator:
    """Test cases for data aggregation functionality."""

    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary directory with mock result files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            
            # Create mock results for 'sequential' condition
            for i in range(35):
                result = {
                    "condition": "sequential",
                    "seed": i,
                    "accuracy": 0.85 + (i * 0.001),
                    "forgetting_rate": 0.05
                }
                with open(results_dir / f"run_sequential_{i}.json", 'w') as f:
                    json.dump(result, f)
            
            # Create mock results for 'mixed' condition
            for i in range(32):
                result = {
                    "condition": "mixed",
                    "seed": i,
                    "accuracy": 0.82 + (i * 0.001),
                    "forgetting_rate": 0.08
                }
                with open(results_dir / f"run_mixed_{i}.json", 'w') as f:
                    json.dump(result, f)
            
            # Create mock results for 'coevolving' condition
            for i in range(33):
                result = {
                    "condition": "coevolving",
                    "seed": i,
                    "accuracy": 0.88 + (i * 0.001),
                    "forgetting_rate": 0.03
                }
                with open(results_dir / f"run_coevolving_{i}.json", 'w') as f:
                    json.dump(result, f)
            
            yield results_dir

    @pytest.fixture
    def temp_insufficient_dir(self):
        """Create a temporary directory with insufficient results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            
            # Only 10 runs for each condition (below SC-004 requirement)
            for condition in ["sequential", "mixed", "coevolving"]:
                for i in range(10):
                    result = {
                        "condition": condition,
                        "seed": i,
                        "accuracy": 0.80,
                        "forgetting_rate": 0.10
                    }
                    with open(results_dir / f"run_{condition}_{i}.json", 'w') as f:
                        json.dump(result, f)
            
            yield results_dir

    @pytest.fixture
    def temp_missing_condition_dir(self):
        """Create a temporary directory with a missing condition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            
            # Only sequential and mixed, missing coevolving
            for condition in ["sequential", "mixed"]:
                for i in range(35):
                    result = {
                        "condition": condition,
                        "seed": i,
                        "accuracy": 0.80,
                        "forgetting_rate": 0.10
                    }
                    with open(results_dir / f"run_{condition}_{i}.json", 'w') as f:
                        json.dump(result, f)
            
            yield results_dir

    @pytest.fixture
    def temp_invalid_json_dir(self):
        """Create a temporary directory with invalid JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)
            
            # Create a valid result
            valid_result = {"condition": "sequential", "seed": 1, "accuracy": 0.9}
            with open(results_dir / "valid.json", 'w') as f:
                json.dump(valid_result, f)
            
            # Create an invalid JSON file
            with open(results_dir / "invalid.json", 'w') as f:
                f.write("not valid json {")
            
            # Create a file missing required fields
            incomplete = {"other_field": "value"}
            with open(results_dir / "incomplete.json", 'w') as f:
                json.dump(incomplete, f)
            
            yield results_dir

    def test_load_single_result_file_valid(self, temp_results_dir):
        """Test loading a valid result file."""
        file_path = temp_results_dir / "run_sequential_0.json"
        data = load_single_result_file(file_path)
        
        assert data is not None
        assert data["condition"] == "sequential"
        assert data["seed"] == 0
        assert "accuracy" in data

    def test_load_single_result_file_missing_file(self):
        """Test loading a non-existent file returns None."""
        file_path = Path("/nonexistent/path/file.json")
        data = load_single_result_file(file_path)
        assert data is None

    def test_load_single_result_file_invalid_json(self, temp_invalid_json_dir):
        """Test loading an invalid JSON file returns None."""
        file_path = temp_invalid_json_dir / "invalid.json"
        data = load_single_result_file(file_path)
        assert data is None

    def test_load_single_result_file_missing_fields(self, temp_invalid_json_dir):
        """Test loading a file with missing required fields returns None."""
        file_path = temp_invalid_json_dir / "incomplete.json"
        data = load_single_result_file(file_path)
        assert data is None

    def test_collect_results_from_directory(self, temp_results_dir):
        """Test collecting all valid results from a directory."""
        results = collect_results_from_directory(temp_results_dir)
        
        # Should have 35 + 32 + 33 = 100 valid results
        assert len(results) == 100
        
        # Verify all have source files
        for r in results:
            assert "_source_file" in r

    def test_collect_results_empty_directory(self):
        """Test collecting from an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = collect_results_from_directory(Path(tmpdir))
            assert len(results) == 0

    def test_collect_results_nonexistent_directory(self):
        """Test collecting from a non-existent directory."""
        results = collect_results_from_directory(Path("/nonexistent/dir"))
        assert len(results) == 0

    def test_validate_run_counts_sufficient(self, temp_results_dir):
        """Test validation when all conditions have sufficient runs."""
        results = collect_results_from_directory(temp_results_dir)
        counts, missing, insufficient = validate_run_counts(results, MIN_RUNS_REQUIRED)
        
        assert counts["sequential"] == 35
        assert counts["mixed"] == 32
        assert counts["coevolving"] == 33
        assert len(missing) == 0
        assert len(insufficient) == 0

    def test_validate_run_counts_insufficient(self, temp_insufficient_dir):
        """Test validation when conditions have insufficient runs."""
        results = collect_results_from_directory(temp_insufficient_dir)
        counts, missing, insufficient = validate_run_counts(results, MIN_RUNS_REQUIRED)
        
        assert counts["sequential"] == 10
        assert counts["mixed"] == 10
        assert counts["coevolving"] == 10
        assert len(missing) == 0
        assert len(insufficient) == 3
        assert set(insufficient) == {"sequential", "mixed", "coevolving"}

    def test_validate_run_counts_missing_condition(self, temp_missing_condition_dir):
        """Test validation when a condition is missing."""
        results = collect_results_from_directory(temp_missing_condition_dir)
        counts, missing, insufficient = validate_run_counts(results, MIN_RUNS_REQUIRED)
        
        assert counts["sequential"] == 35
        assert counts["mixed"] == 35
        assert "coevolving" not in counts
        assert len(missing) == 1
        assert missing[0] == "coevolving"
        assert len(insufficient) == 0

    def test_aggregate_batch_results_success(self, temp_results_dir):
        """Test successful aggregation with sufficient data."""
        result = aggregate_batch_results(temp_results_dir)
        
        assert result.success is True
        assert result.total_runs == 100
        assert len(result.missing_conditions) == 0
        assert len(result.insufficient_conditions) == 0
        assert result.error_message is None

    def test_aggregate_batch_results_insufficient(self, temp_insufficient_dir):
        """Test aggregation fails when data is insufficient."""
        result = aggregate_batch_results(temp_insufficient_dir)
        
        assert result.success is False
        assert result.total_runs == 30
        assert len(result.insufficient_conditions) == 3
        assert result.error_message is not None

    def test_aggregate_batch_results_missing(self, temp_missing_condition_dir):
        """Test aggregation fails when a condition is missing."""
        result = aggregate_batch_results(temp_missing_condition_dir)
        
        assert result.success is False
        assert "coevolving" in result.missing_conditions
        assert result.error_message is not None

    def test_save_aggregated_results(self, temp_results_dir):
        """Test saving aggregated results to a file."""
        agg_result = aggregate_batch_results(temp_results_dir)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "aggregated.json"
            success = save_aggregated_results(agg_result, output_path)
            
            assert success is True
            assert output_path.exists()
            
            # Verify the file content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "summary" in data
            assert data["summary"]["total_runs"] == 100
            assert data["summary"]["sc_004_requirement_met"] is True
            assert "data" in data
            assert len(data["data"]) == 100

    def test_main_execution_success(self, temp_results_dir, capsys):
        """Test the main function execution with success."""
        # We can't easily test sys.exit(0) in pytest without catching SystemExit
        # Instead, we test the logic directly
        result = aggregate_batch_results(temp_results_dir)
        assert result.success is True

    def test_main_execution_failure(self, temp_insufficient_dir, capsys):
        """Test the main function execution with failure."""
        result = aggregate_batch_results(temp_insufficient_dir)
        assert result.success is False

    def test_min_runs_constant(self):
        """Test that the minimum runs constant is set correctly."""
        assert MIN_RUNS_REQUIRED == 30

    def test_aggregation_preserves_all_fields(self, temp_results_dir):
        """Test that aggregation preserves all original fields."""
        results = collect_results_from_directory(temp_results_dir)
        agg_result = aggregate_batch_results(temp_results_dir)
        
        # Check that all original fields are preserved
        for original, aggregated in zip(results, agg_result.aggregated_data):
            assert original["condition"] == aggregated["condition"]
            assert original["seed"] == aggregated["seed"]
            assert original["accuracy"] == aggregated["accuracy"]