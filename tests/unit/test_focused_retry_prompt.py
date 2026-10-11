"""The experimental short prompt for a task that was already attempted.

The full retry prompt in the 2026-10-11 runs was 90,000 to 127,000 characters
and placed the one rejection that mattered in a list of other tasks'
rejections. ``LLMXIVE_IMPLEMENTER_PROMPT=focused`` selects a prompt that ends
with the review of this task's previous attempt. It is off by default and is
measured with ``scripts/maintenance/task_replay_bench.py``.
"""
from pathlib import Path

import yaml

from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName

REPO = Path(__file__).resolve().parents[2]


def _ctx(tmp_path: Path) -> SlashCommandContext:
    project = tmp_path / "projects/PROJ-916-focused"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True)
    (tmp_path / "agents/prompts").mkdir(parents=True)
    (tmp_path / "agents/prompts/implementer_research.md").write_text(
        (REPO / "agents/prompts/implementer_research.md").read_text(encoding="utf-8"), encoding="utf-8")
    (feature / "tasks.md").write_text(
        "- [X] T001 Write `code/lib.py`\n- [ ] T002 Report the total in `data/total.txt` using `code/report.py`\n"
        "- [ ] T003 UNRELATED-TASK-MARKER write the paper\n", encoding="utf-8")
    (feature / "spec.md").write_text("# Spec\n\nFR-001 the total is written.\n", encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\n\nPLAN-ONLY-MARKER\n", encoding="utf-8")
    (feature / "quickstart.md").write_text("# Quickstart\n\n`python code/report.py`\n", encoding="utf-8")
    (project / "code").mkdir()
    (project / "code/report.py").write_text("print('REPORT-SOURCE-MARKER')\n", encoding="utf-8")
    return SlashCommandContext(
        project_id=project.name, project_dir=project, run_id="t", task_id="t", inputs=[], expected_outputs=[],
        prompt_template_path=tmp_path / "agents/prompts/implementer_research.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model="m",
        prompt_version="t", agent_name="implementer")


def _reject(ctx: SlashCommandContext) -> None:
    memory = ctx.project_dir / ".specify/memory"
    memory.mkdir(parents=True)
    (memory / "task_verify.feedback.yaml").write_text(yaml.safe_dump({
        "T002": {"task": "x", "reason": "data/total.txt holds 5 but the inputs sum to 6"},
        "T003": {"task": "y", "reason": "OTHER-TASK-REASON-MARKER"}}), encoding="utf-8")
    logs = ctx.project_dir / "code/.tasks"
    logs.mkdir(parents=True)
    (logs / "T002.code_report.py.log").write_text("# code/report.py (exit 0, 0.1s, ok=True)\nRUN-RECORD-MARKER\n", encoding="utf-8")


def _user(ctx: SlashCommandContext) -> str:
    agent = ImplementerAgent()
    return agent.build_prompt(ctx, agent.mechanical_step(ctx))[1].content


def test_a_retry_ends_with_the_review_of_its_own_previous_attempt(tmp_path: Path, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    _reject(ctx)
    monkeypatch.setenv("LLMXIVE_IMPLEMENTER_PROMPT", "focused")
    user = _user(ctx)
    review = user.index("# Review of the previous attempt at this task")
    assert "**Reviewer:** data/total.txt holds 5 but the inputs sum to 6" in user[review:]
    assert "RUN-RECORD-MARKER" in user[review:]
    assert user.index("REPORT-SOURCE-MARKER") < review  # the file under review comes before it
    assert "FR-001" in user and "python code/report.py" in user
    # Not carried: the plan, the other tasks, another task's rejection.
    for absent in ("PLAN-ONLY-MARKER", "UNRELATED-TASK-MARKER", "OTHER-TASK-REASON-MARKER"):
        assert absent not in user


def test_a_first_attempt_and_the_default_keep_the_full_prompt(tmp_path: Path, monkeypatch) -> None:
    ctx = _ctx(tmp_path)
    monkeypatch.setenv("LLMXIVE_IMPLEMENTER_PROMPT", "focused")
    assert "PLAN-ONLY-MARKER" in _user(ctx)  # never attempted: nothing to review
    _reject(ctx)
    monkeypatch.delenv("LLMXIVE_IMPLEMENTER_PROMPT")
    assert "PLAN-ONLY-MARKER" in _user(ctx)  # attempted, but the variant is not selected
