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

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.convergence import engine
from llmxive.convergence.llm_reviewer import LLMReviewer
from llmxive.convergence.reviewspecs import build_plan_reviewspec
from llmxive.convergence.revisers._self_consistency import invoke_reviser_backend
from llmxive.model_selection.types import RequirementOverrides
from llmxive.pipeline import graph
from llmxive.speckit._stage_panel import StagePanelEscalation as _DispatchEscalation
from llmxive.speckit.slash_command import SlashCommandAgent, SlashCommandContext
from llmxive.state import execution_status as es
from llmxive.state import project as project_store
from llmxive.types import BackendName, Project, Stage

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


# --- (f) Task 7: graph DISPATCH computes + sets the tier's overrides -------
#
# Tasks (a)-(e) above prove overrides ride the whole way down ONCE something
# sets ``ctx.requirement_overrides``. Before Task 7 nothing did: the graph
# dispatch block (``run_one_step``, the ``elif agent_name in _SPECKIT_AGENTS``
# branch) always constructed ``SlashCommandContext`` with the field at its
# ``None`` default, so escalation only ever produced a log line — the
# ``execution_status.tier_overrides`` value never reached ``route_chat``.
# These tests drive the REAL ``graph.run_one_step`` dispatch over a synthetic
# on-disk repo and a REAL ``execution_status`` tier record (Constitution III
# — no mocks of the unit under test). Only the speckit agent class + the
# registry/project-store collaborators are stubbed, the established pattern
# in test_implement_batching.py / test_convergence_kickback_flow.py. The stub
# agent's ``run(sk_ctx)`` captures the REAL, fully-constructed
# ``SlashCommandContext`` the graph builds, then raises
# ``StagePanelEscalation`` — the graph's own proven escape hatch (see
# ``test_run_one_step_keeps_project_schedulable_on_engine_failure`` in
# test_convergence_kickback_flow.py) that returns cleanly without touching
# any further routing machinery, so each test exercises ONLY the
# dispatch-construction code path under test.

_DISPATCH_DEFAULT_MODEL = "openai.gpt-oss-120b"


def _dispatch_stub_entry(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        prompt_path=Path("prompts/x.md"),
        default_backend="dartmouth",
        fallback_backends=[],
        default_model=_DISPATCH_DEFAULT_MODEL,
        prompt_version="1.0.0",
        name=name,
    )


def _dispatch_project(pid: str, stage: Stage) -> Project:
    now = datetime.now(UTC)
    return Project(
        id=pid,
        title="X",
        field="computer science",
        current_stage=stage,
        created_at=now,
        updated_at=now,
        speckit_research_dir="specs/001-x",
    )


def _dispatch_wire(monkeypatch, agent_name: str, agent_cls, project: Project) -> None:
    monkeypatch.setitem(graph._SPECKIT_AGENTS, agent_name, agent_cls)
    monkeypatch.setattr(
        graph.registry_loader, "get",
        lambda name, repo_root=None: _dispatch_stub_entry(name),
    )
    monkeypatch.setattr(project_store, "load", lambda pid, repo_root=None: project)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)


def _dispatch_capturing_agent(captured: dict):
    class _CaptureAgent:
        def run(self, sk_ctx) -> None:
            captured["ctx"] = sk_ctx
            raise _DispatchEscalation("capture-only stub — no real panel/LLM call")

    return _CaptureAgent


