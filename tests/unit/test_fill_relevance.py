"""Unit tests for the PROSE-channel semantic substantiation gate (spec 019, C3).

Two layers, both fail-closed:

* ``_subject_cooccurs`` — deterministic, zero-network: a subject keyword must be
  near an occurrence of the value. This rejects the headline "≤6 / Almoravid
  dynasty" coincidental match with NO LLM call (SC-007).
* ``prose_substantiated`` — for survivors, accept ONLY a ``grounded`` verdict from
  the real :func:`grounding.entailment.assess`. We drive ``assess`` through a
  *recording backend* that returns a canned YAML verdict over the actual router/
  parser path (the secondary fast-feedback layer per Constitution III, using the
  same call syntax); the live-backend behavior is covered by the real_call suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llmxive.backends.base import ChatResponse
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.fill.models import FetchedSource
from llmxive.fill.relevance import _subject_cooccurs, prose_substantiated


@dataclass
class _VerdictBackend:
    """Fake backend (no model mock) whose ``chat`` returns a fixed YAML verdict
    body, exercising the real ``assess`` router + parser. Records every call so a
    test can assert whether the LLM was consulted at all."""

    status: str = "grounded"
    name: str = "dartmouth"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append({"model": model, "max_tokens": max_tokens})
        return ChatResponse(
            text=f"status: {self.status}\nevidence: ''\nnote: ''",
            model=model,
            backend=self.name,
        )


def _knot_claim(raw_text: str) -> Claim:
    return Claim(
        claim_id="c1",
        kind=ClaimKind.NUMERIC,
        raw_text=raw_text,
        canonical=raw_text,
        context="knot theory",
        artifact_path="specs/x/spec.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-06-02T00:00:00Z",
    )


def _source(text: str, *, channel: str = "wikipedia") -> FetchedSource:
    return FetchedSource(
        channel=channel,
        source_id="src1",
        url="https://en.wikipedia.org/wiki/x",
        title="x",
        text=text,
        authority=3,
    )


# The headline bug: the value 6 appears only as "about 6 generations" in an
# unrelated article; the knot subject keywords are nowhere near it.
_ALMORAVID = (
    "The Almoravid dynasty was a Berber Muslim dynasty centered in Morocco. "
    "It lasted about 6 generations before its decline in the 12th century."
)
# A genuinely-relevant passage: the value 3 sits among the knot subject keywords.
_TREFOIL = (
    "The trefoil knot is the simplest nontrivial knot. Its crossing number is 3, "
    "and it is the unique knot with three crossings."
)


def test_cooccur_rejects_coincidental_match_no_llm() -> None:
    """SC-001/SC-007: a knot crossing-number claim whose value 6 matches only an
    unrelated 'about 6 generations' is rejected by the deterministic pre-filter,
    and ``assess`` is NEVER called."""
    claim = _knot_claim("the trefoil knot has crossing number 6")
    assert _subject_cooccurs("6", _ALMORAVID, claim) is False

    backend = _VerdictBackend(status="grounded")  # would say yes if consulted
    ok = prose_substantiated(
        "6", _source(_ALMORAVID), claim, backend=backend, model=None, repo_root=None
    )
    assert ok is False
    assert backend.calls == []  # zero LLM calls — pre-filter short-circuited


def test_cooccur_accepts_relevant_passage() -> None:
    claim = _knot_claim("the trefoil knot has crossing number 3")
    assert _subject_cooccurs("3", _TREFOIL, claim) is True


def test_backend_none_is_fail_closed() -> None:
    """Co-occurrence passes, but without a backend there is no way to run
    entailment → reject (never accept on the literal/keyword layers alone)."""
    claim = _knot_claim("the trefoil knot has crossing number 3")
    ok = prose_substantiated(
        "3", _source(_TREFOIL), claim, backend=None, model=None, repo_root=None
    )
    assert ok is False


def test_grounded_verdict_accepts() -> None:
    claim = _knot_claim("the trefoil knot has crossing number 3")
    backend = _VerdictBackend(status="grounded")
    ok = prose_substantiated(
        "3", _source(_TREFOIL), claim, backend=backend, model=None, repo_root=None
    )
    assert ok is True
    assert backend.calls, "assess must have been consulted for a co-occurring value"


def test_contradicted_and_not_found_reject() -> None:
    claim = _knot_claim("the trefoil knot has crossing number 3")
    for status in ("contradicted", "not_found"):
        backend = _VerdictBackend(status=status)
        ok = prose_substantiated(
            "3", _source(_TREFOIL), claim, backend=backend, model=None, repo_root=None
        )
        assert ok is False, f"{status} verdict must reject (fail-closed)"
