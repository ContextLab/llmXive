"""
Unit tests for the causal language scanner (code/utils/cautions.py).

This module verifies that the scan_report_for_causal_language function
correctly identifies and flags reports containing causal trigger words,
ensuring compliance with FR-006 (associational framing).
"""

import pytest
from utils.cautions import scan_report_for_causal_language


class TestCausalLanguageScanner:
    """Tests for the scan_report_for_causal_language function."""

    def test_clean_report_no_violations(self):
        """Verify that a report without causal language returns (False, [])."""
        report = (
            "The study observed an association between social validation "
            "and self-perception scores. Higher engagement was linked to "
            "higher scores, but no causal mechanism was established."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is False
        assert found_words == []

    def test_report_with_causes_keyword(self):
        """Verify that a report containing 'causes' is flagged and rejected."""
        report = (
            "The results indicate that simulated social validation causes "
            "an increase in self-perception scores among adolescents."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is True
        assert "causes" in found_words

    def test_report_with_leads_to_keyword(self):
        """Verify that a report containing 'leads to' is flagged."""
        report = (
            "Increased engagement leads to better self-perception outcomes."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is True
        assert "leads to" in found_words

    def test_report_with_influences_keyword(self):
        """Verify that a report containing 'influences' is flagged."""
        report = (
            "Social media activity influences how teenagers view themselves."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is True
        assert "influences" in found_words

    def test_report_with_impact_keyword(self):
        """Verify that a report containing 'impact' is flagged."""
        report = (
            "The impact of simulated validation on self-esteem is significant."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is True
        assert "impact of" in found_words

    def test_multiple_violations_detected(self):
        """Verify that multiple trigger words are all detected."""
        report = (
            "Validation causes changes and leads to improvements. "
            "It also influences self-view."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is True
        assert "causes" in found_words
        assert "leads to" in found_words
        assert "influences" in found_words
        assert len(found_words) == 3

    def test_case_insensitive_detection(self):
        """Verify that detection is case-insensitive."""
        report = (
            "Validation CAUSES changes and LEADS TO improvements."
        )
        is_violation, found_words = scan_report_for_causal_language(report)
        
        assert is_violation is True
        assert "causes" in found_words
        assert "leads to" in found_words

    def test_empty_report(self):
        """Verify that an empty report returns (False, [])."""
        is_violation, found_words = scan_report_for_causal_language("")
        
        assert is_violation is False
        assert found_words == []

    def test_none_report(self):
        """Verify that a None report returns (False, [])."""
        is_violation, found_words = scan_report_for_causal_language(None)
        
        assert is_violation is False
        assert found_words == []

    def test_word_boundary_accuracy(self):
        """Verify that trigger words are detected as substrings, not just whole words."""
        # The current implementation uses substring search.
        # "causes" should be found even if embedded in "uncaused" (though unlikely in text).
        report = "The uncaused effect is not what we found."
        is_violation, found_words = scan_report_for_causal_language(report)
        
        # "caused" is a trigger word.
        assert is_violation is True
        assert "caused" in found_words

    def test_rejection_logic(self):
        """
        Verify the rejection logic: if is_violation is True, the report
        should be considered 'rejected' (i.e., not passed).
        """
        report = "Social validation causes self-esteem changes."
        is_violation, _ = scan_report_for_causal_language(report)
        
        # Logic: if violation, reject.
        should_reject = is_violation
        assert should_reject is True

        report_clean = "Social validation is associated with self-esteem."
        is_violation_clean, _ = scan_report_for_causal_language(report_clean)
        
        should_reject_clean = is_violation_clean
        assert should_reject_clean is False