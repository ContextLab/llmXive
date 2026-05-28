"""Verification tests for the spec-015 audit bug fixes (US8).

Each test asserts a specific discrepancy from the design-doc audit is fixed.
Grows as US8 tasks land (T030..T036).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.prompts import render_prompt

_REPO = Path(__file__).resolve().parents[2]


def test_research_implementer_uses_research_code_prompt():
    """T030 / FR-035 (discrepancy #1): the research speckit implementer must use a
    research-CODE prompt (artifacts/verdict YAML), NOT the paper-revision LaTeX prompt."""
    src = (_REPO / "src" / "llmxive" / "speckit" / "implement_cmd.py").read_text()
    assert "agents/prompts/implementer_research.md" in src, \
        "research implementer should render implementer_research.md"

    prompt = render_prompt(
        "agents/prompts/implementer_research.md",
        {"project_id": "PROJ-001-x", "next_task_id": "T007"},
        repo_root=_REPO,
    )
    # research-code contract present, task id substituted
    assert "verdict:" in prompt and "artifacts:" in prompt
    assert "T007" in prompt and "{{" not in prompt
    # the LaTeX paper-revision instructions must NOT leak into the research prompt
    assert "search_and_replace" not in prompt
    assert "unified_diff" not in prompt
    assert "LaTeX source" not in prompt


def test_research_implementer_prompt_file_exists_and_is_not_the_latex_one():
    research = (_REPO / "agents" / "prompts" / "implementer_research.md").read_text()
    latex = (_REPO / "agents" / "prompts" / "implementer.md").read_text()
    assert research != latex
    # the LaTeX prompt remains (used by the separate paper-revision agent)
    assert "peer-reviewed paper's LaTeX source" in latex
    # the research prompt is about code/data artifacts
    assert "code and data artifacts" in research


# ---- T031 / FR-030 / discrepancy #4 : analyze prompts -----------------------


def test_analyze_system_prompt_path_is_actually_used():
    """T031 / discrepancy #4: ANALYZE_SYSTEM_PROMPT_PATH was defined but unused
    (analyze prompt hardcoded inline). The constant now points at a real prompt
    file that ``run_analyze`` actually loads via ``render_prompt``."""
    from llmxive.speckit import analyze_cmd
    assert analyze_cmd.ANALYZE_SYSTEM_PROMPT_PATH == "agents/prompts/analyze.md"
    target = _REPO / analyze_cmd.ANALYZE_SYSTEM_PROMPT_PATH
    assert target.exists(), f"analyze prompt missing: {target}"
    # source uses render_prompt with the path constant (not inline string)
    src = (_REPO / "src" / "llmxive" / "speckit" / "analyze_cmd.py").read_text()
    assert "render_prompt(ANALYZE_SYSTEM_PROMPT_PATHS" in src


def test_paper_analyze_uses_paper_appropriate_prompt():
    """T031 / discrepancy #4: the paper analyze loop must NOT reuse the research
    `tasker.md` prompt — it gets its own paper-appropriate analyze prompt."""
    from llmxive.speckit import analyze_cmd
    assert analyze_cmd.ANALYZE_SYSTEM_PROMPT_PATHS["paper"] == "agents/prompts/paper_analyze.md"
    paper_prompt = (_REPO / "agents" / "prompts" / "paper_analyze.md").read_text()
    research_prompt = (_REPO / "agents" / "prompts" / "analyze.md").read_text()
    assert paper_prompt != research_prompt
    # paper-specific lenses present
    assert "reader_scenario_coverage" in paper_prompt
    assert "claims_supported" in paper_prompt
    assert "required_sections_figures" in paper_prompt
    # paper_tasks_cmd passes kind="paper"
    paper_caller = (_REPO / "src" / "llmxive" / "speckit" / "paper_tasks_cmd.py").read_text()
    assert 'kind="paper"' in paper_caller


def test_analyze_includes_constitution_when_provided():
    """FR-030: the per-project constitution is a standard input to the analyze /
    identify phase from `specified` onward. ``run_analyze`` must include it in
    the user message when ``constitution_text`` is provided."""
    from unittest.mock import patch

    from llmxive.backends.base import ChatResponse
    from llmxive.speckit import analyze_cmd
    from llmxive.types import BackendName

    captured: dict = {}

    def _fake_chat(messages, **kw):
        captured["messages"] = list(messages)
        return ChatResponse(text="CLEAN", model="m", backend="dartmouth")

    with patch("llmxive.speckit.analyze_cmd.chat_with_fallback", _fake_chat):
        analyze_cmd.run_analyze(
            spec_text="SPEC", plan_text="PLAN", tasks_text="TASKS",
            default_backend=BackendName.DARTMOUTH, fallback_backends=[],
            default_model="qwen.qwen3.5-122b", repo_root=_REPO,
            constitution_text="CONST-PRINCIPLE-X",
        )
    assert captured, "chat_with_fallback was not invoked"
    user_msg = next(m.content for m in captured["messages"] if m.role == "user")
    assert "# constitution.md" in user_msg
    assert "CONST-PRINCIPLE-X" in user_msg


def test_analyze_rejects_unknown_kind():
    import pytest as _pt

    from llmxive.speckit import analyze_cmd
    from llmxive.types import BackendName
    with _pt.raises(ValueError):
        analyze_cmd.run_analyze(
            spec_text="", plan_text="", tasks_text="",
            default_backend=BackendName.DARTMOUTH, fallback_backends=[],
            default_model="m", repo_root=_REPO, kind="bogus",
        )


# ---- T032 / discrepancy #5 : dead escalation paths --------------------------


def test_clarifier_attempts_persistence_round_trip(tmp_path):
    """T032 (research clarifier side): attempts_so_far is now read from disk
    instead of hardcoded 0; bump persists; reset clears."""
    from llmxive.speckit._clarify_attempts import (
        bump_attempts,
        read_attempts,
        reset_attempts,
        write_human_input_needed,
    )
    mem = tmp_path / ".specify" / "memory"
    assert read_attempts(mem) == 0
    assert bump_attempts(mem) == 1
    assert bump_attempts(mem) == 2
    assert read_attempts(mem) == 2
    reset_attempts(mem)
    assert read_attempts(mem) == 0
    hin = write_human_input_needed(mem, "test reason")
    assert hin.exists() and "test reason" in hin.read_text()


def test_paper_clarifier_no_silent_resolved_by_default_stub():
    """T032 (paper side): paper_clarifier previously substituted a silent
    'Resolved by default' stub when patches were missing — a no-silent-shortcuts
    violation. It must now raise like the research clarifier does. (The phrase
    "Resolved by default" may remain in a doc/comment as historical reference;
    the executable stub substitution is what must be gone.)"""
    src = (_REPO / "src" / "llmxive" / "speckit" / "paper_clarify_cmd.py").read_text()
    # The exact runtime stub substitution must be gone.
    assert "Resolved by default; LLM clarifier could not pin" not in src, \
        "paper_clarifier still substitutes the silent 'Resolved by default' stub"
    # both clarifiers must reach the same loud-failure helpers
    assert "write_human_input_needed" in src
    assert "TASKER_MAX_REVISION_ROUNDS" in src


def _make_ctx(project_id: str, project_dir, agent_name: str):
    from pathlib import Path as _P

    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName
    return SlashCommandContext(
        project_id=project_id,
        project_dir=project_dir,
        run_id="t032-run",
        task_id="t032-task",
        inputs=[],
        expected_outputs=[],
        prompt_template_path=_P("/dev/null"),
        default_backend=BackendName.DARTMOUTH,
        fallback_backends=[],
        default_model="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        agent_name=agent_name,
    )


def test_clarifier_escalate_verdict_writes_human_input(tmp_path):
    """T032: when the LLM emits ``verdict: escalate`` the clarifier writes
    human_input_needed.yaml + raises (the path was previously dead)."""
    import pytest as _pt

    from llmxive.backends.base import ChatResponse
    from llmxive.speckit.clarify_cmd import ClarifierAgent

    proj = tmp_path / "projects" / "PROJ-T032-x"
    (proj / "specs" / "001-test").mkdir(parents=True)
    spec = proj / "specs" / "001-test" / "spec.md"
    spec.write_text("Some spec [NEEDS CLARIFICATION: what model?]", encoding="utf-8")

    agent = ClarifierAgent()
    ctx = _make_ctx("PROJ-T032-x", proj, "clarifier")
    mech = agent.mechanical_step(ctx)
    resp = ChatResponse(text='{"verdict": "escalate", "patches": []}', model="m", backend="dartmouth")

    with _pt.raises(RuntimeError, match="escalate"):
        agent.write_artifacts(ctx, mech, resp)
    hin = proj / ".specify" / "memory" / "human_input_needed.yaml"
    assert hin.exists(), "escalate verdict must write human_input_needed.yaml"


def test_paper_specifier_supplies_code_and_data_summary(tmp_path):
    """T033 (discrepancy #10): paper_specifier.md advertised code_summary /
    data_summary inputs the code never supplied. The build_prompt must now
    inject both, with content drawn from the project's code/ and data/ trees."""
    from llmxive.speckit.paper_specify_cmd import PaperSpecifierAgent

    proj = tmp_path / "projects" / "PROJ-T033-x"
    (proj / "code").mkdir(parents=True)
    (proj / "data").mkdir(parents=True)
    (proj / "code" / "baseline.py").write_text("def run(): pass\n", encoding="utf-8")
    (proj / "data" / "results.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (proj / "specs" / "001-x").mkdir(parents=True)
    (proj / "specs" / "001-x" / "spec.md").write_text("research spec body", encoding="utf-8")
    (proj / "paper" / ".specify" / "templates").mkdir(parents=True)
    (proj / "paper" / ".specify" / "templates" / "spec-template.md").write_text(
        "template body", encoding="utf-8",
    )
    (proj / "paper" / "specs").mkdir()

    from unittest.mock import patch
    agent = PaperSpecifierAgent()
    ctx = _make_ctx("PROJ-T033-x", proj, "paper_specifier")
    mech = {
        "FEATURE_NUM": "001", "FEATURE_DIR": str(proj / "paper" / "specs" / "001-x"),
        "BRANCH_NAME": "001-x",
    }
    # The system prompt file lives in the real repo; build_prompt uses
    # ctx.project_dir.parent.parent to find it. Stub it for this offline test —
    # the user-message content (code_summary / data_summary) is what we verify.
    with patch("llmxive.speckit.paper_specify_cmd.render_prompt", return_value="<system>"):
        msgs = agent.build_prompt(ctx, mech)
    user_msg = next(m.content for m in msgs if m.role == "user")
    assert "# code_summary" in user_msg
    assert "# data_summary" in user_msg
    # The actual files appear in the summaries.
    assert "baseline.py" in user_msg
    assert "results.csv" in user_msg


def test_clarifier_attempt_cap_writes_human_input(tmp_path):
    """T032: when the persisted attempt count reaches TASKER_MAX_REVISION_ROUNDS
    on a failing run, the clarifier escalates to human input."""
    import pytest as _pt
    import yaml as _yaml

    from llmxive.backends.base import ChatResponse
    from llmxive.config import TASKER_MAX_REVISION_ROUNDS
    from llmxive.speckit.clarify_cmd import ClarifierAgent

    proj = tmp_path / "projects" / "PROJ-T032-y"
    (proj / "specs" / "001-test").mkdir(parents=True)
    (proj / ".specify" / "memory").mkdir(parents=True)
    spec = proj / "specs" / "001-test" / "spec.md"
    spec.write_text("Spec [NEEDS CLARIFICATION: x]", encoding="utf-8")
    # Pre-seed attempts to one below the cap so this run trips it.
    (proj / ".specify" / "memory" / "clarifier_attempts.yaml").write_text(
        _yaml.safe_dump({"attempts": TASKER_MAX_REVISION_ROUNDS - 1}), encoding="utf-8",
    )

    agent = ClarifierAgent()
    ctx = _make_ctx("PROJ-T032-y", proj, "clarifier")
    mech = agent.mechanical_step(ctx)
    # Empty patches -> unresolved marker -> bump hits cap -> escalate.
    resp = ChatResponse(text='{"patches": []}', model="m", backend="dartmouth")

    with _pt.raises(RuntimeError, match="cap"):
        agent.write_artifacts(ctx, mech, resp)
    hin = proj / ".specify" / "memory" / "human_input_needed.yaml"
    assert hin.exists()
