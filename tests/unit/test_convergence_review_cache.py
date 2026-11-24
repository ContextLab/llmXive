"""Tests for the resumable convergence panel-review cache.

CORRECTNESS IS PARAMOUNT: this cache sits on the convergence path. A wrong
cache HIT == a wrong scientific review. Every key-sensitivity test below
asserts that a change to ANY review-determining input forces a fresh model
call (cache MISS). A HIT must be byte-for-byte equivalent to a fresh call's
INPUTS, and must round-trip the stored Concern list exactly.

The fake backend COUNTS calls (no model mock): each ``chat`` call pops one
canned response and increments ``calls``. A HIT that skips the backend
leaves ``calls`` unchanged; a MISS increments it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.convergence import review_cache
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import Concern, Severity
from llmxive.model_selection.types import RequirementOverrides

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --- fake backend that COUNTS calls --------------------------------------


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _CountingBackend:
    """Returns canned responses and counts every ``chat`` invocation."""

    responses: list[str]
    calls: int = field(default=0)

    def chat(self, messages, model=None, **kwargs):  # type: ignore[no-untyped-def]
        self.calls += 1
        if not self.responses:
            raise RuntimeError("out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


_VALID_RESPONSE = """\
---
reviewer_name: requirements_coverage
reviewer_kind: llm
stage: clarified
artifact_path: specs/000-x/spec.md
artifact_hash: abc123
verdict: minor_revision
concerns:
  - severity: requirement
    location: "FR-002"
    text: "FR-002 has no corresponding success criterion"
---

The spec declares FR-002 but never ties it to a measurable outcome.
"""

_ARTIFACTS = {"specs/000-x/spec.md": "# spec\n- FR-002: do Y\n"}


def _reviewer(backend, *, lens="requirements_coverage", stage="clarified",
              repo_root=_REPO_ROOT, profile="deep_review"):
    return LLMReviewer(
        lens=lens, stage=stage, backend=backend,
        repo_root=repo_root, profile=profile,
    )


@pytest.fixture(autouse=True)
def _enable_cache(monkeypatch):
    """Default ENABLED for every test (kill-switch test overrides)."""
    monkeypatch.delenv("LLMXIVE_CONVERGENCE_CACHE", raising=False)
    monkeypatch.delenv("LLMXIVE_CONVERGENCE_CACHE_TTL_DAYS", raising=False)


# --- HIT skips the model -------------------------------------------------


def test_hit_skips_the_model(tmp_path):
    backend = _CountingBackend(responses=[_VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=tmp_root_with_prompts(tmp_path))
    first = rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1, "first identify() must call the backend once"
    # Second identical identify(): HIT, zero additional backend calls.
    second = rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1, "HIT must NOT call the backend again"
    assert len(first) == len(second) == 1


def test_round_trip_fidelity(tmp_path):
    backend = _CountingBackend(responses=[_VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=tmp_root_with_prompts(tmp_path))
    fresh = rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    cached = rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1
    assert len(fresh) == len(cached) == 1
    a, b = fresh[0], cached[0]
    assert a.id == b.id
    assert a.reviewer == b.reviewer
    assert a.severity == b.severity == Severity.REQUIREMENT
    assert a.artifact == b.artifact
    assert a.location == b.location
    assert a.text == b.text
    assert a.round == b.round


# --- key sensitivity: each MUST cause a MISS (new backend call) ----------


def _two_calls_changing(tmp_path, *, second_kwargs=None, second_artifacts=None,
                        lens="requirements_coverage", stage="clarified",
                        profile="deep_review", second_profile="__same__"):
    """Run identify() twice; the second varies ONE input. Returns the
    backend so the caller can assert ``calls == 2`` (a MISS)."""
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev1 = _reviewer(backend, lens=lens, stage=stage, repo_root=root, profile=profile)
    rev1.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1
    return backend, root


def test_miss_on_changed_artifact_text(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    rev.identify({"specs/000-x/spec.md": "# spec\n- FR-002: DIFFERENT\n"},
                 constitution=None, advisory=[])
    assert backend.calls == 2


def test_miss_on_changed_constitution(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution="C-ONE", advisory=[])
    rev.identify(_ARTIFACTS, constitution="C-TWO", advisory=[])
    assert backend.calls == 2


def test_miss_on_changed_advisory(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=["a1"])
    rev.identify(_ARTIFACTS, constitution=None, advisory=["a2"])
    assert backend.calls == 2


def test_miss_on_changed_system_prompt(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    # Mutate the lens prompt content → system prompt changes → MISS.
    rev._system_prompt = rev._system_prompt + "\nADDED RULE\n"
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


def test_miss_on_changed_lens(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev_a = _reviewer(backend, lens="requirements_coverage", repo_root=root)
    rev_b = _reviewer(backend, lens="internal_consistency", repo_root=root)
    rev_a.identify(_ARTIFACTS, constitution=None, advisory=[])
    rev_b.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


def test_miss_on_changed_stage(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev_a = _reviewer(backend, lens="requirements_coverage",
                      stage="clarified", repo_root=root)
    # Same lens prompt exists for a different stage? Build via direct key
    # injection: vary stage only, keep system prompt identical, to prove
    # stage alone is part of the key.
    rev_b = _reviewer(backend, lens="requirements_coverage",
                      stage="clarified", repo_root=root)
    rev_b._stage = "paper_clarified"
    rev_a.identify(_ARTIFACTS, constitution=None, advisory=[])
    rev_b.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


def test_miss_on_changed_profile(tmp_path):
    """Spec 026 slice 7: the cache key binds the named capability PROFILE
    (there is no raw model id to pin anymore) — two reviewers that differ
    only in profile must MISS each other's cache entry."""
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev_a = _reviewer(backend, profile="deep_review", repo_root=root)
    rev_b = _reviewer(backend, profile="deep_code", repo_root=root)
    rev_a.identify(_ARTIFACTS, constitution=None, advisory=[])
    rev_b.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


