"""The research implementer must SEE the execution feedback (spec 023 #25).

The dedicated execution stage writes ``.specify/memory/execution_feedback.md``
(tracebacks + missing deliverables) and re-opens the failing tasks. If that note
is not delivered into the implementer's prompt, the auto-fix loop re-implements
the re-opened task blind and can never converge. These tests pin the delivery:
when the note exists it appears (verbatim, high-priority) in the user message;
when it does not, no execution-failure banner is injected.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.slash_command import SlashCommandContext


def _ctx(repo: Path, project_dir: Path) -> SlashCommandContext:
    return SlashCommandContext(
        project_id=project_dir.name,
        project_dir=project_dir,
        run_id="run-x",
        task_id="T010",
        inputs=["implementation_plan"],
        expected_outputs=["code", "data"],
        prompt_template_path=Path("agents/prompts/implementer_research.md"),
        default_backend="dartmouth",
        fallback_backends=["local"],
        default_model="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        agent_name="implementer",
    )


def _project(tmp_path: Path) -> Path:
    """A tmp repo whose ``agents/`` is the REAL prompt tree (symlinked), so
    ``render_prompt`` loads the production implementer prompt — no mocking."""
    repo = tmp_path / "repo"
    (repo / "projects").mkdir(parents=True)
    real_agents = Path(__file__).resolve().parents[2] / "agents"
    (repo / "agents").symlink_to(real_agents)
    proj = repo / "projects" / "PROJ-999-feedback-probe"
    (proj / "code").mkdir(parents=True)
    (proj / ".specify" / "memory").mkdir(parents=True)
    return proj


_MECH = {
    "all_complete": False,
    "next_task_id": "T010",
    "next_task_line": "- [ ] T010 Implement parser in code/data/parser.py",
    "tasks_text": "- [ ] T010 Implement parser in code/data/parser.py\n",
    "completed_task_ids": "T001 T002",
}


def test_execution_feedback_is_delivered_to_implementer(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    sentinel = "TypeError: KnotRecord.__init__() got an unexpected keyword 'data'"
    (proj / ".specify" / "memory" / "execution_feedback.md").write_text(
        "# Execution failures\n\n"
        "## Failing / missing run-book commands\n\n"
        f"- python code/data/parser.py -> rc=1\n    {sentinel}\n"
        "\n## Declared deliverables still missing\n\n"
        "- data/processed/knots_cleaned.csv\n",
        encoding="utf-8",
    )
    msgs = ImplementerAgent().build_prompt(_ctx(proj.parent.parent, proj), _MECH)
    user = msgs[-1].content
    assert "EXECUTION FAILED" in user
    assert sentinel in user
    assert "knots_cleaned.csv" in user


def test_no_feedback_banner_when_no_failure(tmp_path: Path) -> None:
    proj = _project(tmp_path)  # no execution_feedback.md written
    msgs = ImplementerAgent().build_prompt(_ctx(proj.parent.parent, proj), _MECH)
    assert "EXECUTION FAILED" not in msgs[-1].content
