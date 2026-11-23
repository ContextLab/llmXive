"""Exhausted implementation reaches the planner with its real saved diagnosis."""
import shutil
from pathlib import Path

import pytest

from llmxive.pipeline import graph
from llmxive.speckit.plan_cmd import PlannerAgent
from llmxive.speckit.tasks_cmd import TaskerAgent
from llmxive.state import execution_status as es
from llmxive.state import project as project_store
from llmxive.state import unverifiable
from llmxive.types import Stage
from tests.unit.test_execution_exhaustion_flow import (
    _force_fix_rounds_at_cap,
    _project_in_progress,
)


@pytest.mark.parametrize('failure_kind', ['verification', 'execution'])
def test_exhaustion_dispatches_planner_with_saved_feedback(tmp_path, monkeypatch, failure_kind):
    monkeypatch.delenv('LLMXIVE_PAID_OPT_IN', raising=False)
    monkeypatch.delenv('LLMXIVE_EXECUTION_PAID_TIERS', raising=False)
    pid = 'PROJ-032-replan-owner'
    project, project_dir = _project_in_progress(tmp_path, pid)
    feature = project_dir / 'specs/001-research'
    spec = 'Preserve primes 5, 7, 11 and the original sample sizes.\n'
    plan = '# Existing plan\nReuse the validated sieve; repair the failing driver.\n'
    (feature / 'spec.md').write_text(spec)
    (feature / 'plan.md').write_text(plan)
    es.record(pid, ok=False, reason='driver fails', artifacts=[],
              failures=['python code/driver.py -> rc=1: missing output'], repo_root=tmp_path)
    for _ in es.FREE_MODEL_TIERS[1:]:
        es.bump_model_tier(pid, repo_root=tmp_path)
    if failure_kind == 'verification':
        (feature / 'tasks.md').write_text('- [ ] T001 Driver must emit a valid table\n')
        unverifiable.record_unverifiable(pid, 'T001', 'driver has wrong denominator', repo_root=tmp_path)
    else:
        _force_fix_rounds_at_cap(tmp_path, pid)
    tasks_before = (feature / 'tasks.md').read_bytes()

    target = graph._decide_next_stage(project, project_dir, repo_root=tmp_path)
    assert target == Stage.CLARIFIED
    assert graph.is_valid_transition(project.current_stage, target)
    project = project.model_copy(update={'current_stage': target})
    project_store.save(project, repo_root=tmp_path)
    feedback = project_dir / '.specify/memory/kickback_feedback.md'
    saved_diagnosis = feedback.read_text()
    expected = 'driver has wrong denominator' if failure_kind == 'verification' else 'python code/driver.py'
    assert expected in saved_diagnosis
    assert es.replan_rounds(pid, repo_root=tmp_path) == 1
    assert es.model_tier(pid, repo_root=tmp_path) == 0

    source = Path(__file__).resolve().parents[2]
    (tmp_path / 'agents/prompts').mkdir(parents=True)
    for rel in ('agents/registry.yaml', 'agents/prompts/planner.md'):
        shutil.copyfile(source / rel, tmp_path / rel)
    monkeypatch.setattr('llmxive.execution.data_source.requires_external_data', lambda _: False)
    monkeypatch.setattr(PlannerAgent, '_plan_time_discovered_block', staticmethod(lambda _: ''))

    class PromptObserved(Exception):
        pass

    def inspect_planner(self, ctx):
        assert ctx.agent_name == 'planner'
        mechanical = self.mechanical_step(ctx)
        prompt = self.build_prompt(ctx, mechanical)[-1].content
        assert saved_diagnosis in prompt
        assert plan in prompt
        assert spec in prompt
        # Stop at the external model boundary: no fabricated review/plan success.
        raise PromptObserved

    def reject_tasker(*args):
        pytest.fail('Replanning dispatched the tasker before revising the plan')

    monkeypatch.setattr(PlannerAgent, 'run', inspect_planner)
    monkeypatch.setattr(TaskerAgent, 'run', reject_tasker)
    with pytest.raises(PromptObserved):
        graph.run_one_step(project_store.load(pid, repo_root=tmp_path), repo_root=tmp_path)
    assert feedback.read_text() == saved_diagnosis
    assert (feature / 'plan.md').read_text() == plan
    assert (feature / 'spec.md').read_text() == spec
    assert (feature / 'tasks.md').read_bytes() == tasks_before
    assert not es.is_ok(pid, repo_root=tmp_path)
