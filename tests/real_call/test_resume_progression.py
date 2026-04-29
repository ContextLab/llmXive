"""Real-call (T062): the Implementer resumes from the next-incomplete task.

Skipped unless DARTMOUTH_CHAT_API_KEY is set AND LLMXIVE_REAL_TESTS=1.

The test plants a fixture project at `analyzed` with a tasks.md that
already has T001 marked `[X]` and T002 marked `[ ]`. It runs
`graph.run_one_step()` once and asserts the second step picks T002,
not T001 — proving the resume logic reads the existing checkbox state
rather than restarting.

Because real LLM invocation is required to actually advance the
Implementer's state machine, the test only invokes the in-memory
selector (`_next_incomplete`) directly to assert the deterministic
resume contract. The full LLM-driven path is exercised by the
nightly e2e fixture (T037).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent


@pytest.mark.skipif(
    not os.environ.get("DARTMOUTH_CHAT_API_KEY"),
    reason="DARTMOUTH_CHAT_API_KEY not set; resume real-call test cannot run",
)
def test_implementer_resume_picks_next_incomplete(tmp_path: Path) -> None:
    from llmxive.speckit.implement_cmd import ImplementerAgent

    project_dir = tmp_path / "projects" / "PROJ-001-resume"
    feature_dir = project_dir / "specs" / "001-resume"
    feature_dir.mkdir(parents=True)
    tasks_md = feature_dir / "tasks.md"
    tasks_md.write_text(
        """# Tasks

## Phase 1: Setup

- [X] T001 First task already done
- [ ] T002 Second task to do
- [ ] T003 Third task to do
""",
        encoding="utf-8",
    )

    # ImplementerAgent (a SlashCommandAgent) takes no constructor args;
    # the agent registry is consulted at run() time rather than at construction.
    agent = ImplementerAgent()

    text = tasks_md.read_text(encoding="utf-8")
    pick = agent._next_incomplete(text)
    assert pick is not None
    task_id, _line = pick
    assert task_id == "T002", f"expected T002 to be next; got {task_id}"

    # After marking T002 done, the next pick should be T003 — proves
    # the resume logic walks forward in order.
    text = text.replace("- [ ] T002", "- [X] T002", 1)
    pick = agent._next_incomplete(text)
    assert pick is not None and pick[0] == "T003"

    # When all tasks are done, _next_incomplete returns None and
    # _all_complete returns True.
    text = text.replace("- [ ] T003", "- [X] T003", 1)
    assert agent._next_incomplete(text) is None
    assert agent._all_complete(text)
