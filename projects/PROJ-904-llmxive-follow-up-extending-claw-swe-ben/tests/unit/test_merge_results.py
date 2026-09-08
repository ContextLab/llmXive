import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List

# Adjust import based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.merge_results import (
    validate_input_schema,
    validate_strategy_consistency,
    validate_model_sizes,
    MergedResultRow,
    AnalysisError,
    aggregate_jsonl
)

class TestValidateSchema:
    """Tests for the validate_schema function (T008a)."""

    def test_validate_schema_baseline_valid(self):
        """Test that a valid baseline record passes validation."""
        record = {
            "instance_id": "test-001",
            "model_output": "def foo(): pass",
            "status": "passed",
            "strategy": "first_n_lines",
            "model_size": "1B"
        }
        assert validate_input_schema(record, "baseline") is True

    def test_validate_schema_baseline_missing_field(self):
        """Test that a missing required field raises AnalysisError."""
        record = {
            "instance_id": "test-001",
            "model_output": "def foo(): pass",
            # missing 'status', 'strategy', 'model_size'
        }
        with pytest.raises(AnalysisError) as exc_info:
            validate_input_schema(record, "baseline")
        
        assert "missing required fields" in str(exc_info.value)
        assert "status" in str(exc_info.value)

    def test_validate_schema_hf_run_valid(self):
        """Test that a valid HF run record passes validation."""
        record = {
            "instance_id": "test-001",
            "model_output": "def foo(): pass",
            "status": "passed",
            "strategy": "tfidf",
            "model_size": "7B",
            "retrieval_score": 0.85
        }
        assert validate_input_schema(record, "hf_run") is True

    def test_validate_schema_invalid_name(self):
        """Test that an unknown schema name raises AnalysisError."""
        record = {"instance_id": "test"}
        with pytest.raises(AnalysisError) as exc_info:
            validate_input_schema(record, "unknown_schema")
        assert "Unknown schema name" in str(exc_info.value)

class TestValidateStrategyConsistency:
    """Tests for strategy consistency validation."""

    def test_valid_strategies(self):
        records = [
            {"strategy": "first_n_lines"},
            {"strategy": "tfidf"},
            {"strategy": "diff_aware"}
        ]
        validate_strategy_consistency(records, {"first_n_lines", "tfidf", "diff_aware"})

    def test_invalid_strategy(self):
        records = [
            {"strategy": "first_n_lines"},
            {"strategy": "invalid_strategy"}
        ]
        with pytest.raises(AnalysisError) as exc_info:
            validate_strategy_consistency(records, {"first_n_lines", "tfidf"})
        assert "Invalid strategy" in str(exc_info.value)

class TestValidateModelSizes:
    """Tests for model size validation."""

    def test_valid_sizes(self):
        records = [
            {"model_size": "1B"},
            {"model_size": "7B"}
        ]
        validate_model_sizes(records, {"1B", "7B"})

    def test_invalid_size(self):
        records = [
            {"model_size": "13B"}
        ]
        with pytest.raises(AnalysisError) as exc_info:
            validate_model_sizes(records, {"1B", "7B"})
        assert "Invalid model_size" in str(exc_info.value)

class TestMergedResultRow:
    """Tests for the MergedResultRow class."""

    def test_to_dict_all_passed(self):
        baseline = {"status": "passed", "strategy": "first_n_lines", "model_output": "x"}
        hf_1b = {"status": "passed", "strategy": "tfidf", "model_output": "y"}
        hf_7b = {"status": "passed", "strategy": "diff_aware", "model_output": "z"}
        
        row = MergedResultRow("id-1", baseline, hf_1b, hf_7b)
        result = row.to_dict()
        
        assert result["comparison_result"] == "all_passed"
        assert result["instance_id"] == "id-1"

    def test_to_dict_baseline_superior(self):
        baseline = {"status": "passed", "strategy": "first_n_lines", "model_output": "x"}
        hf_1b = {"status": "failed", "strategy": "tfidf", "model_output": ""}
        hf_7b = {"status": "failed", "strategy": "diff_aware", "model_output": ""}
        
        row = MergedResultRow("id-2", baseline, hf_1b, hf_7b)
        result = row.to_dict()
        
        assert result["comparison_result"] == "baseline_superior"

    def test_to_dict_hf_superior(self):
        baseline = {"status": "failed", "strategy": "first_n_lines", "model_output": ""}
        hf_1b = {"status": "passed", "strategy": "tfidf", "model_output": "y"}
        hf_7b = {"status": "failed", "strategy": "diff_aware", "model_output": ""}
        
        row = MergedResultRow("id-3", baseline, hf_1b, hf_7b)
        result = row.to_dict()
        
        assert result["comparison_result"] == "hf_superior"

