"""
Unit tests for code/metrics/coverage.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from metrics.coverage import (
    calculate_coverage,
    load_ground_truth_lines,
    load_retrieved_context,
    main
)


class TestCalculateCoverage:
    def test_exact_match(self):
        gt = [1, 2, 3, 4, 5]
        context = [
            {"file_path": "test.py", "line_numbers": [1, 2, 3, 4, 5]}
        ]
        pct, total, found, found_set = calculate_coverage(gt, context)
        assert pct == 100.0
        assert total == 5
        assert found == 5
        assert found_set == {1, 2, 3, 4, 5}

    def test_partial_match(self):
        gt = [1, 2, 3, 4, 5]
        context = [
            {"file_path": "test.py", "line_numbers": [1, 3, 10]}
        ]
        pct, total, found, found_set = calculate_coverage(gt, context)
        assert pct == 40.0  # 2 out of 5
        assert total == 5
        assert found == 2
        assert found_set == {1, 3}

    def test_no_match(self):
        gt = [1, 2, 3]
        context = [
            {"file_path": "test.py", "line_numbers": [10, 20, 30]}
        ]
        pct, total, found, found_set = calculate_coverage(gt, context)
        assert pct == 0.0
        assert found == 0

    def test_empty_ground_truth(self):
        gt = []
        context = [
            {"file_path": "test.py", "line_numbers": [1]}
        ]
        pct, total, found, found_set = calculate_coverage(gt, context)
        assert pct == 0.0
        assert total == 0
        assert found == 0

    def test_multiple_context_entries(self):
        gt = [1, 2, 3, 4]
        context = [
            {"file_path": "test.py", "line_numbers": [1]},
            {"file_path": "test.py", "line_numbers": [2, 3]},
            {"file_path": "other.py", "line_numbers": [4]}
        ]
        pct, total, found, found_set = calculate_coverage(gt, context)
        assert pct == 100.0
        assert found == 4

    def test_target_file_filter(self):
        gt = [1, 2, 3]
        context = [
            {"file_path": "test.py", "line_numbers": [1, 2]},
            {"file_path": "other.py", "line_numbers": [3]}
        ]
        # Without filter
        pct_all, _, found_all, _ = calculate_coverage(gt, context)
        assert found_all == 3

        # With filter
        pct_filtered, _, found_filtered, _ = calculate_coverage(
            gt, context, target_file_path="test.py"
        )
        assert found_filtered == 2
        assert pct_filtered == (2/3)*100


class TestLoadGroundTruth:
    def test_load_valid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"issue_id": 1, "ground_truth_lines": [1, 5, 10]}, f)
            f.flush()
            path = Path(f.name)
            
            lines = load_ground_truth_lines(path)
            assert lines == [1, 5, 10]
            path.unlink()

    def test_load_valid_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"issue_id": 1, "ground_truth_lines": [2, 4, 6]}\n')
            f.flush()
            path = Path(f.name)
            
            lines = load_ground_truth_lines(path)
            assert lines == [2, 4, 6]
            path.unlink()

    def test_missing_key(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"issue_id": 1}, f)
            f.flush()
            path = Path(f.name)
            
            with pytest.raises(ValueError):
                load_ground_truth_lines(path)
            path.unlink()

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_ground_truth_lines(Path("/nonexistent/path.json"))


class TestLoadRetrievedContext:
    def test_load_valid_json(self):
        data = {
            "issue_id": 1,
            "retrieved_context": [
                {"file_path": "test.py", "line_numbers": [1, 2]}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = Path(f.name)
            
            context = load_retrieved_context(path)
            assert len(context) == 1
            assert context[0]["file_path"] == "test.py"
            path.unlink()

    def test_missing_key(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"issue_id": 1}, f)
            f.flush()
            path = Path(f.name)
            
            with pytest.raises(ValueError):
                load_retrieved_context(path)
            path.unlink()