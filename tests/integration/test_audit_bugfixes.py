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
