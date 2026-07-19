"""
Unit tests for results text generation and language enforcement.
Verifies that FR-008 (associational language) is strictly enforced.
"""

import pytest
import json
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.results import (
    sanitize_text,
    generate_kruskal_wallis_summary,
    generate_pairwise_summary,
    generate_lme_summary,
    generate_collinearity_summary,
    generate_sensitivity_summary,
    CAUSAL_PHRASES,
    ASSOCIATIONAL_PHRASES
)

class TestSanitizeText:
    """Tests for the text sanitization function."""

    def test_replaces_causes_with_associated(self):
        """Test that 'causes' is replaced with 'is associated with'."""
        raw = "Variable X causes Variable Y."
        sanitized = sanitize_text(raw)
        assert "causes" not in sanitized.lower()
        assert "associated" in sanitized.lower()

    def test_replaces_leads_to(self):
        """Test that 'leads to' is replaced."""
        raw = "This leads to a change."
        sanitized = sanitize_text(raw)
        assert "leads to" not in sanitized.lower()
        assert "associated" in sanitized.lower()

    def test_preserves_non_causal_text(self):
        """Test that non-causal text is preserved."""
        raw = "Variable X is associated with Variable Y."
        sanitized = sanitize_text(raw)
        assert sanitized == raw

    def test_empty_string(self):
        """Test handling of empty strings."""
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""

class TestKruskalWallisSummary:
    """Tests for Kruskal-Wallis summary generation."""

    def test_contains_associational_language(self):
        """Test that the summary contains 'associated' or 'correlational'."""
        stats = {'h_statistic': 10.5, 'df': 3}
        p_val = 0.01
        summary = generate_kruskal_wallis_summary(stats, p_val)
        
        assert "associated" in summary.lower() or "correlational" in summary.lower()
        assert "causes" not in summary.lower()
        assert "determines" not in summary.lower()

    def test_includes_statistics(self):
        """Test that the summary includes the provided statistics."""
        stats = {'h_statistic': 12.34, 'df': 5}
        p_val = 0.001
        summary = generate_kruskal_wallis_summary(stats, p_val)
        
        assert "12.34" in summary
        assert "5" in summary
        assert "0.001" in summary

    def test_non_significant_case(self):
        """Test summary generation for non-significant results."""
        stats = {'h_statistic': 1.2, 'df': 2}
        p_val = 0.55
        summary = generate_kruskal_wallis_summary(stats, p_val)
        
        assert "not significant" in summary.lower()
        assert "correlational" in summary.lower()

class TestPairwiseSummary:
    """Tests for pairwise comparison summary generation."""

    def test_significant_pairs(self):
        """Test summary with significant pairs."""
        comparisons = [
            {'group1': 'A', 'group2': 'B', 'p_value': 0.01, 'significant': True}
        ]
        summary = generate_pairwise_summary(comparisons)
        
        assert "significant association" in summary.lower()
        assert "correlational" in summary.lower()

    def test_no_significant_pairs(self):
        """Test summary with no significant pairs."""
        comparisons = [
            {'group1': 'A', 'group2': 'B', 'p_value': 0.45, 'significant': False}
        ]
        summary = generate_pairwise_summary(comparisons)
        
        assert "No pairwise comparisons" in summary
        assert "correlational" in summary.lower()

class TestLmeSummary:
    """Tests for Linear Mixed Effects summary generation."""

    def test_fixed_effects(self):
        """Test summary includes fixed effects with associational language."""
        fixed = {'x1': {'coef': 0.5, 'p_value': 0.01}}
        random = {'repo_variance': 0.5}
        summary = generate_lme_summary(fixed, random)
        
        assert "associated" in summary.lower() or "correlated" in summary.lower()
        assert "causes" not in summary.lower()

    def test_causality_warning(self):
        """Test that the summary explicitly warns against causal interpretation."""
        fixed = {}
        random = {}
        summary = generate_lme_summary(fixed, random)
        
        assert "causal" in summary.lower() or "not be interpreted as causal" in summary.lower()

class TestCollinearitySummary:
    """Tests for collinearity diagnostic summary."""

    def test_high_vif_detection(self):
        """Test summary when high VIF is detected."""
        vif_results = {'vif_scores': {'x1': 6.5, 'x2': 1.2}}
        summary = generate_collinearity_summary(vif_results)
        
        assert "correlated" in summary.lower() or "joint associational" in summary.lower()

    def test_no_high_vif(self):
        """Test summary when no high VIF is detected."""
        vif_results = {'vif_scores': {'x1': 2.1, 'x2': 1.5}}
        summary = generate_collinearity_summary(vif_results)
        
        assert "weak correlational" in summary.lower() or "multicollinearity" in summary.lower()

class TestSensitivitySummary:
    """Tests for sensitivity analysis summary."""

    def test_threshold_sensitivity(self):
        """Test summary includes threshold sensitivity data."""
        data = {
            'cutoffs': [24, 48],
            'false_positive_rates': [0.1, 0.05],
            'false_negative_rates': [0.05, 0.1]
        }
        summary = generate_sensitivity_summary(data)
        
        assert "threshold" in summary.lower()
        assert "correlational" in summary.lower()

class TestForbiddenPhrases:
    """Tests to ensure forbidden phrases are not present in outputs."""

    def test_no_causes_in_any_summary(self):
        """Verify 'causes' does not appear in any generated summary."""
        kw = generate_kruskal_wallis_summary({'h_statistic': 1, 'df': 1}, 0.5)
        pair = generate_pairwise_summary([])
        lme = generate_lme_summary({}, {})
        coll = generate_collinearity_summary({})
        sens = generate_sensitivity_summary({'cutoffs': [1], 'false_positive_rates': [0.1], 'false_negative_rates': [0.1]})
        
        all_text = f"{kw} {pair} {lme} {coll} {sens}"
        assert "causes" not in all_text.lower()

    def test_no_determines_in_any_summary(self):
        """Verify 'determines' does not appear in any generated summary."""
        kw = generate_kruskal_wallis_summary({'h_statistic': 1, 'df': 1}, 0.5)
        pair = generate_pairwise_summary([])
        lme = generate_lme_summary({}, {})
        coll = generate_collinearity_summary({})
        sens = generate_sensitivity_summary({'cutoffs': [1], 'false_positive_rates': [0.1], 'false_negative_rates': [0.1]})
        
        all_text = f"{kw} {pair} {lme} {coll} {sens}"
        assert "determines" not in all_text.lower()