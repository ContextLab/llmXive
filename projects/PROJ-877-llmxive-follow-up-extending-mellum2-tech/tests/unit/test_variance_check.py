"""
Unit tests for code/analysis/variance_check.py (T011b).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# We will mock the config and logging to avoid dependency on full project setup for unit tests
# However, since the task requires importing from the project, we assume the project structure exists.
# For this unit test, we will test the core logic functions directly.

from code.analysis.variance_check import compute_variance, check_metric_variance, load_annotated_data

class TestComputeVariance:
    def test_empty_list(self):
        assert compute_variance([]) == 0.0

    def test_single_value(self):
        assert compute_variance([5.0]) == 0.0

    def test_two_identical_values(self):
        assert compute_variance([5.0, 5.0]) == 0.0

    def test_two_different_values(self):
        # Variance of [2, 4] -> mean=3, diffs=[-1, 1], sq=[1, 1], var=1.0
        assert compute_variance([2.0, 4.0]) == 1.0

    def test_multiple_values(self):
        # [1, 2, 3, 4, 5] -> mean=3, sq_diffs=[4, 1, 0, 1, 4] -> sum=10, var=2.0
        assert compute_variance([1.0, 2.0, 3.0, 4.0, 5.0]) == 2.0

class TestCheckMetricVariance:
    def test_no_variance_metric(self):
        data = [
            {"metrics": {"cyclomatic_complexity": 5}},
            {"metrics": {"cyclomatic_complexity": 5}},
            {"metrics": {"cyclomatic_complexity": 5}}
        ]
        var, is_null = check_metric_variance(data, "cyclomatic_complexity")
        assert var == 0.0
        assert is_null is True

    def test_has_variance_metric(self):
        data = [
            {"metrics": {"cyclomatic_complexity": 5}},
            {"metrics": {"cyclomatic_complexity": 10}},
            {"metrics": {"cyclomatic_complexity": 15}}
        ]
        var, is_null = check_metric_variance(data, "cyclomatic_complexity")
        assert var > 0.0
        assert is_null is False

    def test_flat_structure_metric(self):
        data = [
            {"cyclomatic_complexity": 2},
            {"cyclomatic_complexity": 4}
        ]
        var, is_null = check_metric_variance(data, "cyclomatic_complexity")
        assert var > 0.0
        assert is_null is False

    def test_missing_metric_key(self):
        data = [
            {"metrics": {"other_metric": 5}},
            {"metrics": {"other_metric": 5}}
        ]
        var, is_null = check_metric_variance(data, "cyclomatic_complexity")
        assert var == 0.0
        assert is_null is True

    def test_mixed_valid_invalid(self):
        data = [
            {"metrics": {"cyclomatic_complexity": 5}},
            {"metrics": {"other": 10}}, # Missing key
            {"metrics": {"cyclomatic_complexity": 5}}
        ]
        var, is_null = check_metric_variance(data, "cyclomatic_complexity")
        assert var == 0.0 # Only two 5s remain
        assert is_null is True

class TestLoadAnnotatedData:
    def test_load_valid_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1, "metrics": {"cc": 5}}\n')
            f.write('{"id": 2, "metrics": {"cc": 10}}\n')
            temp_path = f.name

        try:
            data = load_annotated_data(Path(temp_path))
            assert len(data) == 2
            assert data[0]["id"] == 1
        finally:
            os.unlink(temp_path)

    def test_load_invalid_json_skipped(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            f.write('not json\n')
            f.write('{"id": 2}\n')
            temp_path = f.name

        try:
            data = load_annotated_data(Path(temp_path))
            assert len(data) == 2 # Should skip the invalid line
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        with pytest.raises(Exception): # PipelineError is a subclass of Exception
            load_annotated_data(Path("/nonexistent/file.jsonl"))