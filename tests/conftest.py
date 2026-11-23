"""pytest conftest — gate real-call tests behind LLMXIVE_REAL_TESTS=1."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

_TESTS_ROOT = Path(__file__).resolve().parent


def under_real_call(path: object) -> bool:
    """True when ``path`` is a test FILE inside ``tests/real_call``.

    The real-call gate classifies by the test file's path and NEVER by a node
    id. A node id embeds parameter values, so
    ``test_x[tests/real_call/test_y.py]`` — an offline test whose *parameter*
    happens to be a real-call path — would be gated as if it were itself a
    real-call test. A silently skipped test reads as a pass, so the regression
    it guards disappears without any CI signal.
    """
    candidate = Path(str(path))
    if not candidate.is_absolute():
        # pytest always hands this an absolute file path (``item.path`` /
        # ``node.fspath``). A relative string is therefore never a test file
        # here — it is a parameter value, and resolving it against the current
        # working directory is exactly how such a value used to be mistaken
        # for a real-call test.
        return False
    try:
        relative = candidate.resolve().relative_to(_TESTS_ROOT)
    except ValueError:
        return False
    return relative.parts[:1] == ("real_call",)


@pytest.fixture(autouse=True)
def _stub_task_verifier_backend(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default the independent task-verifier's LLM boundary to ACCEPT in offline
    tests (mirrors how ``test_task_verifier`` / ``relevance_judge`` tests stub the
    model boundary). The verifier runs a REAL ``chat_with_fallback`` after the
    implement batch (``pipeline.graph``); without a live backend it would DEFER
    every claimed task to ``[~]`` and stall every offline test that drives a
    project through ``in_progress``. The real-call suite (``LLMXIVE_REAL_TESTS=1``)
    exercises the genuine model — so it is left untouched here. Tests that
    specifically exercise reject/defer override this with their own monkeypatch.
    """
    if os.environ.get("LLMXIVE_REAL_TESTS") == "1":
        return
    if under_real_call(request.node.fspath):
        return
    # Isolated offline verdict receipts use a test key at the verifier boundary.
    # Do not set the process credential env: credential-loader and execution
    # environment tests must retain their own missing-key/secret behavior.
    monkeypatch.setattr(
        "llmxive.agents._task_verdict_receipt.load_signing_key",
        lambda: b"offline-task-verifier-receipt-test-only",
    )
    monkeypatch.setattr(
        "llmxive.agents.task_verifier.chat_with_fallback",
        lambda *a, **k: SimpleNamespace(
            text="VERDICT: COMPLETE\n(offline test stub — verifier accepts)",
            model="stub",
        ),
        raising=False,
    )


