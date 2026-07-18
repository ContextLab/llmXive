"""
Contract test for statistical test output format.

This test verifies that the statistical test module (code/screening/statistical_test.py)
produces output conforming to the expected schema defined in the project specifications.

The test checks:
1. The output is a valid JSON-serializable dictionary.
2. Required keys are present: 'test_type', 'statistic', 'p_value', 'alpha', 'conclusion', 'details'.
3. Data types match expectations (e.g., p_value is float, conclusion is string).
4. The 'details' dictionary contains necessary metadata for reproducibility.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from screening.statistical_test import run_mann_whitney_u_test, generate_statistical_report


class TestStatisticalTestOutputFormat:
    """Contract tests for statistical test output structure and content."""

    def test_output_is_dictionary(self):
        """Verify the main output is a dictionary."""
        # Mock data for contract testing
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        assert isinstance(result, dict), "Output must be a dictionary"

    def test_required_top_level_keys_present(self):
        """Verify all required top-level keys are present in the output."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        required_keys = [
            'test_type',
            'statistic',
            'p_value',
            'alpha',
            'conclusion',
            'details'
        ]

        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_data_types_are_correct(self):
        """Verify data types match the contract specification."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        assert isinstance(result['test_type'], str), "test_type must be a string"
        assert isinstance(result['statistic'], (int, float)), "statistic must be numeric"
        assert isinstance(result['p_value'], (int, float)), "p_value must be numeric"
        assert isinstance(result['alpha'], (int, float)), "alpha must be numeric"
        assert isinstance(result['conclusion'], str), "conclusion must be a string"
        assert isinstance(result['details'], dict), "details must be a dictionary"

    def test_details_structure(self):
        """Verify the details dictionary contains required metadata."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        required_detail_keys = [
            'bio_candidate_count',
            'petro_benchmark_count',
            'method',
            'alternative'
        ]

        for key in required_detail_keys:
            assert key in result['details'], f"Missing required detail key: {key}"

    def test_p_value_range(self):
        """Verify p_value is within valid probability range [0, 1]."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        assert 0.0 <= result['p_value'] <= 1.0, "p_value must be between 0 and 1"

    def test_conclusion_logic(self):
        """Verify conclusion string reflects the p_value vs alpha comparison."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        alpha = result['alpha']
        p_value = result['p_value']
        conclusion = result['conclusion'].lower()

        if p_value < alpha:
            assert 'significant' in conclusion or 'reject' in conclusion, \
                "Conclusion should indicate statistical significance when p < alpha"
        else:
            assert 'not significant' in conclusion or 'fail to reject' in conclusion, \
                "Conclusion should indicate lack of significance when p >= alpha"

    def test_json_serializability(self):
        """Verify the entire output can be serialized to JSON."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        try:
            json_str = json.dumps(result)
            parsed = json.loads(json_str)
            assert parsed == result, "JSON round-trip failed"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Output is not JSON serializable: {e}")

    def test_test_type_identifier(self):
        """Verify test_type correctly identifies the statistical method used."""
        bio_scores = [100.5, 110.2, 95.8, 120.1, 105.3]
        petro_scores = [85.0, 90.5, 88.2, 92.1, 87.5]

        result = generate_statistical_report(bio_scores, petro_scores)

        assert 'mann-whitney' in result['test_type'].lower() or 'u-test' in result['test_type'].lower(), \
            "test_type should identify Mann-Whitney U test"