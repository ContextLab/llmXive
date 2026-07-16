"""Spec 026 (#10) — the DEDICATED local-backend real-call lane.

The composite snapshot lists the local transformers fallback (`Qwen/Qwen2.5-3B-
Instruct`); this proves it is REAL by loading the model and making an actual chat
call — not merely asserting the id is present. Marked ``local`` so the ordinary
suites deselect it. In the dedicated CI lane (the ``[local]`` extra installed +
``LLMXIVE_LOCAL_LANE=1``) an absent transformers is a FAILURE, never a skip
(``importorskip`` is deliberately NOT used there); outside the lane a dev without
the heavy dep skips it.
"""

from __future__ import annotations

import os

import pytest

from llmxive.backends.base import ChatMessage

pytestmark = [
    pytest.mark.local,
    pytest.mark.skipif(
        os.environ.get("LLMXIVE_REAL_TESTS") != "1",
        reason="real-call test; set LLMXIVE_REAL_TESTS=1",
    ),
]


def _require_transformers() -> None:
    try:
        import transformers  # noqa: F401
    except ImportError:
        if os.environ.get("LLMXIVE_LOCAL_LANE") == "1":
            raise  # dedicated lane: an absent [local] extra is a FAILURE, not a skip (#10)
        pytest.skip("transformers not installed — `pip install -e .[local]` to run this lane")


def test_local_backend_real_load_and_call() -> None:
    _require_transformers()
    from llmxive.backends.local import LocalBackend
    from llmxive.model_selection import runtime_snapshot

    # the model the composite snapshot advertises as the local fallback
    snap = runtime_snapshot()
    local_ids = [m.model_id for m in snap.models if m.backend == "local"]
    assert local_ids, "composite snapshot has no local-backend models"

    backend = LocalBackend()
    model = backend.list_models()[0]
    assert model in local_ids  # the snapshot and the backend agree on the inventory

    resp = backend.chat(
        [ChatMessage(role="user", content="Reply with exactly one word: ping")],
        model=model,
        max_tokens=16,
        temperature=0.0,
    )
    assert resp.text.strip(), "local model returned an empty completion"
    assert resp.model == model and resp.backend == "local"