# --- TTL -----------------------------------------------------------------


def test_expired_entry_is_a_miss(tmp_path, monkeypatch):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1
    # Force the TTL to negative → every stored entry is expired → MISS.
    monkeypatch.setenv("LLMXIVE_CONVERGENCE_CACHE_TTL_DAYS", "-1")
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


def test_old_timestamp_entry_is_a_miss(tmp_path, monkeypatch):
    """Write an entry, then advance the clock past the default TTL."""
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1
    # Advance the cache clock by 100 days (default TTL is 14 days).
    real_now = review_cache._now()
    monkeypatch.setattr(review_cache, "_now", lambda: real_now + 100 * 24 * 3600)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


# --- kill-switch ---------------------------------------------------------


def test_kill_switch_disables_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_CONVERGENCE_CACHE", "0")
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    # Disabled → never reads/writes → both calls hit the backend.
    assert backend.calls == 2
    # And NOTHING was persisted.
    cache_dir = review_cache.convergence_cache_dir(root)
    assert not cache_dir.exists() or not any(cache_dir.iterdir())


def test_kill_switch_false_string_disables_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMXIVE_CONVERGENCE_CACHE", "false")
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2


# --- robustness ----------------------------------------------------------


def test_corrupt_cache_file_is_a_miss_no_crash(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 1
    # Corrupt every cache file on disk.
    cache_dir = review_cache.convergence_cache_dir(root)
    for f in cache_dir.glob("*.json"):
        f.write_text("{ this is not valid json")
    # Corrupt read must be swallowed → MISS → normal model call, no crash.
    out = rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert backend.calls == 2
    assert len(out) == 1


def test_disabled_behaves_identically_to_today(tmp_path, monkeypatch):
    """When disabled, identify() returns the same parsed concerns it
    always would (pure-addition invariant)."""
    monkeypatch.setenv("LLMXIVE_CONVERGENCE_CACHE", "0")
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE])
    rev = _reviewer(backend, repo_root=root)
    concerns = rev.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert len(concerns) == 1
    assert concerns[0].severity == Severity.REQUIREMENT
    assert concerns[0].text.startswith("FR-002")


# --- direct cache-module unit tests --------------------------------------


def test_cache_module_round_trip(tmp_path):
    concerns = [
        Concern(id="C1", reviewer="lens", severity=Severity.SCIENCE,
                artifact="a.md", location="L1", text="t1", round=1),
        Concern(id="C2", reviewer="lens", severity=Severity.TRIVIAL,
                artifact="a.md", location="", text="t2", round=1),
    ]
    key = review_cache.compose_key(
        user="U", system="S", lens="lens", stage="clarified",
        profile="deep_review", selection_policy_version=1,
        temperature=0.0, max_tokens=32_768,
    )
    review_cache.store(tmp_path, key, concerns)
    got = review_cache.load(tmp_path, key)
    assert got is not None
    assert [c.model_dump() for c in got] == [c.model_dump() for c in concerns]


