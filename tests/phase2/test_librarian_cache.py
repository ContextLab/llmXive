"""Tests for the librarian disk cache (spec 005 / T015 / FR-011 / SC-012).

Per Constitution Principle III: real disk (pytest tmp_path), no
in-memory mocks.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from llmxive.librarian.cache import (
    cache_key,
    cache_path,
    get,
    invalidate,
    normalize_term,
    set,
)

# --- Cache key ------------------------------------------------------------


def test_cache_key_is_deterministic():
    """Same inputs → same key; different inputs → different keys."""
    k1 = cache_key("term", "computer science", 5, "1.0.0")
    k2 = cache_key("term", "computer science", 5, "1.0.0")
    assert k1 == k2

    k3 = cache_key("term", "biology", 5, "1.0.0")  # field differs
    assert k1 != k3


def test_cache_key_length():
    """Keys are sha256 hex digests (64 chars)."""
    k = cache_key("anything", None, 5, "1.0.0")
    assert len(k) == 64


def test_cache_path_under_state_dir(tmp_path: Path):
    """cache_path() returns under <repo>/state/librarian-cache/."""
    p = cache_path(tmp_path, "abc123")
    assert p == tmp_path / "state" / "librarian-cache" / "abc123.json"


# --- Cache miss / hit / TTL / invalidation --------------------------------


def test_cache_miss_returns_none(tmp_path: Path):
    """Empty cache → get returns None."""
    k = cache_key("never-cached", None, 5, "1.0.0")
    assert get(tmp_path, k, current_prompt_version="1.0.0") is None


def test_cache_set_then_hit(tmp_path: Path):
    """A roundtrip — set + get returns the same payload."""
    k = cache_key("term", None, 5, "1.0.0")
    payload = {"verified_citations": [], "outcome": "success"}
    set(tmp_path, k,
        term_normalized="term", field=None, target_n=5,
        prompt_version="1.0.0", result=payload)
    hit = get(tmp_path, k, current_prompt_version="1.0.0")
    assert hit == payload


def test_cache_invalidation_on_prompt_version_bump(tmp_path: Path):
    """Cached entry under prompt v1.0.0 is ignored when current is v1.1.0."""
    k = cache_key("term", None, 5, "1.0.0")
    set(tmp_path, k,
        term_normalized="term", field=None, target_n=5,
        prompt_version="1.0.0", result={"x": 1})
    # Same key, but caller is on a newer prompt version → miss.
    assert get(tmp_path, k, current_prompt_version="1.1.0") is None


def test_cache_ttl_expiry(tmp_path: Path):
    """An entry older than http_head TTL (7d) is treated as a miss."""
    k = cache_key("term", None, 5, "1.0.0")
    set(tmp_path, k,
        term_normalized="term", field=None, target_n=5,
        prompt_version="1.0.0", result={"x": 1})
    # Pretend it's now 10 days later.
    future = _dt.datetime.now(_dt.UTC) + _dt.timedelta(days=10)
    assert get(tmp_path, k, current_prompt_version="1.0.0", now_utc=future) is None


def test_cache_hit_within_ttl(tmp_path: Path):
    """An entry within the http_head TTL (7d) is returned."""
    k = cache_key("term", None, 5, "1.0.0")
    set(tmp_path, k,
        term_normalized="term", field=None, target_n=5,
        prompt_version="1.0.0", result={"x": 1})
    # Fast-forward only a few days.
    future = _dt.datetime.now(_dt.UTC) + _dt.timedelta(days=3)
    assert get(tmp_path, k, current_prompt_version="1.0.0", now_utc=future) == {"x": 1}


def test_cache_hit_returns_deterministic_result(tmp_path: Path):
    """SC-012: re-invoking with the same key on the same cache state
    returns identical results across multiple reads."""
    k = cache_key("transformer attention", "computer science", 5, "1.0.0")
    payload = {
        "verified_citations": [{"primary_pointer": "1706.03762", "title": "Attention"}],
        "outcome": "success",
        "metadata": {"deterministic": True},
    }
    set(tmp_path, k,
        term_normalized="transformer attention", field="computer science",
        target_n=5, prompt_version="1.0.0", result=payload)
    hit_1 = get(tmp_path, k, current_prompt_version="1.0.0")
    hit_2 = get(tmp_path, k, current_prompt_version="1.0.0")
    hit_3 = get(tmp_path, k, current_prompt_version="1.0.0")
    assert hit_1 == hit_2 == hit_3 == payload


def test_invalidate_removes_file(tmp_path: Path):
    """invalidate() returns True when a file existed, False otherwise."""
    k = cache_key("term", None, 5, "1.0.0")
    set(tmp_path, k,
        term_normalized="term", field=None, target_n=5,
        prompt_version="1.0.0", result={"x": 1})
    assert invalidate(tmp_path, k) is True
    assert invalidate(tmp_path, k) is False  # already gone


def test_corrupt_cache_file_treated_as_miss(tmp_path: Path):
    """If the JSON file is unparseable, get() returns None (no crash)."""
    k = cache_key("term", None, 5, "1.0.0")
    p = cache_path(tmp_path, k)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not-json{garbage", encoding="utf-8")
    assert get(tmp_path, k, current_prompt_version="1.0.0") is None


# --- normalize_term -------------------------------------------------------


def test_normalize_term_lowercases():
    assert normalize_term("Transformer Attention") == "transformer attention"


def test_normalize_term_collapses_whitespace():
    assert normalize_term("  foo   bar  baz  ") == "foo bar baz"


def test_normalize_term_handles_empty():
    assert normalize_term("") == ""
    assert normalize_term("   ") == ""


def test_normalize_term_idempotent():
    first = normalize_term("  Transformer  Attention  ")
    second = normalize_term(first)
    assert first == second
