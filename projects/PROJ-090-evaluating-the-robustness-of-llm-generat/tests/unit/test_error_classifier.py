"""
Unit tests for the error classifier module (T035).

These tests verify:
1. Stratified sampling logic
2. Error classification (syntax vs logic)
3. Report generation structure
"""
import json
import random
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.error_classifier import (
    filter_failures,
    stratify_by_perturbation_type,
    sample_stratified,
    classify_error,
    create_error_classification_report
)
from model.execution_results import ExecutionTag


class TestFilterFailures:
    """Tests for filter_failures function."""
    
    def test_filter_passes_and_fails(self):
        """Test that only failures are returned."""
        results = [
            {"task_id": "1", "tag": ExecutionTag.PASS.value, "error_message": ""},
            {"task_id": "2", "tag": ExecutionTag.SYNTAX_ERROR.value, "error_message": "SyntaxError"},
            {"task_id": "3", "tag": ExecutionTag.TIMEOUT.value, "error_message": "Timeout"},
            {"task_id": "4", "tag": ExecutionTag.PASS.value, "error_message": ""},
        ]
        
        failures = filter_failures(results)
        
        assert len(failures) == 2
        assert failures[0]["task_id"] == "2"
        assert failures[1]["task_id"] == "3"
    
    def test_empty_list(self):
        """Test with empty input."""
        failures = filter_failures([])
        assert failures == []
    
    def test_all_passes(self):
        """Test when all results pass."""
        results = [
            {"task_id": "1", "tag": ExecutionTag.PASS.value},
            {"task_id": "2", "tag": ExecutionTag.PASS.value},
        ]
        failures = filter_failures(results)
        assert failures == []


class TestStratifyByPerturbationType:
    """Tests for stratify_by_perturbation_type function."""
    
    def test_stratification(self):
        """Test that failures are correctly grouped by type."""
        failures = [
            {"task_id": "1", "perturbation_type": "synonym", "tag": "syntax"},
            {"task_id": "2", "perturbation_type": "typo", "tag": "syntax"},
            {"task_id": "3", "perturbation_type": "synonym", "tag": "timeout"},
            {"task_id": "4", "perturbation_type": "rephrase", "tag": "fail"},
        ]
        
        stratified = stratify_by_perturbation_type(failures)
        
        assert len(stratified) == 3
        assert len(stratified["synonym"]) == 2
        assert len(stratified["typo"]) == 1
        assert len(stratified["rephrase"]) == 1
    
    def test_unknown_type(self):
        """Test handling of missing perturbation_type."""
        failures = [
            {"task_id": "1", "tag": "syntax"},  # No perturbation_type
            {"task_id": "2", "perturbation_type": "typo", "tag": "syntax"},
        ]
        
        stratified = stratify_by_perturbation_type(failures)
        
        assert "unknown" in stratified
        assert len(stratified["unknown"]) == 1


class TestSampleStratified:
    """Tests for sample_stratified function."""
    
    def test_sample_smaller_than_total(self):
        """Test sampling when total > max_sample_size."""
        # Create stratified data with 100 items across 2 types
        stratified = {
            "type1": [{"id": i} for i in range(50)],
            "type2": [{"id": i} for i in range(50, 100)],
        }
        
        sample = sample_stratified(stratified, max_sample_size=20, seed=42)
        
        assert len(sample) == 20
        # Verify we got items from both types
        type_ids = [item["id"] for item in sample]
        assert any(id_ < 50 for id_ in type_ids)  # From type1
        assert any(id_ >= 50 for id_ in type_ids)  # From type2
    
    def test_sample_larger_than_total(self):
        """Test when total <= max_sample_size (should return all)."""
        stratified = {
            "type1": [{"id": i} for i in range(10)],
            "type2": [{"id": i} for i in range(10, 15)],
        }
        
        sample = sample_stratified(stratified, max_sample_size=50, seed=42)
        
        assert len(sample) == 15  # All items
    
    def test_empty_input(self):
        """Test with empty stratified data."""
        sample = sample_stratified({}, max_sample_size=10, seed=42)
        assert sample == []
    
    def test_deterministic_with_seed(self):
        """Test that same seed produces same result."""
        stratified = {
            "type1": [{"id": i} for i in range(100)],
            "type2": [{"id": i} for i in range(100, 200)],
        }
        
        sample1 = sample_stratified(stratified, max_sample_size=10, seed=42)
        sample2 = sample_stratified(stratified, max_sample_size=10, seed=42)
        
        assert sample1 == sample2


