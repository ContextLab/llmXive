"""Markdown task examples must never enter execution or acceptance state."""
import pytest

from llmxive.agents import task_verifier as verifier
from llmxive.pipeline.graph import _task_marks
from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.paper_implement_cmd import PaperImplementerAgent
from llmxive.speckit.task_lines import (
    TaskFormatError,
    all_complete,
    mark_task,
    mask_fenced_code,
    task_continuation,
    validate_open_tasks,
)


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_examples_are_ignored_by_all_task_consumers(fence):
    example = f"{fence}markdown\n- [ ] T### example\n- [X] T001 example with a real-looking ID\n{fence}  \n"
    text = example + "- [X] T001 Actual accepted task\n- [ ] T002 Actual pending task\n"
    validate_open_tasks(text)
    assert len(mask_fenced_code(text)) == len(text)
    assert _task_marks(text) == ["X", " "]
    assert verifier.claimed_done_keys(text) == {"T001"}
    assert list(verifier.task_keys(text).values()) == ["T001", "T002"]
    assert verifier._mark_counts(text.splitlines()) == {"X": 1, " ": 1, "~": 0}
    for agent in (ImplementerAgent(), PaperImplementerAgent()):
        assert agent._next_incomplete(text)[0] == "T002"
        assert not agent._all_complete(text)
    changed = mark_task(text, "T002", "X")
    assert changed.startswith(example)
    assert all_complete(changed)
    assert _task_marks(changed) == ["X", "X"]


def test_indented_code_remains_task_context_without_creating_tasks():
    text = "- [ ] T001 Document this example\n  ```md\n  - [ ] T999 illustrative only\n  ```\n  explain it\n\n- [ ] T002 Continue\n"
    assert list(verifier.task_keys(text).values()) == ["T001", "T002"]
    continuation = task_continuation(text.splitlines(), 0)
    assert "T999 illustrative only" in continuation
    assert "explain it" in continuation
    assert "T002" not in continuation


def test_unclosed_fence_cannot_hide_unfinished_work():
    text = "- [X] T001 Done\n```\n- [ ] T002 unfinished\n"
    with pytest.raises(TaskFormatError, match="Unterminated"):
        validate_open_tasks(text)
    with pytest.raises(TaskFormatError):
        all_complete(text)
    assert _task_marks(text) == [" "]


def test_only_matching_fence_closes_example():
    text = "````md\n```\n- [ ] T999 example\n~~~\n````\n- [X] T001 Done\n"
    validate_open_tasks(text)
    assert all_complete(text)
    assert list(verifier.task_keys(text).values()) == ["T001"]


def test_verification_updates_only_real_tasks(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks.md"
    example = "```md\n- [X] T001 sample\n- [ ] T### template placeholder\n```\n"
    tasks.write_text(example + "- [X] T001 Real requirement\n")
    judged = []

    def judge(**kwargs):
        judged.append(kwargs["task_text"])
        return verifier.TaskVerdict(False, "Actual requirement not met")

    monkeypatch.setattr(verifier, "verify_task", judge)
    result = verifier.run_verification_pass(tmp_path, tasks, already_verified=set(),
        notes_path=tmp_path / "notes.md", state_path=tmp_path / "verify.yaml")
    assert judged == ["T001 Real requirement"]
    assert result["rejected"] == [("T001", "Actual requirement not met")]
    assert tasks.read_text() == example + "- [ ] T001 Real requirement\n"


@pytest.mark.parametrize('agent_name', ['research', 'paper'])
def test_task_generation_rejects_duplicate_ids_before_replacing_artifacts(tmp_path, agent_name):
    from types import SimpleNamespace

    from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent
    from llmxive.speckit.tasks_cmd import TaskerAgent

    project = tmp_path / 'projects/PROJ-1'
    feature = project / 'specs/001-test'
    feature.mkdir(parents=True)
    tasks = feature / 'tasks.md'
    original = '\n'.join(f'- [X] T{i:03d} Existing requirement {i}' for i in range(1, 6))
    tasks.write_text(original)
    response = SimpleNamespace(text=original + '\n- [ ] T003 Conflicting duplicate')
    agent = TaskerAgent() if agent_name == 'research' else PaperTaskerAgent()
    with pytest.raises(TaskFormatError, match='duplicates'):
        agent.write_artifacts(SimpleNamespace(project_dir=project), {'tasks_path':str(tasks)}, response)
    assert tasks.read_text() == original


def test_engine_writeback_refuses_ambiguous_ids_and_ignores_example_count():
    from llmxive.speckit._legacy_guards import check_legacy_guards
    real = '\n'.join(f'- [ ] T{i:03d} Requirement {i}' for i in range(1, 6))
    def check(text):
        return check_legacy_guards(filename='tasks.md', new_content=text, original_content=real)
    assert not check('```md\n- [ ] T### example\n```\n' + real)
    assert 'duplicates' in check(real + '\n- [ ] T003 Another requirement')[0]
    assert 'only 0 task IDs' in check('```md\n' + real + '\n```')[0]
    assert 'Unterminated' in check(real + '\n```')[0]


@pytest.mark.parametrize("wrapper", ["```", "~~~~", "````"])
def test_outer_model_wrapper_preserves_inner_markdown_examples(wrapper):
    from llmxive.speckit.task_lines import unwrap_task_document
    content = "# Tasks\n```md\n- [ ] T### format example\n```\n- [ ] T001 Real task"
    unwrapped = unwrap_task_document(wrapper + "markdown\n" + content + "\n" + wrapper)
    assert unwrapped == content
    validate_open_tasks(unwrapped)
    assert list(verifier.task_keys(unwrapped).values()) == ["T001"]


def test_paper_tasker_rejects_example_only_response_without_replacing_artifacts(tmp_path):
    from types import SimpleNamespace

    from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent
    project = tmp_path / "projects/PROJ-1"
    project.mkdir(parents=True)
    tasks = project / "tasks.md"
    tasks.write_text("- [ ] T001 Existing task")
    with pytest.raises(TaskFormatError, match="no executable"):
        PaperTaskerAgent().write_artifacts(SimpleNamespace(project_dir=project),
            {"tasks_path": str(tasks)}, SimpleNamespace(text="# Examples\n```md\n- [ ] T### example\n```"))
    assert tasks.read_text() == "- [ ] T001 Existing task"
