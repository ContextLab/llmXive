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
