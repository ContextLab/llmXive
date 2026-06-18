"""SemanticScholar availability breaker (papers channel, Fix E).

SS rate-limits aggressively (HTTP 429) and recovers slowly. Re-querying it once
per claim after a 429 wedges a whole pipeline run in fail-soft retries. These
pin the breaker contract: a persistent-unavailability signal (429/403/rate-limit)
trips it for the rest of the process; a transient error (timeout, reset) does
NOT; and the reset hook clears it.
"""

from __future__ import annotations

import pytest

from llmxive.fill.channels import papers


@pytest.fixture(autouse=True)
def _clean_breaker():
    papers._reset_ss_breaker()
    yield
    papers._reset_ss_breaker()


def test_starts_available() -> None:
    assert papers._ss_is_unavailable() is False


@pytest.mark.parametrize(
    "message",
    [
        "429 Client Error:  for url: https://api.semanticscholar.org/...",
        "Too Many Requests",
        "rate limit exceeded",
        "403 Forbidden",
    ],
)
def test_persistent_signal_trips_breaker(message: str) -> None:
    papers._trip_ss_breaker_if_persistent(Exception(message))
    assert papers._ss_is_unavailable() is True


@pytest.mark.parametrize(
    "message",
    [
        "Connection reset by peer",
        "Read timed out",
        "Temporary failure in name resolution",
    ],
)
def test_transient_error_does_not_trip_breaker(message: str) -> None:
    papers._trip_ss_breaker_if_persistent(Exception(message))
    assert papers._ss_is_unavailable() is False


def test_reset_clears_a_tripped_breaker() -> None:
    papers._trip_ss_breaker_if_persistent(Exception("429"))
    assert papers._ss_is_unavailable() is True
    papers._reset_ss_breaker()
    assert papers._ss_is_unavailable() is False


def test_tripped_breaker_short_circuits_ss_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Once tripped, search_and_fetch must NOT construct a SemanticScholar client.

    This is the whole point of the breaker: stop hammering a service that has
    told us to stop. We assert by making SS construction explode — if the guard
    works, it is never reached. arXiv is stubbed to empty so the call is offline.
    """
    papers._trip_ss_breaker_if_persistent(Exception("429"))

    def _boom(*a, **k):  # pragma: no cover - must never be called
        raise AssertionError("SemanticScholarClient constructed despite tripped breaker")

    class _EmptyArxiv:
        def search(self, *a, **k):
            return []

    monkeypatch.setattr(papers, "SemanticScholarClient", _boom)
    monkeypatch.setattr(papers, "_shared_arxiv_client", lambda: _EmptyArxiv())

    # A real Claim — the tripped path never touches its fields, but build it
    # faithfully rather than mocking the type.
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus

    claim = Claim(
        claim_id="c_ssbreaker",
        kind=ClaimKind.NUMERIC,
        raw_text="x",
        canonical="x",
        context="",
        artifact_path="a.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence={},
        resolver=None,
        attempts=0,
        updated_at="2026-06-18T00:00:00Z",
        source_hash=None,
    )
    assert papers.search_and_fetch("any query", claim) == []
