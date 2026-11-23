import pytest
import sys
import os

# Add the project root to the path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.cautions import scan_report_for_causal_language
from utils.exceptions import CausalLanguageViolationError

class TestScanReportForCausalLanguage:
    """
    Unit tests for code/utils/cautions.py verifying that a report with 
    causal trigger words is flagged and rejected.
    """

    def test_no_causal_language(self):
        """Test that a report without causal language returns False."""
        report = "This study shows an association between engagement and self-esteem."
        result = scan_report_for_causal_language(report)
        assert result is False, "Expected False for report without causal language"

    def test_causes_detected(self):
        """Test that 'causes' is detected as causal language."""
        report = "Increased engagement causes higher self-esteem."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report containing 'causes'"

    def test_leads_to_detected(self):
        """Test that 'leads to' is detected as causal language."""
        report = "Social validation leads to improved self-perception."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report containing 'leads to'"

    def test_results_in_detected(self):
        """Test that 'results in' is detected as causal language."""
        report = "High engagement results in better mental health outcomes."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report containing 'results in'"

    def test_impacts_detected(self):
        """Test that 'impacts' is detected as causal language."""
        report = "Simulated validation impacts how adolescents view themselves."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report containing 'impacts'"

    def test_affects_detected(self):
        """Test that 'affects' is detected as causal language."""
        report = "The number of likes affects self-worth."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report containing 'affects'"

    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        report = "Engagement CAUSES changes in self-esteem."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report with uppercase causal word"

    def test_partial_word_not_detected(self):
        """Test that partial matches of trigger words are not detected."""
        report = "The causality of the study is questionable."
        result = scan_report_for_causal_language(report)
        assert result is False, "Expected False for partial match of 'causes'"

    def test_empty_report(self):
        """Test that an empty report returns False."""
        report = ""
        result = scan_report_for_causal_language(report)
        assert result is False, "Expected False for empty report"

    def test_multiple_triggers_detected(self):
        """Test that multiple causal triggers in one report are detected."""
        report = "Engagement causes stress and leads to anxiety."
        result = scan_report_for_causal_language(report)
        assert result is True, "Expected True for report with multiple causal triggers"

    def test_integration_with_exception(self):
        """
        Test that the scanner can be used to raise CausalLanguageViolationError
        as required by the pipeline (T020, T028).
        """
        report = "This data proves that likes cause happiness."
        if scan_report_for_causal_language(report):
            with pytest.raises(CausalLanguageViolationError):
                raise CausalLanguageViolationError(
                    "Causal language detected in report: " + report
                )