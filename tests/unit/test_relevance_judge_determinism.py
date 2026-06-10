"""Issue #112 — librarian relevance judge must be deterministic.

Covers the two root causes confirmed in the issue:
  1. ``judge_one()`` never pinned a temperature, so backend-default
     sampling (> 0) flipped verdicts run-to-run → ``JUDGE_TEMPERATURE``
     (0.0) is now passed on every call.
  2. The module docstring claimed verdicts were cached, but no cache
     existed → per-verdict disk cache at ``state/librarian-cache/judge/``
     keyed by (normalized query, candidate pointer, prompt-content hash).

Correctness guards: fail-open verdicts (backend unreachable, empty or
unparseable response) are NEVER cached — a transient outage must not
latch into a permanent "admit".
"""

from __future__ import annotations

import json

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.librarian import relevance_judge
from llmxive.librarian.relevance_judge import (
    JUDGE_PROMPT_VERSION,
    JUDGE_TEMPERATURE,
    JudgeVerdict,
    _verdict_cache_key,
    _verdict_cache_path,
    filter_by_relevance,
    judge_one,
)
from llmxive.librarian.verify import VerificationLog, VerifiedCitation

QUERY = "How does code-clone density correlate with LLM perplexity?"
POINTER = "arXiv:2107.06499"


def _response(text: str) -> ChatResponse:
    return ChatResponse(
        text=text,
        model="fake-model",
        backend="fake",
        cost_estimate_usd=0.0,
    )


def _judge_kwargs(tmp_path):
    return dict(
        query=QUERY,
        candidate_title="Deduplicating training data makes language models better",
        candidate_abstract="We study duplication and memorization in LMs.",
        candidate_pointer=POINTER,
        repo_root=tmp_path,
    )


def _citation(pointer: str) -> VerifiedCitation:
    return VerifiedCitation(
        primary_pointer=pointer,
        bibliographic_info={"title": f"Paper {pointer}"},
        summary="A grounded summary.",
        summary_grounded_pdf=None,
        verification_log=VerificationLog(
            url_resolves=True,
            final_url=f"https://example.org/{pointer}",
            redirect_chain=[],
            http_status=200,
            title_token_overlap_score=1.0,
            summary_grounding_score=1.0,
            pdf_sample_score=None,
            verified_at="2026-06-10T00:00:00Z",
        ),
    )


def test_judge_pins_temperature_zero(monkeypatch, tmp_path):
    captured: dict = {}

    def fake_chat(messages, **kwargs):
        captured.update(kwargs)
        return _response("VERDICT: YES\ncategory (b) applies")

    monkeypatch.setattr(relevance_judge, "chat_with_fallback", fake_chat)
    verdict = judge_one(**_judge_kwargs(tmp_path))
    assert verdict.relevant is True
    assert captured["temperature"] == JUDGE_TEMPERATURE == 0.0


def test_verdict_frozen_and_replayed_across_backend_flip(monkeypatch, tmp_path):
    """First resolution freezes the verdict; a later backend flip (the
    nondeterminism #112 documents) cannot change the replayed verdict."""
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: YES\n(b) same mechanism"),
    )
    first = judge_one(**_judge_kwargs(tmp_path))
    assert first.relevant is True and first.cached is False

    key = _verdict_cache_key(QUERY, POINTER)
    cache_file = _verdict_cache_path(tmp_path, key)
    assert cache_file.is_file()
    entry = json.loads(cache_file.read_text(encoding="utf-8"))
    assert entry["relevant"] is True
    assert entry["prompt_version"] == JUDGE_PROMPT_VERSION

    # Simulate temperature-noise: the backend now says NO. The frozen
    # verdict must replay instead.
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: NO\noff-domain"),
    )
    second = judge_one(**_judge_kwargs(tmp_path))
    assert second.relevant is True
    assert second.cached is True