class TestAggregateJsonl:
    """Integration tests for the aggregate_jsonl function (T008b)."""

    def test_aggregate_jsonl(self):
        """Test that aggregate_jsonl merges files correctly and writes CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create temporary input files
            baseline_path = tmpdir / "baseline.jsonl"
            hf_1b_path = tmpdir / "hf_1b.jsonl"
            hf_7b_path = tmpdir / "hf_7b.jsonl"
            output_path = tmpdir / "results.csv"
            
            # Write sample data
            baseline_data = [
                {"instance_id": "id-1", "status": "passed", "strategy": "first_n_lines", "model_output": "x", "model_size": "1B"},
                {"instance_id": "id-2", "status": "passed", "strategy": "first_n_lines", "model_output": "x", "model_size": "1B"},
                {"instance_id": "id-3", "status": "failed", "strategy": "first_n_lines", "model_output": "", "model_size": "1B"}
            ]
            
            hf_1b_data = [
                {"instance_id": "id-1", "status": "passed", "strategy": "tfidf", "model_output": "y", "model_size": "1B", "retrieval_score": 0.9},
                {"instance_id": "id-2", "status": "failed", "strategy": "tfidf", "model_output": "", "model_size": "1B", "retrieval_score": 0.5},
                {"instance_id": "id-3", "status": "passed", "strategy": "tfidf", "model_output": "y", "model_size": "1B", "retrieval_score": 0.8}
            ]
            
            hf_7b_data = [
                {"instance_id": "id-1", "status": "passed", "strategy": "diff_aware", "model_output": "z", "model_size": "7B", "retrieval_score": 0.9},
                {"instance_id": "id-2", "status": "failed", "strategy": "diff_aware", "model_output": "", "model_size": "7B", "retrieval_score": 0.4},
                {"instance_id": "id-3", "status": "failed", "strategy": "diff_aware", "model_output": "", "model_size": "7B", "retrieval_score": 0.6}
            ]
            
            def write_jsonl(path, data):
                with open(path, 'w') as f:
                    for item in data:
                        f.write(json.dumps(item) + '\n')
            
            write_jsonl(baseline_path, baseline_data)
            write_jsonl(hf_1b_path, hf_1b_data)
            write_jsonl(hf_7b_path, hf_7b_data)
            
            # Run aggregation
            result = aggregate_jsonl(baseline_path, hf_1b_path, hf_7b_path, output_path)
            
            assert result.exists()
            assert result == output_path
            
            # Verify CSV content
            with open(result, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3
            
            # Check specific comparison logic
            # id-1: all passed -> all_passed
            assert rows[0]['instance_id'] == 'id-1'
            assert rows[0]['comparison_result'] == 'all_passed'
            
            # id-2: baseline passed, others failed -> baseline_superior
            assert rows[1]['instance_id'] == 'id-2'
            assert rows[1]['comparison_result'] == 'baseline_superior'
            
            # id-3: baseline failed, hf_1b passed -> hf_superior
            assert rows[2]['instance_id'] == 'id-3'
            assert rows[2]['comparison_result'] == 'hf_superior'

    def test_aggregate_missing_instance(self):
        """Test behavior when an instance is missing in one source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            baseline_path = tmpdir / "baseline.jsonl"
            hf_1b_path = tmpdir / "hf_1b.jsonl"
            hf_7b_path = tmpdir / "hf_7b.jsonl"
            output_path = tmpdir / "results.csv"
            
            # id-1 exists in all
            # id-2 missing in hf_7b
            baseline_data = [
                {"instance_id": "id-1", "status": "passed", "strategy": "first_n_lines", "model_output": "x", "model_size": "1B"},
                {"instance_id": "id-2", "status": "passed", "strategy": "first_n_lines", "model_output": "x", "model_size": "1B"}
            ]
            
            hf_1b_data = [
                {"instance_id": "id-1", "status": "passed", "strategy": "tfidf", "model_output": "y", "model_size": "1B", "retrieval_score": 0.9},
                {"instance_id": "id-2", "status": "passed", "strategy": "tfidf", "model_output": "y", "model_size": "1B", "retrieval_score": 0.9}
            ]
            
            hf_7b_data = [
                {"instance_id": "id-1", "status": "passed", "strategy": "diff_aware", "model_output": "z", "model_size": "7B", "retrieval_score": 0.9}
                # id-2 missing here
            ]
            
            def write_jsonl(path, data):
                with open(path, 'w') as f:
                    for item in data:
                        f.write(json.dumps(item) + '\n')
            
            write_jsonl(baseline_path, baseline_data)
            write_jsonl(hf_1b_path, hf_1b_data)
            write_jsonl(hf_7b_path, hf_7b_data)
            
            # Should succeed but skip id-2
            result = aggregate_jsonl(baseline_path, hf_1b_path, hf_7b_path, output_path)
            
            with open(result, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['instance_id'] == 'id-1'

import csv