def test_cache_key_is_deterministic_and_sensitive():
    """Spec 026 slice 7: the key hashes ``profile`` + ``selection_policy_version``
    (a real int) in place of the retired raw model-id pin — every
    review-determining input, string or int, must independently move the key."""
    base = dict(user="U", system="S", lens="L", stage="ST",
                profile="deep_review", selection_policy_version=1,
                temperature=0.0, max_tokens=32_768)
    k = review_cache.compose_key(**base)
    assert k == review_cache.compose_key(**base)
    assert len(k) == 64
    for field_name in ("user", "system", "lens", "stage", "profile"):
        changed = dict(base)
        changed[field_name] = base[field_name] + "X"
        assert review_cache.compose_key(**changed) != k, (
            f"changing {field_name} must change the key"
        )
    changed_version = dict(base)
    changed_version["selection_policy_version"] = base["selection_policy_version"] + 1
    assert review_cache.compose_key(**changed_version) != k, (
        "changing selection_policy_version must change the key"
    )


def test_cache_key_none_and_default_overrides_are_identical():
    """``overrides=None`` (no override object at all) and an all-default
    ``RequirementOverrides()`` are semantically IDENTICAL to ``route_chat``
    (both mean "no escalation constraints"). They MUST canonicalize to the
    SAME key, or a no-override run would spuriously MISS a no-override
    cache entry written by a caller that happened to pass an explicit
    default instance."""
    base = dict(user="U", system="S", lens="L", stage="ST",
                profile="deep_review", selection_policy_version=1,
                temperature=0.0, max_tokens=32_768)
    assert (
        review_cache.compose_key(**base, overrides=None)
        == review_cache.compose_key(**base, overrides=RequirementOverrides())
    )


def test_cache_key_sensitive_to_overrides():
    """FINDING 1 (BLOCKER) regression: two effective ``RequirementOverrides``
    that differ MUST produce different keys, or an escalation rung (e.g.
    tier 1's ``exclude_leader=True``) would silently reuse a prior tier's
    cached review instead of reaching the model."""
    base = dict(user="U", system="S", lens="L", stage="ST",
                profile="deep_review", selection_policy_version=1,
                temperature=0.0, max_tokens=32_768)
    k_none = review_cache.compose_key(**base, overrides=None)
    k_exclude_leader = review_cache.compose_key(
        **base, overrides=RequirementOverrides(exclude_leader=True)
    )
    k_require_paid = review_cache.compose_key(
        **base, overrides=RequirementOverrides(require_paid=True)
    )
    k_exclude_models = review_cache.compose_key(
        **base, overrides=RequirementOverrides(exclude_models=frozenset({"m1"}))
    )
    k_max_credits = review_cache.compose_key(
        **base, overrides=RequirementOverrides(max_credits=5)
    )
    k_allow_paid = review_cache.compose_key(
        **base, overrides=RequirementOverrides(allow_paid=True)
    )
    keys = [k_none, k_exclude_leader, k_require_paid, k_exclude_models,
            k_max_credits, k_allow_paid]
    assert len(set(keys)) == len(keys), "every distinct overrides value must move the key"


def test_cache_key_overrides_field_order_independent_but_field_sensitive():
    """``exclude_models`` is a ``frozenset`` (unordered) — the canonicalization
    must sort it so key equality doesn't depend on set iteration order."""
    base = dict(user="U", system="S", lens="L", stage="ST",
                profile="deep_review", selection_policy_version=1,
                temperature=0.0, max_tokens=32_768)
    ov_a = RequirementOverrides(exclude_models=frozenset({"m1", "m2"}))
    ov_b = RequirementOverrides(exclude_models=frozenset({"m2", "m1"}))
    assert (
        review_cache.compose_key(**base, overrides=ov_a)
        == review_cache.compose_key(**base, overrides=ov_b)
    )


# --- Finding 1 (BLOCKER) regression: escalation overrides bust the cache ---
#
# Tier 0 caches a review; the panel escalates (bump_model_tier) and tier 1
# dispatches with RequirementOverrides(exclude_leader=True) — the "free
# second opinion" rung. Before the fix, compose_key ignored overrides
# entirely, so identify() returned the tier-0 cached review WITHOUT ever
# reaching route_chat — silently defeating escalation. These tests drive
# the REAL LLMReviewer.identify() path and monkeypatch the TRUE routing
# chokepoint (llmxive.model_selection.route.route_chat, one level below
# chat_with_model_fallback — see test_slice7_review_panel_profile_propagation.py)
# to prove whether routing was actually reached, not merely that the keys differ.


