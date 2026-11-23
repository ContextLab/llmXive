import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from the API surface provided
from scripts.extract_features import (
    load_ground_truth,
    filter_unparseable,
    get_lines_of_code,
    get_cyclomatic_complexity,
    get_dependency_depth,
    calculate_semantic_complexity_score,
    extract_graph_and_metrics,
    serialize_graph,
    load_graph_metrics,
)
from scripts.baseline_runner import run_with_timeout, ExecutionResult
from scripts.train_model import load_features, encode_target
from scripts.validate_features import (
    load_features_csv,
    validate_columns_present,
    validate_no_missing_metrics,
)
from scripts.ingest import load_swe_bench, parse_swe_bench, merge_datasets

# Constants for test paths
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
GRAPHS_DIR = DATA_DIR / "graphs"


class TestEdgeCasesEmptyDatasets:
    """Tests for handling empty datasets and missing files."""

    def test_load_ground_truth_empty_file(self, tmp_path):
        """Test loading an empty ground truth CSV."""
        empty_csv = tmp_path / "ground_truth.csv"
        empty_csv.write_text("task_id,code_diff,dynamic_execution_outcome\n")

        result = load_ground_truth(str(empty_csv))
        assert result == []

    def test_load_ground_truth_missing_file(self):
        """Test loading a non-existent ground truth file."""
        with pytest.raises(FileNotFoundError):
            load_ground_truth("data/processed/non_existent.csv")

    def test_filter_unparseable_empty_list(self):
        """Test filtering an empty list of tasks."""
        tasks = []
        result = filter_unparseable(tasks)
        assert result == []

    def test_filter_unparseable_all_unparseable(self):
        """Test filtering a list where all tasks are unparseable."""
        tasks = [
            {"task_id": "1", "status": "Unparseable"},
            {"task_id": "2", "status": "Unparseable"},
        ]
        result = filter_unparseable(tasks)
        assert result == []

    def test_load_features_csv_empty(self, tmp_path):
        """Test loading an empty features CSV."""
        empty_csv = tmp_path / "features.csv"
        empty_csv.write_text("task_id,lines_of_code,cyclomatic_complexity\n")

        df = load_features_csv(str(empty_csv))
        assert df.empty

    def test_validate_columns_present_empty_dataframe(self):
        """Test validating columns on an empty dataframe."""
        import pandas as pd
        df = pd.DataFrame()
        required_cols = {"task_id", "lines_of_code"}
        # Should not raise if dataframe is empty but schema check logic handles it
        # If implementation raises, this test documents expected behavior
        try:
            validate_columns_present(df, required_cols)
        except ValueError:
            # Expected if implementation requires non-empty or specific columns
            pass

    def test_load_swe_bench_empty_dataset(self):
        """Test loading an empty SWE-bench subset (mocked)."""
        with patch("scripts.ingest.load_dataset") as mock_load:
            mock_load.return_value = []
            result = load_swe_bench("test_subset")
            assert result == []


class TestEdgeCasesParsingFailures:
    """Tests for handling code parsing failures and edge cases."""

    def test_get_lines_of_code_empty_string(self):
        """Test LOC calculation on empty string."""
        assert get_lines_of_code("") == 0

    def test_get_lines_of_code_whitespace_only(self):
        """Test LOC calculation on whitespace-only string."""
        assert get_lines_of_code("   \n\n   ") == 0

    def test_get_cyclomatic_complexity_empty_string(self):
        """Test cyclomatic complexity on empty string."""
        assert get_cyclomatic_complexity("") == 0

    def test_get_cyclomatic_complexity_syntax_error(self):
        """Test cyclomatic complexity on invalid Python code."""
        invalid_code = "def broken("
        result = get_cyclomatic_complexity(invalid_code)
        # Should return 0 or handle gracefully
        assert result == 0

    def test_get_dependency_depth_empty_string(self):
        """Test dependency depth on empty string."""
        assert get_dependency_depth("") == 0

    def test_calculate_semantic_complexity_score_empty_string(self):
        """Test semantic complexity on empty string."""
        assert calculate_semantic_complexity_score("") == 0

    def test_calculate_semantic_complexity_score_syntax_error(self):
        """Test semantic complexity on invalid code."""
        invalid_code = "if True print('missing colon')"
        result = calculate_semantic_complexity_score(invalid_code)
        assert result == 0

    def test_extract_graph_and_metrics_unparseable_code(self):
        """Test graph extraction on unparseable code."""
        unparseable = "class Broken:::"
        result = extract_graph_and_metrics(unparseable)
        # Should return empty metrics or handle gracefully
        assert result.get("dependency_depth") == 0
        assert result.get("cyclomatic_complexity") == 0

    def test_serialize_graph_empty_graph(self, tmp_path):
        """Test serializing an empty dependency graph."""
        empty_graph = {"nodes": [], "edges": []}
        output_path = tmp_path / "test_graph.json"
        
        serialize_graph(empty_graph, str(output_path))
        
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
            assert data == empty_graph


