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

import pytest

from llmxive.convergence import review_cache
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.types import Concern, Severity

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
              repo_root=_REPO_ROOT, model=None):
    return LLMReviewer(
        lens=lens, stage=stage, backend=backend,
        repo_root=repo_root, model=model,
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
                        model=None, second_model="__same__"):
    """Run identify() twice; the second varies ONE input. Returns the
    backend so the caller can assert ``calls == 2`` (a MISS)."""
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev1 = _reviewer(backend, lens=lens, stage=stage, repo_root=root, model=model)
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


def test_miss_on_changed_model(tmp_path):
    root = tmp_root_with_prompts(tmp_path)
    backend = _CountingBackend(responses=[_VALID_RESPONSE, _VALID_RESPONSE])
    rev_a = _reviewer(backend, model="model-a", repo_root=root)
    rev_b = _reviewer(backend, model="model-b", repo_root=root)
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
        user="U", system="S", lens="lens", stage="clarified", model="m",
    )
    review_cache.store(tmp_path, key, concerns)
    got = review_cache.load(tmp_path, key)
    assert got is not None
    assert [c.model_dump() for c in got] == [c.model_dump() for c in concerns]


def test_cache_key_is_deterministic_and_sensitive():
    base = dict(user="U", system="S", lens="L", stage="ST", model="M")
    k = review_cache.compose_key(**base)
    assert k == review_cache.compose_key(**base)
    assert len(k) == 64
    for field_name in ("user", "system", "lens", "stage", "model"):
        changed = dict(base)
        changed[field_name] = base[field_name] + "X"
        assert review_cache.compose_key(**changed) != k, (
            f"changing {field_name} must change the key"
        )


def test_cache_key_model_none_distinct_from_empty():
    """model=None and model='' must not collide (different inputs)."""
    k_none = review_cache.compose_key(
        user="U", system="S", lens="L", stage="ST", model=None)
    k_empty = review_cache.compose_key(
        user="U", system="S", lens="L", stage="ST", model="")
    assert k_none != k_empty


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
