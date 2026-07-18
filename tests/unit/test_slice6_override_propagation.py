"""Spec 026 Slice 6: ``RequirementOverrides`` threading (escalation constraints).

Proves the typed escalation-constraint channel rides ALONGSIDE the existing
``model=`` channel, from the speckit ``SlashCommandContext`` down to
``chat_with_fallback``, and from ``build_*_reviewspec`` down to BOTH the panel
reviewers (``chat_with_model_fallback``) AND the reviser (``reasoning_chat``),
including the REAL concurrent panel-execution path (the engine's
ThreadPoolExecutor runner). Default ``None`` everywhere keeps existing callers
unchanged.

Constitution III: the captured/asserted objects are REAL — the immutable
``RequirementOverrides`` value, real ``LLMReviewer``/reviser instances built by
the production ``build_plan_reviewspec`` factory, and the real engine panel
runner. Only the network boundary (``chat_with_fallback`` /
``chat_with_model_fallback`` / ``reasoning_chat``) is monkeypatched to capture
the forwarded value — a module-symbol capture, not a mock object.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.convergence import engine
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.reviewspecs import build_plan_reviewspec
from llmxive.convergence.revisers._self_consistency import invoke_reviser_backend
from llmxive.model_selection.types import RequirementOverrides
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.types import BackendName

_REPO_ROOT = Path(__file__).resolve().parents[2]

_ACCEPT_REVIEW = "---\nreviewer_name: x\nverdict: accept\nconcerns: []\n---\n"
_ARTIFACTS = {"projects/P/specs/000-x/plan.md": "## Plan\n- do X\n"}


class _FakeBackend:
    """Real, minimal backend object. The network calls are monkeypatched, so
    ``chat`` is never actually reached — but a non-None backend is required for
    ``_wire_live_panel`` to build the LIVE LLMReviewer panel (rather than keep
    the static placeholders)."""

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        return ChatResponse(text=_ACCEPT_REVIEW, model=model or "m", backend="dartmouth")


def _disable_review_cache(monkeypatch) -> None:
    """Force a cache MISS + no-op store so every reviewer actually calls the
    (monkeypatched) backend on the real ``identify`` path — the resumable review
    cache would otherwise short-circuit ``_call_backend``."""
    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.review_cache.load", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.review_cache.store", lambda *a, **k: None
    )


# --- (a) SlashCommandAgent.run forwards ctx.requirement_overrides ----------


class _RunnableSlashAgent(SlashCommandAgent):
    """Minimal concrete agent — every abstract method is a trivial real impl."""

    def slash_command_name(self) -> str:
        return "speckit.test"

    def mechanical_step(self, ctx: SlashCommandContext) -> dict[str, Any]:
        return {}

    def build_prompt(self, ctx, mechanical_output):  # type: ignore[no-untyped-def]
        return [ChatMessage(role="user", content="hi")]

    def write_artifacts(self, ctx, mechanical_output, llm_response):  # type: ignore[no-untyped-def]
        return []


def _min_ctx(*, requirement_overrides) -> SlashCommandContext:
    return SlashCommandContext(
        project_id="PROJ-001-test",
        project_dir=Path("/tmp/llmxive-test/projects/PROJ-001-test"),
        run_id="r",
        task_id="t",
        inputs=[],
        expected_outputs=[],
        prompt_template_path=Path("/tmp/x.md"),
        default_backend=BackendName.DARTMOUTH,
        fallback_backends=[],
        default_model="m",
        prompt_version="1.0.0",
        agent_name="a",
        requirement_overrides=requirement_overrides,
    )


def test_slashcommand_run_forwards_overrides(monkeypatch):
    captured: dict[str, Any] = {}

    def _fake_chat_with_fallback(messages, **kw):
        captured.update(kw)
        return ChatResponse(text="ok", model="m", backend="dartmouth")

    monkeypatch.setattr(
        "llmxive.speckit.slash_command.chat_with_fallback", _fake_chat_with_fallback
    )
    # Keep the run-log side-effect off the real repo (not under test).
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.runlog.append_entry", lambda entry: None
    )

    ov = RequirementOverrides(allow_paid=False)
    ctx = _min_ctx(requirement_overrides=ov)
    _RunnableSlashAgent().run(ctx)

    assert captured["overrides"] is ov


def test_slashcommand_run_default_is_none(monkeypatch):
    """Existing callers (no requirement_overrides) forward the None default."""
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.chat_with_fallback",
        lambda messages, **kw: (captured.update(kw), ChatResponse(text="ok", model="m", backend="dartmouth"))[1],
    )
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.runlog.append_entry", lambda entry: None
    )
    ctx = _min_ctx(requirement_overrides=None)
    _RunnableSlashAgent().run(ctx)
    assert captured["overrides"] is None


# --- (b) LLMReviewer carries + forwards overrides --------------------------


def test_reviewer_carries_overrides_and_forwards(monkeypatch):
    captured: dict[str, Any] = {}

    def _fake_cmf(backend, messages, **kw):
        captured.update(kw)
        return ChatResponse(text=_ACCEPT_REVIEW, model="m", backend="dartmouth")

    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake_cmf
    )
    _disable_review_cache(monkeypatch)

    r = LLMReviewer(
        lens="requirements_coverage",
        stage="clarified",
        backend=_FakeBackend(),
        repo_root=_REPO_ROOT,
        model=None,
        overrides=RequirementOverrides(require_paid=True),
    )
    r.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert captured["overrides"].require_paid is True


def test_reviewer_default_overrides_none(monkeypatch):
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.chat_with_model_fallback",
        lambda backend, messages, **kw: (captured.update(kw), ChatResponse(text=_ACCEPT_REVIEW, model="m", backend="dartmouth"))[1],
    )
    _disable_review_cache(monkeypatch)
    r = LLMReviewer(
        lens="requirements_coverage", stage="clarified",
        backend=_FakeBackend(), repo_root=_REPO_ROOT, model=None,
    )
    r.identify(_ARTIFACTS, constitution=None, advisory=[])
    assert captured["overrides"] is None


# --- (c) CONCURRENCY: every reviewer forwards the SAME immutable value ------


def test_concurrent_reviewers_share_immutable_override_via_real_path(monkeypatch):
    seen: list[Any] = []

    def _fake_cmf(backend, messages, **kw):
        seen.append(kw.get("overrides"))
        return ChatResponse(text=_ACCEPT_REVIEW, model="m", backend="dartmouth")

    monkeypatch.setattr(
        "llmxive.convergence.llm_reviewer.chat_with_model_fallback", _fake_cmf
    )
    _disable_review_cache(monkeypatch)

    ov = RequirementOverrides(allow_paid=True, require_paid=True)
    spec = build_plan_reviewspec(
        backend=_FakeBackend(), repo_root=_REPO_ROOT, project_id="P",
        model=None, requirement_overrides=ov,
    )
    # The real engine panel runner — bounded ThreadPoolExecutor over the 5 plan
    # lenses (default concurrency 8 → the pool path fires, not the serial path).
    # This is the SAME dispatch the engine's R1 ``identify`` phase uses.
    engine._map_reviewers(
        spec.reviewers,
        lambda r: r.identify(_ARTIFACTS, constitution=None, advisory=[]),
    )

    assert len(seen) == len(spec.reviewers) >= 2
    # Every concurrent reviewer forwarded the SAME immutable object — no copy,
    # no per-review mutation (RequirementOverrides is frozen).
    assert all(o is ov for o in seen)


# --- (d) reviser DECLARED _overrides field reaches reasoning_chat ----------


def test_reviser_declared_overrides_field_reaches_reasoning_chat(monkeypatch):
    captured: dict[str, Any] = {}

    def _fake_reasoning_chat(backend, messages, **kw):
        captured.update(kw)
        return ChatResponse(text="ok", model="m", backend="dartmouth")

    monkeypatch.setattr(
        "llmxive.convergence.revisers._self_consistency.reasoning_chat",
        _fake_reasoning_chat,
    )

    ov = RequirementOverrides(allow_paid=True)
    spec = build_plan_reviewspec(
        backend=_FakeBackend(), repo_root=_REPO_ROOT, project_id="P",
        model=None, requirement_overrides=ov,
    )
    invoke_reviser_backend(spec.reviser, [ChatMessage(role="user", content="x")])
    assert captured["overrides"] is ov
    assert captured["overrides"].allow_paid is True


def test_reviser_default_overrides_none(monkeypatch):
    """A reviser built WITHOUT overrides forwards the None default (back-compat
    for the placeholder revisers that lack the field, via getattr default)."""
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        "llmxive.convergence.revisers._self_consistency.reasoning_chat",
        lambda backend, messages, **kw: (captured.update(kw), ChatResponse(text="ok", model="m", backend="dartmouth"))[1],
    )
    spec = build_plan_reviewspec(
        backend=_FakeBackend(), repo_root=_REPO_ROOT, project_id="P", model=None,
    )
    invoke_reviser_backend(spec.reviser, [ChatMessage(role="user", content="x")])
    assert captured["overrides"] is None


# --- (e) research-tasks bridge: run_tasker_via_engine forwards overrides ----


def test_tasker_bridge_forwards_overrides_to_build_tasks_reviewspec(monkeypatch):
    """The research-``tasked`` stage runs its panel/reviser through the bridge
    ``run_tasker_via_engine``, which is called from ``tasks_cmd.py`` WITH a
    SlashCommandContext in scope. Assert the REAL bridge forwards the override
    to ``build_tasks_reviewspec``.

    Real-path choice: we drive the ACTUAL ``run_tasker_via_engine(...)`` (real
    function, real ``RequirementOverrides``, real backend object) and only stub
    the ``build_tasks_reviewspec`` boundary symbol to CAPTURE the forwarded
    kwarg + short-circuit (a sentinel raise) before the heavy engine run — the
    build call is the first thing the bridge does, so no real spec/plan/tasks
    files are needed. This exercises the exact seam under test end-to-end
    without a full engine execution (per the brief's guidance for a focused
    unit test)."""
    from llmxive.speckit import _tasker_engine_bridge as bridge

    captured: dict[str, Any] = {}

    class _StopHere(Exception):
        pass

    def _fake_build_tasks_reviewspec(**kw):
        captured.update(kw)
        raise _StopHere

    monkeypatch.setattr(bridge, "build_tasks_reviewspec", _fake_build_tasks_reviewspec)

    ov = RequirementOverrides(require_paid=True)
    with pytest.raises(_StopHere):
        bridge.run_tasker_via_engine(
            project_id="PROJ-001-test",
            repo_root=_REPO_ROOT,
            tasks_path=Path("/tmp/p/specs/001-x/tasks.md"),
            spec_path=Path("/tmp/p/specs/001-x/spec.md"),
            plan_path=Path("/tmp/p/specs/001-x/plan.md"),
            analyze_findings=[],
            backend=_FakeBackend(),
            requirement_overrides=ov,
        )
    assert captured["requirement_overrides"] is ov


def test_tasker_bridge_default_overrides_none(monkeypatch):
    """No override → the bridge forwards the None default (back-compat)."""
    from llmxive.speckit import _tasker_engine_bridge as bridge

    captured: dict[str, Any] = {}

    class _StopHere(Exception):
        pass

    def _fake_build_tasks_reviewspec(**kw):
        captured.update(kw)
        raise _StopHere

    monkeypatch.setattr(bridge, "build_tasks_reviewspec", _fake_build_tasks_reviewspec)

    with pytest.raises(_StopHere):
        bridge.run_tasker_via_engine(
            project_id="PROJ-001-test",
            repo_root=_REPO_ROOT,
            tasks_path=Path("/tmp/p/specs/001-x/tasks.md"),
            spec_path=Path("/tmp/p/specs/001-x/spec.md"),
            plan_path=Path("/tmp/p/specs/001-x/plan.md"),
            analyze_findings=[],
            backend=_FakeBackend(),
        )
    assert captured["requirement_overrides"] is None
