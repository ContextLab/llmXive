"""
Unit tests for the Causal Framing Validator in code/analysis/report.py.

This test suite verifies that the report generation pipeline correctly
enforces the 'Associational Framing' constraint (FR-010) by raising
a RuntimeError when causal keywords are detected in the generated text.

Dependencies:
- T032: Implementation of the validation step in code/analysis/report.py
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.report import generate_executive_summary, generate_detailed_results, generate_report
from utils.logger import ResearchError


class TestCausalFramingValidator:
    """Tests for the causal keyword detection and enforcement logic."""

    # Common causal keywords that should trigger the validator
    CAUSAL_KEYWORDS = [
        "causes", "drives", "leads to", "results in", "determines",
        "influences", "triggers", "forces", "creates", "generates"
    ]

    def test_no_causal_keywords_passes(self):
        """Verify that text without causal keywords is accepted."""
        # Mock data to simulate a valid report state
        mock_correlation_data = {
            "degree_vs_size": {"rho": 0.45, "p_value": 0.03},
            "clustering_vs_duration": {"rho": 0.12, "p_value": 0.45}
        }
        mock_fitting_data = {"subject_001": {"exponent": 2.3, "status": "converged"}}
        mock_sensitivity_data = {"stable": True, "thresholds": [0.7, 0.75, 0.8]}

        # Mock the helper functions to return safe, associational text
        with patch('analysis.report.load_correlation_results', return_value=mock_correlation_data), \
             patch('analysis.report.load_fitting_results', return_value=mock_fitting_data), \
             patch('analysis.report.load_sensitivity_results', return_value=mock_sensitivity_data), \
             patch('analysis.report.format_associational_statement', return_value="Structural degree is associated with avalanche size."), \
             patch('analysis.report.generate_executive_summary', return_value="The analysis shows a correlation between structure and dynamics."), \
             patch('analysis.report.generate_detailed_results', return_value="Detailed metrics confirm the association."):
            
            # This should NOT raise an error
            try:
                result = generate_report()
                # If we get here without exception, the test passes
                assert "associated" in result or "correlation" in result or "correlation" in result.lower()
            except RuntimeError as e:
                pytest.fail(f"Valid associational text raised RuntimeError: {e}")

    @pytest.mark.parametrize("keyword", CAUSAL_KEYWORDS)
    def test_causal_keywords_raise_error(self, keyword):
        """Verify that text containing causal keywords raises a RuntimeError."""
        # We need to simulate a scenario where the generated text contains a causal keyword.
        # Since the actual generation logic is complex, we mock the internal text generation
        # to inject the specific keyword we are testing.
        
        mock_correlation_data = {"metric": {"rho": 0.5, "p_value": 0.01}}
        mock_fitting_data = {"sub": {"exponent": 2.0}}
        mock_sensitivity_data = {"stable": True}

        # Create a mock summary that contains the causal keyword
        causal_text = f"The network structure {keyword} the avalanche dynamics."

        with patch('analysis.report.load_correlation_results', return_value=mock_correlation_data), \
             patch('analysis.report.load_fitting_results', return_value=mock_fitting_data), \
             patch('analysis.report.load_sensitivity_results', return_value=mock_sensitivity_data), \
             patch('analysis.report.format_associational_statement', return_value="Safe text"), \
             patch('analysis.report.generate_executive_summary', return_value=causal_text), \
             patch('analysis.report.generate_detailed_results', return_value="Safe text"):
            
            with pytest.raises(RuntimeError) as excinfo:
                generate_report()
            
            assert "causal" in str(excinfo.value).lower() or "forbidden" in str(excinfo.value).lower()
            assert keyword in str(excinfo.value)

    def test_detailed_results_with_causal_keyword(self):
        """Verify that causal keywords in detailed results are also caught."""
        mock_correlation_data = {"metric": {"rho": 0.5, "p_value": 0.01}}
        mock_fitting_data = {"sub": {"exponent": 2.0}}
        mock_sensitivity_data = {"stable": True}

        # Inject keyword into detailed results
        detailed_text = "The clustering coefficient drives the duration of events."

        with patch('analysis.report.load_correlation_results', return_value=mock_correlation_data), \
             patch('analysis.report.load_fitting_results', return_value=mock_fitting_data), \
             patch('analysis.report.load_sensitivity_results', return_value=mock_sensitivity_data), \
             patch('analysis.report.format_associational_statement', return_value="Safe text"), \
             patch('analysis.report.generate_executive_summary', return_value="Safe summary"), \
             patch('analysis.report.generate_detailed_results', return_value=detailed_text):
            
            with pytest.raises(RuntimeError) as excinfo:
                generate_report()
            
            assert "drives" in str(excinfo.value)

    def test_mixed_case_keywords_detected(self):
        """Verify that case-insensitive matching works for causal keywords."""
        mock_correlation_data = {"metric": {"rho": 0.5, "p_value": 0.01}}
        mock_fitting_data = {"sub": {"exponent": 2.0}}
        mock_sensitivity_data = {"stable": True}

        # Test with mixed case
        mixed_case_text = "The structure CAUSES the dynamics to change."

        with patch('analysis.report.load_correlation_results', return_value=mock_correlation_data), \
             patch('analysis.report.load_fitting_results', return_value=mock_fitting_data), \
             patch('analysis.report.load_sensitivity_results', return_value=mock_sensitivity_data), \
             patch('analysis.report.format_associational_statement', return_value="Safe text"), \
             patch('analysis.report.generate_executive_summary', return_value=mixed_case_text), \
             patch('analysis.report.generate_detailed_results', return_value="Safe text"):
            
            with pytest.raises(RuntimeError) as excinfo:
                generate_report()
            
            assert "CAUSES" in str(excinfo.value) or "causes" in str(excinfo.value).lower()

    def test_empty_text_passes(self):
        """Verify that empty or None text does not raise an error."""
        mock_correlation_data = {"metric": {"rho": 0.5, "p_value": 0.01}}
        mock_fitting_data = {"sub": {"exponent": 2.0}}
        mock_sensitivity_data = {"stable": True}

        with patch('analysis.report.load_correlation_results', return_value=mock_correlation_data), \
             patch('analysis.report.load_fitting_results', return_value=mock_fitting_data), \
             patch('analysis.report.load_sensitivity_results', return_value=mock_sensitivity_data), \
             patch('analysis.report.format_associational_statement', return_value=""), \
             patch('analysis.report.generate_executive_summary', return_value=""), \
             patch('analysis.report.generate_detailed_results', return_value=""):
            
            try:
                generate_report()
            except RuntimeError:
                pytest.fail("Empty text should not raise RuntimeError")

    def test_report_contains_validation_message(self):
        """Verify the error message provides guidance on how to fix the issue."""
        mock_correlation_data = {"metric": {"rho": 0.5, "p_value": 0.01}}
        mock_fitting_data = {"sub": {"exponent": 2.0}}
        mock_sensitivity_data = {"stable": True}

        bad_text = "This drives that."

        with patch('analysis.report.load_correlation_results', return_value=mock_correlation_data), \
             patch('analysis.report.load_fitting_results', return_value=mock_fitting_data), \
             patch('analysis.report.load_sensitivity_results', return_value=mock_sensitivity_data), \
             patch('analysis.report.format_associational_statement', return_value="Safe"), \
             patch('analysis.report.generate_executive_summary', return_value=bad_text), \
             patch('analysis.report.generate_detailed_results', return_value="Safe"):
            
            with pytest.raises(RuntimeError) as excinfo:
                generate_report()
            
            error_msg = str(excinfo.value)
            # Check for helpful guidance in the error message
            assert "causal" in error_msg.lower() or "associational" in error_msg.lower()
            assert "rephrase" in error_msg.lower() or "forbidden" in error_msg.lower()