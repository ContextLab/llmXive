"""
Integration tests for the refactoring pipeline (User Story 2).

Specifically tests error handling during batch processing to ensure
that a single failed refactoring does not crash the entire batch.
"""
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from llm.pipeline import process_refactoring_batch, load_processed_data, save_results
from llm.refactoring import refactor_single_function
from llm.baseline import generate_identity_baseline
from llm.quality import analyze_function_quality, compute_deltas
from utils.logging import LLMRefactoringError, get_logger
from models.entities import FunctionSample, MetricDelta

logger = get_logger(__name__)


class TestRefactoringBatchErrorHandling:
    """Tests for robust error handling in batch refactoring."""

    @pytest.fixture
    def sample_data(self):
        """Create a list of sample function data for testing."""
        return [
            {
                "code": "def valid_func(x):\n    return x + 1",
                "hash": "abc123",
                "metrics": {"loc": 2, "complexity": 1}
            },
            {
                "code": "def another_valid(y):\n    return y * 2",
                "hash": "def456",
                "metrics": {"loc": 2, "complexity": 1}
            }
        ]

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_batch_processing_handles_single_error(self, sample_data, temp_output_dir):
        """
        Assert that a single failed refactoring does not crash the batch
        and is marked as 'Refactoring Failed'.
        """
        # Mock the refactoring function to fail on the first item
        def mock_refactor(code, hash_val, **kwargs):
            if hash_val == "abc123":
                raise LLMRefactoringError("Simulated API failure")
            return f"refactored_{code}"

        # Mock the baseline generation (should always succeed)
        def mock_baseline(code):
            return code

        # Mock quality analysis to handle the failure case gracefully
        def mock_quality(original, refactored, baseline):
            if refactored is None:
                # Return a delta indicating failure or zero improvement
                return MetricDelta(
                    complexity_delta=0.0,
                    pylint_delta=0.0,
                    maintainability_delta=0.0,
                    status="Refactoring Failed"
                )
            # Normal case
            return MetricDelta(
                complexity_delta=-0.5,
                pylint_delta=-2.0,
                maintainability_delta=1.5,
                status="Success"
            )

        with patch('llm.refactoring.refactor_single_function', side_effect=mock_refactor), \
             patch('llm.baseline.generate_identity_baseline', side_effect=mock_baseline), \
             patch('llm.quality.analyze_function_quality', side_effect=mock_quality):
            
            # Process the batch
            results = process_refactoring_batch(sample_data)

            # Assertions
            assert len(results) == len(sample_data), "All items should be processed"
            
            # First item should be marked as failed
            first_result = results[0]
            assert first_result["status"] == "Refactoring Failed", \
                f"Expected 'Refactoring Failed', got {first_result.get('status')}"
            assert "error_message" in first_result, "Failed item should contain error details"
            
            # Second item should be successful
            second_result = results[1]
            assert second_result["status"] == "Success", \
                f"Expected 'Success', got {second_result.get('status')}"

    def test_batch_processing_handles_multiple_errors(self, sample_data, temp_output_dir):
        """
        Assert that multiple failures in a batch are handled correctly
        without crashing, and all are marked appropriately.
        """
        # Mock to fail on all items
        def mock_refactor_fail(code, hash_val, **kwargs):
            raise LLMRefactoringError("Simulated API failure for all")

        def mock_quality_failure(original, refactored, baseline):
            return MetricDelta(
                complexity_delta=0.0,
                pylint_delta=0.0,
                maintainability_delta=0.0,
                status="Refactoring Failed"
            )

        with patch('llm.refactoring.refactor_single_function', side_effect=mock_refactor_fail), \
             patch('llm.baseline.generate_identity_baseline', side_effect=lambda x: x), \
             patch('llm.quality.analyze_function_quality', side_effect=mock_quality_failure):
            
            results = process_refactoring_batch(sample_data)

            assert len(results) == len(sample_data)
            for result in results:
                assert result["status"] == "Refactoring Failed"
                assert "error_message" in result

    def test_batch_processing_continues_after_syntax_error(self, sample_data, temp_output_dir):
        """
        Assert that syntax errors in LLM output are handled and marked as failed,
        allowing the batch to continue.
        """
        def mock_refactor_syntax_error(code, hash_val, **kwargs):
            if hash_val == "abc123":
                # Return invalid Python code
                return "def invalid(" 
            return f"refactored_{code}"

        def mock_quality_syntax(original, refactored, baseline):
            # Simulate quality check failing on syntax error
            if "invalid" in refactored:
                raise SyntaxError("Invalid syntax in refactored code")
            return MetricDelta(
                complexity_delta=-0.5,
                pylint_delta=-2.0,
                maintainability_delta=1.5,
                status="Success"
            )

        with patch('llm.refactoring.refactor_single_function', side_effect=mock_refactor_syntax_error), \
             patch('llm.baseline.generate_identity_baseline', side_effect=lambda x: x), \
             patch('llm.quality.analyze_function_quality', side_effect=mock_quality_syntax):
            
            results = process_refactoring_batch(sample_data)

            assert len(results) == len(sample_data)
            # First item failed due to syntax error
            assert results[0]["status"] == "Refactoring Failed"
            # Second item succeeded
            assert results[1]["status"] == "Success"

    def test_save_results_on_partial_failure(self, sample_data, temp_output_dir):
        """
        Assert that results can be saved even if some items failed.
        """
        def mock_refactor_partial(code, hash_val, **kwargs):
            if hash_val == "abc123":
                raise LLMRefactoringError("API Error")
            return f"refactored_{code}"

        def mock_quality_partial(original, refactored, baseline):
            if refactored is None or "Failed" in str(refactored):
                return MetricDelta(
                    complexity_delta=0.0,
                    pylint_delta=0.0,
                    maintainability_delta=0.0,
                    status="Refactoring Failed"
                )
            return MetricDelta(
                complexity_delta=-0.5,
                pylint_delta=-2.0,
                maintainability_delta=1.5,
                status="Success"
            )

        output_file = temp_output_dir / "test_results.json"

        with patch('llm.refactoring.refactor_single_function', side_effect=mock_refactor_partial), \
             patch('llm.baseline.generate_identity_baseline', side_effect=lambda x: x), \
             patch('llm.quality.analyze_function_quality', side_effect=mock_quality_partial):
            
            results = process_refactoring_batch(sample_data)
            save_results(results, str(output_file))

            assert output_file.exists(), "Output file should be created"
            
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == len(sample_data)
            # Verify structure of saved data
            for item in saved_data:
                assert "hash" in item
                assert "status" in item
                assert "metrics" in item or "error_message" in item

    def test_empty_batch_handling(self):
        """Assert that an empty batch returns an empty list without error."""
        results = process_refactoring_batch([])
        assert results == []

    def test_non_dict_item_handling(self):
        """Assert that malformed input items are handled gracefully."""
        malformed_data = [
            {"code": "valid", "hash": "1"},
            "not a dict",  # Malformed item
            {"code": "valid2", "hash": "2"}
        ]

        # This should not crash, but might log a warning or skip the item
        # Depending on implementation details of process_refactoring_batch
        # We expect the function to handle this without raising an unhandled exception
        try:
            # Mock dependencies to avoid actual API calls
            with patch('llm.refactoring.refactor_single_function', return_value="refactored"), \
                 patch('llm.baseline.generate_identity_baseline', return_value="baseline"), \
                 patch('llm.quality.analyze_function_quality', return_value=MetricDelta(0,0,0,"Success")):
                
                results = process_refactoring_batch(malformed_data)
                
                # The implementation should ideally skip or mark the malformed item as failed
                # We assert that the process didn't crash and returned a list
                assert isinstance(results, list)
                # At least the valid items should be processed
                assert len(results) >= 2 
        except Exception as e:
            # If the implementation doesn't handle this, it should be a clear error, not a crash
            pytest.fail(f"Batch processing crashed on malformed input: {e}")