@pytest.mark.parametrize(
    ("pid", "stage", "agent_name"),
    [
        ("PROJ-950-tier1-exec", Stage.IN_PROGRESS, "implementer"),
        ("PROJ-951-tier1-panel", Stage.SPECIFIED, "clarifier"),
    ],
)
def test_dispatch_sets_tier1_overrides_matching_execution_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pid: str, stage: Stage, agent_name: str
) -> None:
    """For the two escalation-bearing dispatch paths (the IN_PROGRESS exec-fix
    implementer, and a doc-stage panel), at model_tier==1 the dispatched
    ``SlashCommandContext.requirement_overrides`` equals
    ``execution_status.tier_overrides(project.id, default_model=entry.
    default_model, repo_root=repo)`` EXACTLY — tier 1 excludes the registered
    default (``exclude_registered_default=True`` on the ladder's rung 1)."""
    project = _dispatch_project(pid, stage)
    new_tier = es.bump_model_tier(pid, repo_root=tmp_path)  # tier 0 -> 1
    assert new_tier == 1
    assert es.model_tier(pid, repo_root=tmp_path) == 1

    captured: dict = {}
    _dispatch_wire(monkeypatch, agent_name, _dispatch_capturing_agent(captured), project)

    graph.run_one_step(project, repo_root=tmp_path)

    ctx = captured.get("ctx")
    assert ctx is not None, "the agent-run boundary was never reached"

    expected = es.tier_overrides(
        pid, default_model=_DISPATCH_DEFAULT_MODEL, repo_root=tmp_path
    )
    assert ctx.requirement_overrides == expected
    # Pin the concrete tier-1 shape so a ladder regression is caught directly.
    assert ctx.requirement_overrides.allow_paid is False
    assert ctx.requirement_overrides.exclude_models == frozenset({_DISPATCH_DEFAULT_MODEL})
    assert ctx.default_model == _DISPATCH_DEFAULT_MODEL  # registered default untouched


@pytest.mark.parametrize(
    ("pid", "stage", "agent_name"),
    [
        ("PROJ-952-tier0-exec", Stage.IN_PROGRESS, "implementer"),
        ("PROJ-953-tier0-panel", Stage.SPECIFIED, "clarifier"),
    ],
)
def test_dispatch_sets_tier0_overrides_not_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pid: str, stage: Stage, agent_name: str
) -> None:
    """At tier 0 (no escalation yet — no execution_status record at all) the
    escalation-bearing stages still get a REAL RequirementOverrides object,
    not ``None``-through-default: a ``None`` here would silently defer to
    whatever per-call defaults the router applies elsewhere instead of
    pinning the explicit free-only tier-0 constraint (``allow_paid=False``)."""
    project = _dispatch_project(pid, stage)
    assert es.model_tier(pid, repo_root=tmp_path) == 0  # no record yet -> tier 0

    captured: dict = {}
    _dispatch_wire(monkeypatch, agent_name, _dispatch_capturing_agent(captured), project)

    graph.run_one_step(project, repo_root=tmp_path)

    ctx = captured.get("ctx")
    assert ctx is not None

    expected = es.tier_overrides(
        pid, default_model=_DISPATCH_DEFAULT_MODEL, repo_root=tmp_path
    )
    assert ctx.requirement_overrides == expected
    assert ctx.requirement_overrides is not None
    assert ctx.requirement_overrides.allow_paid is False
    assert ctx.requirement_overrides.exclude_models == frozenset()


def test_dispatch_leaves_overrides_none_for_non_escalation_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PROJECT_INITIALIZED -> specifier is neither the IN_PROGRESS exec-fix
    loop nor a panel stage in ``graph._STAGE_PANEL_LABEL`` — the tier ladder
    does not apply there (spec 026 slice 6 scopes escalation to the two
    autonomous loops), so dispatch must not compute/attach overrides even
    when the project's recorded tier is nonzero."""
    pid = "PROJ-954-no-escalation"
    project = _dispatch_project(pid, Stage.PROJECT_INITIALIZED)
    es.bump_model_tier(pid, repo_root=tmp_path)  # tier 1 — still unaffected here

    captured: dict = {}
    _dispatch_wire(monkeypatch, "specifier", _dispatch_capturing_agent(captured), project)

    graph.run_one_step(project, repo_root=tmp_path)

    ctx = captured.get("ctx")
    assert ctx is not None
    assert ctx.requirement_overrides is None
