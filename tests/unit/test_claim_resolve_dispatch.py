"""T013 — Unit tests for claims/resolve.py dispatch (pure logic, no mocks).

Tests:
- select_resolver maps each ClaimKind to the correct callable.
- number_substantiated (deterministic gate) returns True/False based on real text.
"""

from __future__ import annotations

import pytest

from llmxive.claims.models import ClaimKind
from llmxive.claims.resolve import select_resolver
from llmxive.grounding.service import number_substantiated


class TestSelectResolver:
    def test_numeric_resolver(self):
        fn = select_resolver(ClaimKind.NUMERIC)
        assert callable(fn)
        assert fn.__name__ == "resolve_numeric_or_citation"

    def test_citation_resolver(self):
        fn = select_resolver(ClaimKind.CITATION)
        assert callable(fn)
        assert fn.__name__ == "resolve_numeric_or_citation"

    def test_magnitude_resolver(self):
        fn = select_resolver(ClaimKind.MAGNITUDE)
        assert callable(fn)
        assert fn.__name__ == "resolve_magnitude"

    def test_relational_resolver(self):
        fn = select_resolver(ClaimKind.RELATIONAL)
        assert callable(fn)
        assert fn.__name__ == "resolve_relational"

    def test_causal_resolver(self):
        fn = select_resolver(ClaimKind.CAUSAL)
        assert callable(fn)
        assert fn.__name__ == "resolve_causal"

    def test_entity_fact_resolver(self):
        fn = select_resolver(ClaimKind.ENTITY_FACT)
        assert callable(fn)
        assert fn.__name__ == "resolve_entity_fact"

    def test_result_resolver(self):
        fn = select_resolver(ClaimKind.RESULT)
        assert callable(fn)
        assert fn.__name__ == "resolve_result"

    def test_all_kinds_covered(self):
        """Every ClaimKind maps to a callable without raising."""
        for kind in ClaimKind:
            fn = select_resolver(kind)
            assert callable(fn), f"No resolver for {kind}"


class TestNumberSubstantiated:
    """Deterministic content gate — no backend, no network."""

    def test_number_present_with_comma(self):
        doc = "There are 9,988 prime knots with 10 or fewer crossings."
        assert number_substantiated("9988", doc) is True

    def test_number_present_bare(self):
        doc = "The count is 9988 prime knots."
        assert number_substantiated("9988", doc) is True

    def test_number_present_spaced(self):
        doc = "Exactly 9 988 prime knots are documented."
        assert number_substantiated("9988", doc) is True

    def test_wrong_number_absent(self):
        doc = "There are 9,988 prime knots with up to 10 crossings."
        assert number_substantiated("27635", doc) is False

    def test_wrong_number_absent_variant(self):
        doc = "There are 9,988 prime knots with up to 10 crossings."
        assert number_substantiated("27,635", doc) is False

    def test_none_number_returns_true(self):
        """No number to check → gate not applicable → True."""
        assert number_substantiated(None, "some text") is True

    def test_empty_number_returns_true(self):
        assert number_substantiated("", "some text") is True

    def test_number_absent_from_empty_doc(self):
        assert number_substantiated("9988", "") is False

    def test_number_absent_from_none_doc(self):
        assert number_substantiated("9988", None) is False
