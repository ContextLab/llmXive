"""T011 — unit tests for claims/classify.py (spec 016 foundational)."""

from __future__ import annotations

import pytest

from llmxive.claims.classify import classify
from llmxive.claims.models import ClaimKind


class TestClassifyMagnitude:
    def test_superlative_largest(self):
        assert classify("Python is the most popular language", "Python is the most popular") == ClaimKind.MAGNITUDE

    def test_superlative_earliest(self):
        assert classify("This is the earliest known record", "earliest known record") == ClaimKind.MAGNITUDE

    def test_comparative_more_than(self):
        assert classify("The model achieves more than 90% accuracy", "accuracy > 90%") == ClaimKind.MAGNITUDE

    def test_superlative_largest_word(self):
        assert classify("Jupiter is the largest planet in the solar system", "Jupiter is largest planet") == ClaimKind.MAGNITUDE

    def test_comparative_fewer_than(self):
        assert classify("Fewer than 100 examples exist", "count < 100") == ClaimKind.MAGNITUDE


class TestClassifyRelational:
    def test_is_capital_of(self):
        assert classify("Paris is the capital of France", "Paris | is capital of | France") == ClaimKind.RELATIONAL

    def test_author_of(self):
        assert classify("Einstein is the author of the relativity paper", "Einstein | author of | relativity paper") == ClaimKind.RELATIONAL

    def test_wrote(self):
        assert classify("Turing wrote 'Computing Machinery and Intelligence'", "Turing | wrote | Computing Machinery") == ClaimKind.RELATIONAL


class TestClassifyCausal:
    def test_causes(self):
        assert classify("Smoking causes lung cancer", "smoking causes lung cancer") == ClaimKind.CAUSAL

    def test_leads_to(self):
        assert classify("High temperature leads to protein denaturation", "temperature leads to denaturation") == ClaimKind.CAUSAL

    def test_results_in(self):
        assert classify("Overtraining results in poor generalization", "overtraining results in poor generalization") == ClaimKind.CAUSAL


class TestClassifyResult:
    def test_accuracy_was(self):
        assert classify("The accuracy was 95% on the test set", "accuracy=0.95") == ClaimKind.RESULT

    def test_we_observed(self):
        assert classify("We observed a 3x speedup over the baseline", "speedup=3x") == ClaimKind.RESULT

    def test_our_model_achieved(self):
        assert classify("Our model achieved state-of-the-art performance", "model achieved SOTA") == ClaimKind.RESULT


class TestClassifyCitation:
    def test_arxiv_id(self):
        assert classify("See arXiv:2301.00001 for details", "arXiv:2301.00001") == ClaimKind.CITATION

    def test_doi(self):
        assert classify("As shown in doi:10.1234/abc", "doi:10.1234/abc") == ClaimKind.CITATION

    def test_bare_doi_canonical(self):
        assert classify("Reference 10.1038/nature12345", "10.1038/nature12345") == ClaimKind.CITATION


class TestClassifyNumeric:
    def test_plain_statistic(self):
        assert classify("There are 9988 prime knots with 13 crossings", "9988") == ClaimKind.NUMERIC

    def test_percentage(self):
        assert classify("42% of respondents agreed", "42%") == ClaimKind.NUMERIC

    def test_count(self):
        assert classify("The dataset contains 10000 samples", "10000") == ClaimKind.NUMERIC


class TestClassifyEntityFact:
    def test_definition(self):
        assert classify("A knot is a closed curve in 3-dimensional space", "knot is a closed curve in 3D space") == ClaimKind.ENTITY_FACT

    def test_is_a_relation(self):
        assert classify("Python is a programming language", "Python is a programming language") == ClaimKind.ENTITY_FACT
