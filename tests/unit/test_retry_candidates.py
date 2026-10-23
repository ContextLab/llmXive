"""A task that was already attempted gets several independent replies; the best
by executed checks is the one applied.

Measured 2026-10-11 on the stuck tasks of three finished runs, one reply per
attempt: 3 of 13, 1 of 11 and 0 of 4 accepted, and the same prompt on the same
task gave 1 of 4, 2 of 3 and 0 of 6 in three rounds. These tests run the real
implementer, sandbox and pytest; only the model's replies are supplied.
"""
from pathlib import Path

import pytest
import yaml

from llmxive.backends import router
from llmxive.backends.base import ChatResponse
from llmxive.speckit import scorecard
from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName

REPO = Path(__file__).resolve().parents[2]
LIB = "def total(values):\n    return sum(values)\n"
TESTS = ("import sys\nsys.path.insert(0, 'code')\nfrom lib import total\n\n"
         "def test_total():\n    assert total([1, 2, 3]) == 6\n")


def _reply(*artifacts: dict) -> ChatResponse:
    document = {"task_id": "T003", "verdict": "completed", "artifacts": list(artifacts)}
    return ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth")


BREAKS_A_TEST = _reply({"path": "code/lib.py", "contents": "def total(values):\n    return 0\n"},
                       {"path": "data/note.txt", "contents": "from the reply that breaks a test\n"})
OWN_RUN_FAILS = _reply({"path": "code/note.py", "execute": True, "contents": "raise SystemExit(3)\n"})
GOOD = _reply({"path": "code/note.py", "execute": True, "contents": (
    "from llmxive_toolkit import paths\npaths.data('note.txt').write_text('from the good reply\\n', encoding='utf-8')\n")})


@pytest.fixture
def setup(tmp_path: Path):
    project = tmp_path / "projects/PROJ-917-candidates"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True)
    (tmp_path / "agents/prompts").mkdir(parents=True)
    (tmp_path / "agents/prompts/implementer_research.md").write_text(
        (REPO / "agents/prompts/implementer_research.md").read_text(encoding="utf-8"), encoding="utf-8")
    (feature / "tasks.md").write_text(
        "- [X] T001 Write `code/lib.py`\n- [X] T002 Test it in `tests/test_lib.py`\n"
        "- [ ] T003 Write `data/note.txt` with `code/note.py`\n", encoding="utf-8")
    (project / "code").mkdir()
    (project / "code/lib.py").write_text(LIB, encoding="utf-8")
    (project / "tests").mkdir()
    (project / "tests/test_lib.py").write_text(TESTS, encoding="utf-8")
    ctx = SlashCommandContext(
        project_id=project.name, project_dir=project, run_id="t", task_id="t", inputs=[], expected_outputs=[],
        prompt_template_path=tmp_path / "agents/prompts/implementer_research.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model="m",
        prompt_version="t", agent_name="implementer")
    return ctx, project


def _run(ctx: SlashCommandContext, first: ChatResponse) -> None:
    agent = ImplementerAgent()
    mech = agent.mechanical_step(ctx)
    agent.build_prompt(ctx, mech)
    agent.write_artifacts(ctx, mech, first)


def _attempted_before(project: Path) -> None:
    logs = project / "code/.tasks"
    logs.mkdir(parents=True)
    (logs / "T003.code_note.py.log").write_text("# code/note.py (exit 3, 0.1s, ok=False)\n", encoding="utf-8")


def _line(project: Path) -> str:
    return (project / "specs/001-study/tasks.md").read_text(encoding="utf-8").splitlines()[2]