@pytest.fixture(autouse=True)
def _disable_convergence_cache_by_default(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default the resumable convergence panel-review cache OFF in tests.

    The cache (``llmxive.convergence.review_cache``) is content-addressed
    and persists under the reviewer's ``repo_root``. Most reviewer tests
    construct an ``LLMReviewer`` with ``repo_root`` pointing at the REAL
    repo, so a live cache would (a) write JSON files into the real
    ``state/convergence-cache/`` and (b) make a second ``identify()`` with
    identical inputs a HIT — which silently changes routing/parsing tests
    that intentionally re-use the same inputs with a different backend.

    Disabling the cache here restores byte-identical pre-cache behavior
    for every test that does not opt in. The dedicated cache suite
    (``test_convergence_review_cache.py``) re-enables it per-function with
    its own ``tmp_path`` repo roots, so its coverage is unaffected.
    """
    test_file = str(request.node.fspath)
    if test_file.endswith("test_convergence_review_cache.py"):
        return  # the cache's own suite controls the env explicitly
    monkeypatch.setenv("LLMXIVE_CONVERGENCE_CACHE", "0")


@pytest.fixture(autouse=True)
def _isolate_run_side_effect_flags() -> object:
    """Snapshot + restore the run-only feature flags that ``cli._cmd_run`` enables.

    For a REAL ``python -m llmxive run`` process, ``_cmd_run`` flips on the
    grounding-guard / claim-layer / claim-fill via ``os.environ.setdefault`` (so
    the deep reviser chokepoint sees them); the process then exits, so the global
    mutation is harmless there. But an in-process test that calls ``_cmd_run``
    (e.g. the ``run``-loop budget tests, or the ``--stage`` validation test) would
    LEAK those flags into whatever network-free test runs next — and the reviser
    suites assert EXACT backend call counts that those flags change, so the leak
    surfaces as an order-dependent failure (cli test before flesh_out reviser
    test). Restoring the three keys to their pre-test value makes a ``_cmd_run``
    call in one test never perturb another's environment. Real-call runs are
    exempt (they WANT the flags on).
    """
    if os.environ.get("LLMXIVE_REAL_TESTS") == "1":
        yield
        return
    keys = ("LLMXIVE_GROUNDING_GUARD", "LLMXIVE_CLAIM_LAYER", "LLMXIVE_CLAIM_FILL")
    before = {k: os.environ.get(k) for k in keys}
    yield
    for k, v in before.items():
        if v is None:
            os.environ.pop(k, None)
        elif os.environ.get(k) != v:
            os.environ[k] = v


_OFFLINE_SNAPSHOT = None


def _offline_snapshot(*_args, **_kwargs):
    """A fixed, deterministic free Dartmouth runtime snapshot for offline tests
    (built once): qwen3.5-122b → gemma-4-31B-it → gpt-oss-120b, all free + live."""
    global _OFFLINE_SNAPSHOT
    if _OFFLINE_SNAPSHOT is None:
        from datetime import UTC, datetime

        from llmxive.model_selection.snapshot import _family_of, _vendor_of
        from llmxive.model_selection.types import (
            CreditGuardSnapshot,
            ModelPricing,
            ModelRef,
            RuntimeSnapshot,
            SnapshotProvenance,
        )

        now = datetime(2026, 7, 17, 12, 0, 0, tzinfo=UTC)
        ep = "https://chat.dartmouth.edu"
        ids = ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
        models = tuple(
            ModelRef("dartmouth", ep, mid, _family_of(mid, _vendor_of(mid)), _vendor_of(mid))
            for mid in ids
        )
        credit = CreditGuardSnapshot(
            balance=1000.0, spend=0.0, max_budget=2000.0, paid_opt_in=False,
            budget_fraction=0.75, effective_cap=1500.0, available_headroom=1500.0,
            budget_reset_at="2026-07-18T03:45:00-04:00", observed_at=now, source="live",
        )
        sources = {
            comp: SnapshotProvenance("live", now, 0.0)
            for comp in ("catalog", "local", "credit")
        }
        _OFFLINE_SNAPSHOT = RuntimeSnapshot(
            models=models,
            pricing={mid: ModelPricing(0.0, 0.0) for mid in ids},
            health={m.model_id: "ok" for m in models},
            credit=credit, observed_at=now, sources=sources,
            digest="OFFLINE-TEST-SNAPSHOT",
        )
    return _OFFLINE_SNAPSHOT


@pytest.fixture(autouse=True)
def _offline_model_selection_snapshot(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch,
):
    """Serve model selection a DETERMINISTIC offline snapshot (spec 026 slice 5).

    ``chat_with_fallback`` / ``reasoning_chat`` / ``chat_with_model_fallback`` now
    delegate to ``model_selection.route.route_chat``, which acquires a NETWORKED
    ``runtime_snapshot`` before the pure ``select``. Offline that would hit
    Dartmouth (or fail closed). This stub pins the fixed free Dartmouth chain so an
    injected-fake reviser/reviewer/claims test — whose fake backend is threaded in
    as the ``dartmouth`` serving backend — deterministically serves the primary
    candidate, exactly as the pre-026 same-backend walk did. The bounded snapshot
    cache is reset around each test so nothing leaks. Real-call suites
    (LLMXIVE_REAL_TESTS=1 / tests/real_call) use the genuine networked snapshot.
    """
    if os.environ.get("LLMXIVE_REAL_TESTS") == "1" or "real_call" in str(request.node.fspath):
        yield
        return
    import llmxive.model_selection.route as route_mod

    route_mod.reset_snapshot_cache()
    monkeypatch.setattr(route_mod, "runtime_snapshot", _offline_snapshot)
    yield
    route_mod.reset_snapshot_cache()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("LLMXIVE_REAL_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="set LLMXIVE_REAL_TESTS=1 to run real-call tests")
    for item in items:
        if under_real_call(getattr(item, "path", None) or item.fspath):
            item.add_marker(skip)