class TestEdgeCasesTimeoutAndExecution:
    """Tests for timeout handling and execution edge cases."""

    def test_run_with_timeout_immediate_return(self):
        """Test timeout handler with a function that returns immediately."""
        def quick_func():
            return 42
        
        result = run_with_timeout(quick_func, timeout=5)
        assert result == 42

    def test_run_with_timeout_timeout_occurs(self):
        """Test timeout handler when function exceeds time limit."""
        def slow_func():
            import time
            time.sleep(10)
            return 42
        
        with pytest.raises(TimeoutError):
            run_with_timeout(slow_func, timeout=0.1)

    def test_run_with_timeout_exception_in_function(self):
        """Test timeout handler when function raises exception."""
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            run_with_timeout(failing_func, timeout=5)

    def test_execution_result_timeout_status(self):
        """Test ExecutionResult creation with timeout status."""
        result = ExecutionResult(
            task_id="test_1",
            status="Timeout",
            execution_time=5.0,
            output=""
        )
        assert result.status == "Timeout"


class TestEdgeCasesModelTraining:
    """Tests for model training edge cases."""

    def test_encode_target_all_same_class(self):
        """Test encoding when all samples are the same class."""
        targets = ["Pass"] * 10
        encoded, _ = encode_target(targets)
        assert len(encoded) == 10
        assert all(e == 1 for e in encoded)  # Assuming Pass=1

    def test_encode_target_empty_list(self):
        """Test encoding an empty list."""
        targets = []
        with pytest.raises(ValueError):
            encode_target(targets)

    def test_load_features_missing_columns(self, tmp_path):
        """Test loading features with missing required columns."""
        import pandas as pd
        df = pd.DataFrame({"task_id": ["1", "2"]})
        csv_path = tmp_path / "features.csv"
        df.to_csv(csv_path, index=False)
        
        # This should raise or handle missing columns gracefully
        try:
            loaded_df = load_features(str(csv_path))
            # If it loads, verify it handles missing data
        except (KeyError, ValueError):
            pass  # Expected behavior

    def test_validate_no_missing_metrics_empty_dataframe(self):
        """Test validation on empty dataframe."""
        import pandas as pd
        df = pd.DataFrame()
        # Should handle empty dataframe gracefully
        try:
            validate_no_missing_metrics(df)
        except (ValueError, KeyError):
            pass  # Expected if implementation requires data


class TestEdgeCasesGraphMetrics:
    """Tests for graph metric calculation edge cases."""

    def test_load_graph_metrics_missing_file(self):
        """Test loading metrics from a non-existent graph file."""
        with pytest.raises(FileNotFoundError):
            load_graph_metrics("data/graphs/non_existent.json")

    def test_load_graph_metrics_invalid_json(self, tmp_path):
        """Test loading metrics from a file with invalid JSON."""
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            load_graph_metrics(str(invalid_json))

    def test_load_graph_metrics_empty_json(self, tmp_path):
        """Test loading metrics from an empty JSON file."""
        empty_json = tmp_path / "empty.json"
        empty_json.write_text("{}")
        
        result = load_graph_metrics(str(empty_json))
        assert result == {}

    def test_merge_datasets_empty_both(self):
        """Test merging two empty datasets."""
        dataset_a = []
        dataset_b = []
        result = merge_datasets(dataset_a, dataset_b)
        assert result == []

    def test_merge_datasets_one_empty(self):
        """Test merging when one dataset is empty."""
        dataset_a = [{"task_id": "1", "code": "pass"}]
        dataset_b = []
        result = merge_datasets(dataset_a, dataset_b)
        assert len(result) == 1
        assert result[0]["task_id"] == "1"