def test_tier1_overrides_miss_tier0_cache_and_reach_route_chat(tmp_path, monkeypatch):
    root = tmp_root_with_prompts(tmp_path)
    seen: list[dict[str, Any]] = []

    def _fake_route_chat(messages, **kw):  # type: ignore[no-untyped-def]
        seen.append(kw)
        return ChatResponse(text=_VALID_RESPONSE, model="m", backend="dartmouth")

    monkeypatch.setattr("llmxive.model_selection.route.route_chat", _fake_route_chat)

    backend = _CountingBackend(responses=[])  # never reached directly; route_chat is faked
    rev_tier0 = _reviewer(backend, repo_root=root, profile="deep_review")
    rev_tier1 = LLMReviewer(
        lens="requirements_coverage", stage="clarified", backend=backend,
        repo_root=root, profile="deep_review",
        overrides=RequirementOverrides(exclude_leader=True),
    )

    rev_tier0.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert len(seen) == 1, "tier-0 identify() must reach route_chat (cold cache)"
    assert seen[0].get("overrides") is None

    # Tier-1 override MUST NOT be served the tier-0 cache entry: it must
    # independently reach route_chat with its OWN overrides.
    rev_tier1.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert len(seen) == 2, (
        "tier-1 identify() incorrectly served the tier-0 cache entry — "
        "escalation overrides did not bust the cache key"
    )
    assert seen[1]["overrides"] == RequirementOverrides(exclude_leader=True)


def test_none_and_default_overrides_reviewers_hit_same_cache_entry(tmp_path, monkeypatch):
    """A reviewer with ``overrides=None`` and a separately-constructed reviewer
    with an explicit all-default ``RequirementOverrides()`` must be treated as
    the SAME escalation state — a HIT, not a spurious MISS."""
    root = tmp_root_with_prompts(tmp_path)
    seen: list[dict[str, Any]] = []

    def _fake_route_chat(messages, **kw):  # type: ignore[no-untyped-def]
        seen.append(kw)
        return ChatResponse(text=_VALID_RESPONSE, model="m", backend="dartmouth")

    monkeypatch.setattr("llmxive.model_selection.route.route_chat", _fake_route_chat)

    backend = _CountingBackend(responses=[])
    rev_none = LLMReviewer(
        lens="requirements_coverage", stage="clarified", backend=backend,
        repo_root=root, profile="deep_review", overrides=None,
    )
    rev_default = LLMReviewer(
        lens="requirements_coverage", stage="clarified", backend=backend,
        repo_root=root, profile="deep_review", overrides=RequirementOverrides(),
    )

    rev_none.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert len(seen) == 1
    rev_default.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert len(seen) == 1, "default RequirementOverrides() must HIT the None-overrides cache entry"


# --- helper: a tmp repo root carrying the real panel prompts -------------


def tmp_root_with_prompts(tmp_path: Path) -> Path:
    """Create an isolated repo root whose ``agents/prompts`` tree is a copy
    of the real one (so LLMReviewer can load its system prompt) but whose
    ``state/`` is empty (so the cache writes into the test's tmp dir).

    Using a tmp root keeps each test's cache hermetic — no cross-test
    contamination and no writes into the real repo's state/ dir.
    """
    import shutil

    prompts_src = _REPO_ROOT / "agents" / "prompts"
    prompts_dst = tmp_path / "agents" / "prompts"
    prompts_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(prompts_src, prompts_dst)
    return tmp_path


def test_cache_key_sensitive_to_sampling_settings():
    """``LLMReviewer`` exposes ``temperature`` and ``max_tokens`` as constructor
    parameters, and both are review-DETERMINING: temperature changes what the
    model produces from identical inputs, and max_tokens changes where a long
    review is truncated. Without binding them, a reviewer configured at
    temperature 0.7 would be served the deterministic reviewer's cached
    concerns. They are invariant across the standard production panel today —
    this test keeps ``compose_key``'s "ALL review-determining inputs" claim
    true if that ever stops being so."""
    base = dict(user="U", system="S", lens="L", stage="ST",
                profile="deep_review", selection_policy_version=1)
    k = review_cache.compose_key(**base, temperature=0.0, max_tokens=32_768)
    assert review_cache.compose_key(**base, temperature=0.7, max_tokens=32_768) != k, (
        "a different temperature must MISS — it changes what the model emits"
    )
    assert review_cache.compose_key(**base, temperature=0.0, max_tokens=8_192) != k, (
        "a different max_tokens must MISS — it changes where the review truncates"
    )
    assert review_cache.compose_key(**base, temperature=0.0, max_tokens=None) != k, (
        "an unbounded max_tokens must MISS against a bounded one"
    )
    # ...and identical settings still HIT.
    assert review_cache.compose_key(**base, temperature=0.0, max_tokens=32_768) == k