def test_backend_failure_fail_open_not_cached(monkeypatch, tmp_path):
    def boom(messages, **kw):
        raise RuntimeError("backend down")

    monkeypatch.setattr(relevance_judge, "chat_with_fallback", boom)
    verdict = judge_one(**_judge_kwargs(tmp_path))
    assert verdict.relevant is True  # fail-open admit
    assert verdict.fail_open is True
    assert verdict.backend_error is not None
    key = _verdict_cache_key(QUERY, POINTER)
    assert not _verdict_cache_path(tmp_path, key).exists()

    # Once the backend recovers, a REAL judgment is made and cached.
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: NO\noff-domain"),
    )
    recovered = judge_one(**_judge_kwargs(tmp_path))
    assert recovered.relevant is False
    assert _verdict_cache_path(tmp_path, key).is_file()


def test_unparseable_response_fail_open_not_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("I am not sure what to say here."),
    )
    verdict = judge_one(**_judge_kwargs(tmp_path))
    assert verdict.relevant is True
    assert verdict.fail_open is True
    key = _verdict_cache_key(QUERY, POINTER)
    assert not _verdict_cache_path(tmp_path, key).exists()


def test_cache_key_normalizes_query_and_separates_candidates():
    spaced = "  How does   code-clone density correlate with LLM perplexity? "
    assert _verdict_cache_key(QUERY, POINTER) == _verdict_cache_key(spaced, POINTER)
    assert _verdict_cache_key(QUERY, POINTER) != _verdict_cache_key(QUERY, "arXiv:9999.00001")
    assert _verdict_cache_key("a different question", POINTER) != _verdict_cache_key(QUERY, POINTER)


def test_no_cache_io_without_pointer_or_root(monkeypatch, tmp_path):
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: YES\nfine"),
    )
    kwargs = _judge_kwargs(tmp_path)
    kwargs.pop("candidate_pointer")
    kwargs.pop("repo_root")
    verdict = judge_one(**kwargs)
    assert verdict.relevant is True
    assert not (tmp_path / "state").exists()


def test_filter_by_relevance_replays_frozen_verdicts(monkeypatch, tmp_path):
    """End-to-end: a flesh_out-style re-run sees identical judgments."""
    citations = [_citation("arXiv:1111.11111"), _citation("arXiv:2222.22222")]

    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: YES\n(b)"),
    )
    kept1, rejected1 = filter_by_relevance(
        citations, query=QUERY, repo_root=tmp_path,
    )
    assert len(kept1) == 2 and not rejected1

    # Re-run with a flipped backend: frozen verdicts must win.
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: NO\nhomonym keywords"),
    )
    kept2, rejected2 = filter_by_relevance(
        citations, query=QUERY, repo_root=tmp_path,
    )
    assert [c.primary_pointer for c in kept2] == [c.primary_pointer for c in kept1]
    assert not rejected2


def test_cache_write_failure_does_not_break_judgment(monkeypatch, tmp_path):
    monkeypatch.setattr(
        relevance_judge, "chat_with_fallback",
        lambda messages, **kw: _response("VERDICT: NO\noff-domain"),
    )

    def boom_write(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(relevance_judge, "_write_cached_verdict", boom_write)
    verdict = judge_one(**_judge_kwargs(tmp_path))
    assert verdict.relevant is False  # judgment still returned


@pytest.mark.parametrize("raw,expected_relevant,expected_fail_open", [
    ("VERDICT: YES\nbecause (a)", True, False),
    ("VERDICT: NO\noff-domain", False, False),
    ("", True, True),
    ("garbled nonsense with no verdict", True, True),
])
def test_parse_verdict_fail_open_marking(raw, expected_relevant, expected_fail_open):
    verdict = relevance_judge._parse_verdict(raw)
    assert isinstance(verdict, JudgeVerdict)
    assert verdict.relevant is expected_relevant
    assert verdict.fail_open is expected_fail_open