def test_the_best_of_several_replies_is_applied(setup, monkeypatch) -> None:
    ctx, project = setup
    _attempted_before(project)
    more = iter([OWN_RUN_FAILS, GOOD])
    monkeypatch.setattr(router, "chat_with_fallback", lambda *a, **k: next(more))
    _run(ctx, BREAKS_A_TEST)
    # The third reply broke nothing and its own run passed: it is the state that stands.
    assert (project / "data/note.txt").read_text(encoding="utf-8") == "from the good reply\n"
    assert (project / "code/lib.py").read_text(encoding="utf-8") == LIB
    assert _line(project).startswith("- [X] T003")
    assert not (project / "code/.tasks/T003.attempt-not-kept.log").exists()
    values = scorecard.current(project / ".specify/memory", "T003")
    assert values["candidates"] == 3 and values["candidates_claimed"] == 1 and values["kept"] == 1
    # Only the applied reply's run is in the history, once.
    runs = [row for row in scorecard.history(project / ".specify/memory", "T003") if row["source"] == "run"]
    assert [row["values"] for row in runs] == [{"run:code/note.py": 1}]


def test_a_first_attempt_asks_for_one_reply(setup, monkeypatch) -> None:
    ctx, project = setup
    monkeypatch.setattr(router, "chat_with_fallback", lambda *a, **k: pytest.fail("no further reply on a first attempt"))
    _run(ctx, GOOD)
    assert (project / "data/note.txt").read_text(encoding="utf-8") == "from the good reply\n"
    assert "candidates" not in scorecard.current(project / ".specify/memory", "T003")


def test_one_candidate_turns_it_off_and_a_failed_extra_reply_is_left_out(setup, monkeypatch) -> None:
    ctx, project = setup
    _attempted_before(project)
    monkeypatch.setenv("LLMXIVE_RETRY_CANDIDATES", "1")
    monkeypatch.setattr(router, "chat_with_fallback", lambda *a, **k: pytest.fail("turned off"))
    _run(ctx, OWN_RUN_FAILS)
    assert "FAILED-IN-EXECUTION: code/note.py exit=3" in _line(project)
    # The verifier reopens a failed run; do the same here for the next attempt.
    tasks = project / "specs/001-study/tasks.md"
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [~] T003", "- [ ] T003"), encoding="utf-8")
    monkeypatch.setenv("LLMXIVE_RETRY_CANDIDATES", "3")
    replies = iter([RuntimeError("backend down"), GOOD])

    def flaky(*a, **k):
        reply = next(replies)
        if isinstance(reply, Exception):
            raise reply
        return reply
    monkeypatch.setattr(router, "chat_with_fallback", flaky)
    _run(ctx, OWN_RUN_FAILS)
    assert (project / "data/note.txt").read_text(encoding="utf-8") == "from the good reply\n"
    assert scorecard.current(project / ".specify/memory", "T003")["candidates"] == 2


def test_when_every_reply_fails_the_first_is_what_stands(setup, monkeypatch) -> None:
    ctx, project = setup
    _attempted_before(project)
    monkeypatch.setattr(router, "chat_with_fallback", lambda *a, **k: BREAKS_A_TEST)
    _run(ctx, BREAKS_A_TEST)
    assert (project / "code/lib.py").read_text(encoding="utf-8") == LIB
    assert "FAILED-IN-EXECUTION: tests/test_lib.py exit=1" in _line(project)
    assert (project / "code/.tasks/T003.attempt-not-kept.log").is_file()


def test_a_retry_runs_the_project_tests_once_before_and_once_per_reply(setup, monkeypatch) -> None:
    """Batch 5 (2026-10-12): a retry ran the whole suite 8 times, 53-70 s each."""
    from llmxive import sandbox

    ctx, project = setup
    _attempted_before(project)
    more = iter([OWN_RUN_FAILS, GOOD])
    monkeypatch.setattr(router, "chat_with_fallback", lambda *a, **k: next(more))
    real, sessions = sandbox.run_pytest_modules, []

    def counted(**kwargs):
        sessions.append(kwargs["test_relpaths"])
        return real(**kwargs)
    monkeypatch.setattr(sandbox, "run_pytest_modules", counted)
    _run(ctx, BREAKS_A_TEST)
    assert len(sessions) == 4
    # The applied reply's script ran once: its output and its record are the ones it left.
    assert (project / "data/note.txt").read_text(encoding="utf-8") == "from the good reply\n"
    assert "ok=True" in (project / "code/.tasks/T003.code_note.py.log").read_text(encoding="utf-8")
