"""Reject the live table-only response without losing tasks or crashing dispatch."""
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.pipeline import graph
from llmxive.speckit.task_lines import TaskFormatError
from llmxive.speckit.tasks_cmd import TaskerAgent
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

SOURCE = Path(__file__).resolve().parents[2]
OBSERVED_TABLES = json.loads(
    (SOURCE / 'tests/fixtures/tasker-table-response.json').read_text()
)['raw_response']


@pytest.fixture
def project(tmp_path):
    (tmp_path / 'agents').symlink_to(SOURCE / 'agents')
    root = tmp_path / 'projects/PROJ-901-task-format'
    feature = root / 'specs/001-study'
    feature.mkdir(parents=True)
    (feature / 'spec.md').write_text('FR-001: Compute all specified integer inputs.\n')
    (feature / 'plan.md').write_text('Compute and independently verify the residue distribution.\n')
    (feature / 'tasks.md').write_text('- [ ] T001 Existing scientific requirement in src/run.py\n')
    now = datetime.now(UTC)
    state = Project(id=root.name, title='Task format recovery', field='mathematics',
        current_stage=Stage.PLANNED, created_at=now, updated_at=now,
        speckit_research_dir=str(feature.relative_to(tmp_path)))
    project_store.save(state, repo_root=tmp_path)
    return root, feature, state


def test_authoring_prompt_identifies_active_mode_and_checkbox_minimum(project):
    root, feature, _ = project
    ctx = SimpleNamespace(project_dir=root, project_id=root.name)
    agent = TaskerAgent()
    messages = agent.build_prompt(ctx, agent.mechanical_step(ctx))
    assert 'Active mode for this call: A' in messages[0].content
    assert '{{mode}}' not in messages[0].content
    assert 'at least five substantive tasks' in messages[0].content
    assert 'at least five substantive canonical checkbox' in messages[1].content
    assert 'FR-001' in messages[1].content
    assert (feature / 'tasks.md').read_text() in messages[1].content


@pytest.mark.parametrize('response', [
    OBSERVED_TABLES,
    '\n'.join(f'- [ ] T{i:03d} Compute src/analysis_{i}.py' for i in range(1, 5)),
], ids=['recorded-table-response', 'four-checkbox-stub'])
def test_invalid_task_counts_raise_recoverable_format_error_and_preserve_prior_files(project, response):
    root, feature, _ = project
    before = {p.name: p.read_bytes() for p in feature.iterdir()}
    with pytest.raises(TaskFormatError, match='need >= 5') as exc:
        TaskerAgent().write_artifacts(SimpleNamespace(project_dir=root),
            {'tasks_path': str(feature / 'tasks.md')}, SimpleNamespace(text=response))
    assert 'Preserve every scientific requirement' in str(exc.value)
    assert before == {p.name: p.read_bytes() for p in feature.iterdir()}


def test_observed_table_response_survives_real_graph_dispatch_as_recoverable_task_feedback(project, monkeypatch):
    root, feature, state = project
    before = {p.name: p.read_bytes() for p in feature.iterdir()}
    calls = []

    def respond(messages, **kwargs):
        calls.append(messages)
        return ChatResponse(text=OBSERVED_TABLES, model='recorded-live-response', backend='dartmouth')

    monkeypatch.setattr('llmxive.speckit.slash_command.chat_with_fallback', respond)
    result = graph.run_one_step(state, repo_root=root.parent.parent, run_id='format-recovery')
    assert len(calls) == 1
    assert result.current_stage == Stage.PLANNED
    assert project_store.load(root.name, repo_root=root.parent.parent).current_stage == Stage.PLANNED
    assert before == {p.name: p.read_bytes() for p in feature.iterdir()}
    feedback = (root / '.specify/memory/kickback_feedback.md').read_text()
    assert 'only 0 task IDs' in feedback
    assert 'not task tables or fenced examples' in feedback
    retry = TaskerAgent()
    ctx = SimpleNamespace(project_dir=root, project_id=root.name)
    prompt = retry.build_prompt(ctx, retry.mechanical_step(ctx))
    assert 'only 0 task IDs' in prompt[1].content