class TestClassifyError:
    """Tests for classify_error function."""
    
    def test_syntax_error_detection(self):
        """Test detection of syntax errors."""
        test_cases = [
            {"error_message": "SyntaxError: invalid syntax", "tag": "syntax_error"},
            {"error_message": "IndentationError: unexpected indent", "tag": ""},
            {"error_message": "NameError: name 'x' is not defined", "tag": ""},
            {"error_message": "ModuleNotFoundError: No module named 'foo'", "tag": ""},
        ]
        
        for case in test_cases:
            result = classify_error(case)
            assert result == "syntax", f"Failed for {case}"
    
    def test_logic_error_detection(self):
        """Test detection of logic errors."""
        test_cases = [
            {"error_message": "AssertionError: expected True but got False", "tag": "fail"},
            {"error_message": "ValueError: invalid literal", "tag": ""},
            {"error_message": "Timeout exceeded", "tag": "timeout"},
            {"error_message": "Output mismatch", "tag": "fail"},
        ]
        
        for case in test_cases:
            result = classify_error(case)
            assert result == "logic", f"Failed for {case}"
    
    def test_default_to_logic(self):
        """Test that unknown errors default to logic."""
        case = {"error_message": "Some unknown error", "tag": "unknown"}
        result = classify_error(case)
        assert result == "logic"


class TestCreateErrorClassificationReport:
    """Tests for create_error_classification_report function."""
    
    def test_report_structure(self):
        """Test that report has correct structure."""
        sampled_failures = [
            {
                "task_id": "test1",
                "perturbation_type": "synonym",
                "tag": "syntax_error",
                "error_message": "SyntaxError: invalid syntax"
            },
            {
                "task_id": "test2",
                "perturbation_type": "typo",
                "tag": "fail",
                "error_message": "AssertionError"
            }
        ]
        
        report = create_error_classification_report(sampled_failures)
        
        assert len(report) == 2
        assert all("task_id" in item for item in report)
        assert all("perturbation_type" in item for item in report)
        assert all("classification" in item for item in report)
        assert all("original_tag" in item for item in report)
        assert all("error_message" in item for item in report)
        assert all("sample_index" in item for item in report)
    
    def test_classification_values(self):
        """Test that classifications are valid."""
        sampled_failures = [
            {"task_id": "1", "perturbation_type": "synonym", "tag": "syntax_error", "error_message": "SyntaxError"},
            {"task_id": "2", "perturbation_type": "typo", "tag": "fail", "error_message": "AssertionError"},
        ]
        
        report = create_error_classification_report(sampled_failures)
        
        classifications = [item["classification"] for item in report]
        assert all(c in ["syntax", "logic"] for c in classifications)


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    @patch('analysis.error_classifier.load_execution_results')
    def test_full_pipeline(self, mock_load):
        """Test the full pipeline from loading to report generation."""
        # Mock execution results
        mock_results = [
            {"task_id": "1", "tag": ExecutionTag.PASS.value, "perturbation_type": "synonym"},
            {"task_id": "2", "tag": ExecutionTag.SYNTAX_ERROR.value, "perturbation_type": "synonym", "error_message": "SyntaxError"},
            {"task_id": "3", "tag": ExecutionTag.TIMEOUT.value, "perturbation_type": "typo", "error_message": "Timeout"},
            {"task_id": "4", "tag": ExecutionTag.PASS.value, "perturbation_type": "rephrase"},
            {"task_id": "5", "tag": ExecutionTag.FAILED.value, "perturbation_type": "typo", "error_message": "AssertionError"},
        ]
        
        mock_load.return_value = mock_results
        
        # Run the pipeline components
        failures = filter_failures(mock_results)
        assert len(failures) == 3
        
        stratified = stratify_by_perturbation_type(failures)
        assert len(stratified) == 2  # synonym and typo
        
        sampled = sample_stratified(stratified, max_sample_size=2, seed=42)
        assert len(sampled) <= 2
        
        report = create_error_classification_report(sampled)
        assert len(report) == len(sampled)
        assert all("perturbation_type" in item for item in report)
        assert all("classification" in item for item in report)