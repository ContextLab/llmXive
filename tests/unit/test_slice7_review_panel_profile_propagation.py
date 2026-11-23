"""Spec 026 Slice 7 gap fix: the convergence REVIEW PANEL was missed by the
model-selection migration (issue tracked in ``.superpowers/sdd/fix-f2-report.md``).

``reviewspecs.py`` imported ``llmxive.backends.router.DEFAULT_MODEL`` and every
``build_*_reviewspec`` builder pinned it via ``model=DEFAULT_MODEL``, forwarded
through ``_wire_live_panel`` -> ``build_panel`` -> ``LLMReviewer.__init__`` ->
``chat_with_model_fallback(..., model=self._model)``. That promotes the legacy
model id as ``caller_model`` at the routing chokepoint, contradicting FR-012/
FR-013 (every call site expresses intent via a named PROFILE, never a raw model
id pin) and blocking Slice 8 (which must delete ``DEFAULT_MODEL`` — impossible
while ``reviewspecs.py`` imports it).

This test proves the FIX: a LIVE panel built by the production
``build_plan_reviewspec`` factory reaches ``llmxive.model_selection.route.route_chat``
— the actual routing chokepoint one level BELOW ``chat_with_model_fallback`` —
with ``profile="deep_review"`` and ``caller_model=None`` for every reviewer,
including across the panel's ThreadPoolExecutor dispatch path
(``llmxive.convergence.engine._map_reviewers``, the same dispatch the R1
``identify`` phase uses). A test that only inspects ``LLMReviewer._profile``
would NOT prove this — the value must actually arrive at ``route_chat``.

Reuses the pattern established in ``test_slice6_override_propagation.py``: a
REAL backend object + a REAL ``build_plan_reviewspec``-constructed panel + the
REAL engine ThreadPoolExecutor runner (Constitution III — no mocks of the unit
under test). Only the network boundary is monkeypatched to capture the
forwarded kwargs — here that boundary is ``model_selection.route.route_chat``
itself (one level deeper than slice6's ``chat_with_model_fallback`` capture),
since the whole point is to prove the value survives the ``_walker_route``
hop, not merely a wrapper rename.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llmxive.backends.base import ChatResponse
from llmxive.convergence import engine
from llmxive.convergence.reviewspecs import build_plan_reviewspec

_REPO_ROOT = Path(__file__).resolve().parents[2]

_ACCEPT_REVIEW = "---\nreviewer_name: x\nverdict: accept\nconcerns: []\n---\n"
_ARTIFACTS = {"projects/P/specs/000-x/plan.md": "## Plan\n- do X\n"}


class _FakeBackend:
    """Real, minimal backend object. ``route_chat`` is monkeypatched below, so
    ``chat`` is never actually reached — but a non-None backend is required for
    ``_wire_live_panel`` to build the LIVE LLMReviewer panel (rather than keep
    the static ``_TodoReviewer`` placeholders)."""

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        return ChatResponse(text=_ACCEPT_REVIEW, model=model or "m", backend="dartmouth")


def _disable_review_cache(monkeypatch) -> None:
    """Force a cache MISS + no-op store so every reviewer actually calls the
    (monkeypatched) routing chokepoint on the real ``identify`` path."""
    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.review_cache.load", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.review_cache.store", lambda *a, **k: None
    )


def test_live_panel_reaches_route_chat_with_deep_review_profile_and_no_caller_model(
    monkeypatch,
):
    seen: list[dict[str, Any]] = []

    def _fake_route_chat(messages, **kw):  # type: ignore[no-untyped-def]
        seen.append(kw)
        return ChatResponse(text=_ACCEPT_REVIEW, model="m", backend="dartmouth")

    # The TRUE routing chokepoint: ``_walker_route`` (inside
    # ``chat_with_model_fallback``) does a function-local
    # ``from llmxive.model_selection.route import route_chat`` on every call,
    # so patching the module attribute is picked up live.
    monkeypatch.setattr("llmxive.model_selection.route.route_chat", _fake_route_chat)
    _disable_review_cache(monkeypatch)

    spec = build_plan_reviewspec(
        backend=_FakeBackend(), repo_root=_REPO_ROOT, project_id="PROJ-900-panel-profile",
    )

    # The REAL engine panel runner — bounded ThreadPoolExecutor over the 5
    # plan lenses (default concurrency >1 -> the pool path fires, not the
    # serial path). This is the SAME dispatch the engine's R1 ``identify``
    # phase uses.
    engine._map_reviewers(
        spec.reviewers,
        lambda r: r.identify(_ARTIFACTS, constitution=None, advisory=[]),
    )

    assert len(seen) == len(spec.reviewers) >= 2
    # Every concurrent reviewer's call reached route_chat carrying the
    # review-lens profile — never a raw model id pin (FR-012/FR-013).
    assert all(kw.get("profile") == "deep_review" for kw in seen), seen
    # No caller model pin (the retired DEFAULT_MODEL is gone from this path).
    assert all(kw.get("caller_model") is None for kw in seen), seen
