"""A malformed paper response cannot send accepted research back to its tasker."""

from types import SimpleNamespace

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.pipeline import graph
from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent
from llmxive.state import project as store
from llmxive.types import Stage
from tests.unit.test_tasker_authoring_contract import OBSERVED_TABLES, project  # noqa: F401


@pytest.mark.parametrize("stage", [Stage.PAPER_PLANNED, Stage.PAPER_TASKED])
def test_paper_table_response_recovers_within_paper_and_preserves_research(
    project, monkeypatch, stage  # noqa: F811 - imported pytest fixture
):
    root, research, state = project
    paper = root / "paper/specs/001-paper"
    paper.mkdir(parents=True)
    for name, text in {
        "spec.md": "Write a finite-range replication paper.\n",
        "plan.md": "Use reviewed data, source, figures and limitations.\n",
        "tasks.md": "- [ ] T001 [kind:prose] Preserve the previous paper task\n",
    }.items():
        (paper / name).write_text(text)
    state = state.model_copy(
        update={
            "current_stage": stage,
            "speckit_paper_dir": str(paper.relative_to(root.parent.parent)),
        }
    )
    store.save(state, repo_root=root.parent.parent)
    before = {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    monkeypatch.setattr(
        "llmxive.speckit.slash_command.chat_with_fallback",
        lambda *a, **kw: ChatResponse(
            text=OBSERVED_TABLES, model="recorded", backend="dartmouth"
        ),
    )
    result = graph.run_one_step(
        state, repo_root=root.parent.parent, run_id="paper-format-recovery"
    )
    assert result.current_stage == Stage.PAPER_PLANNED
    assert (
        store.load(root.name, repo_root=root.parent.parent).current_stage
        == Stage.PAPER_PLANNED
    )
    for rel, data in before.items():
        assert (root / rel).read_bytes() == data
    assert not (root / ".specify/memory/kickback_feedback.md").exists()
    feedback = (root / "paper/.specify/memory/kickback_feedback.md").read_text()
    assert "Paper tasker produced no executable task identities" in feedback
    agent = PaperTaskerAgent()
    ctx = SimpleNamespace(project_dir=root, project_id=root.name)
    prompt = agent.build_prompt(ctx, agent.mechanical_step(ctx))[-1].content
    assert "Paper tasker produced no executable task identities" in prompt
    assert "- [ ] T001 [kind:prose]" in prompt
    assert "not tables" in prompt
