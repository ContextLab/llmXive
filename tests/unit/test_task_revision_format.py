"""Generated task syntax errors use bounded reply recovery, not engine failure."""

import json
from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.convergence.revisers.tasks_reviser import TasksReviser, PaperTasksReviser
from llmxive.convergence.revisers._reviser_response import is_malformed_reply_error

ROOT = Path(__file__).resolve().parents[2]
BAD = [
    "- [ ] T001 Produce data/a.csv\n```python\nprint(1)\n",
    "- [ ] T001 Produce data/a.csv\n- [ ] T001 Produce data/b.csv\n",
]
GOOD = "- [ ] T001 Produce data/a.csv\n"


class Backend:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = 0

    def chat(self, messages, **kwargs):
        if "auditing a revision you just produced" in messages[0].content:
            text = "ok: true\nproblems: []\n"
        else:
            self.calls += 1
            text = json.dumps({"new_tasks_md": next(self.replies), "responses": []})
        return ChatResponse(text=text, model="fixture", backend="fixture")


def setup(tmp_path, cls, replies):
    path = ("paper/" if cls is PaperTasksReviser else "") + "specs/001-test/tasks.md"
    backend = Backend(replies)
    reviser = cls(
        backend=backend,
        repo_root=ROOT,
        project_id="PROJ-format-fixture",
        summarize_cache_dir=tmp_path / "cache",
    )
    return reviser, backend, path


@pytest.mark.parametrize("cls", [TasksReviser, PaperTasksReviser])
@pytest.mark.parametrize("bad", BAD)
def test_malformed_task_document_retries_then_returns_valid_revision(tmp_path, cls, bad):
    reviser, backend, path = setup(tmp_path, cls, [bad, GOOD])
    original = {path: GOOD}
    updated, _ = reviser.revise(original, [])
    assert backend.calls == 2
    assert updated[path] == GOOD
    assert original == {path: GOOD}


@pytest.mark.parametrize("cls", [TasksReviser, PaperTasksReviser])
def test_persistent_bad_document_is_classified_for_engine_kickback(tmp_path, cls):
    reviser, backend, path = setup(tmp_path, cls, [BAD[0], BAD[0]])
    original = {path: GOOD}
    with pytest.raises(RuntimeError, match="no usable tasks artifact") as raised:
        reviser.revise(original, [])
    assert is_malformed_reply_error(raised.value)
    assert backend.calls == 2
    assert original == {path: GOOD}
