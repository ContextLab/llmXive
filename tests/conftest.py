"""pytest conftest — gate real-call tests behind LLMXIVE_REAL_TESTS=1."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest


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
    if "real_call" in str(request.node.fspath):
        return
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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("LLMXIVE_REAL_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="set LLMXIVE_REAL_TESTS=1 to run real-call tests")
    for item in items:
        if "real_call" in item.nodeid.split("/"):
            item.add_marker(skip)
