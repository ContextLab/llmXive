"""A real failed command cannot be accepted by an optimistic model review."""
from types import SimpleNamespace
import pytest
import yaml
from llmxive.agents import task_verifier as tv
from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent


def setup(tmp_path):
    project = tmp_path / 'projects/PROJ-execution'
    feature = project / 'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature / 'tasks.md'
    tasks.write_text('- [ ] T001 Execute scripts/study.sh\n')
    return project, tasks, {'tasks_path': str(tasks), 'feature_dir': str(feature), 'next_task_id': 'T001'}


def write(project, mechanical, body, execute=True):
    ImplementerAgent().write_artifacts(SimpleNamespace(project_dir=project), mechanical,
        ChatResponse(text=yaml.safe_dump({'verdict': 'completed', 'artifacts': [{
            'path': 'scripts/study.sh', 'contents': body, 'execute': execute}]}),
            model='test', backend='dartmouth'))


def review(project, tasks):
    memory = project / '.specify/memory'
    return tv.run_verification_pass(project, tasks, already_verified=set(),
        notes_path=memory/'notes.md', state_path=memory/'task_verify.yaml')


def test_actual_failure_rejected_then_successful_retry_gets_independent_review(tmp_path, monkeypatch):
    project, tasks, mechanical = setup(tmp_path)
    write(project, mechanical, 'exit 7\n')
    assert '- [~] T001' in tasks.read_text()
    calls = []
    def optimistic(**kwargs):
        calls.append(kwargs)
        return tv.TaskVerdict(True, 'accepted after inspecting actual artifacts')
    monkeypatch.setattr(tv, 'verify_task', optimistic)
    failed = review(project, tasks)
    assert len(failed['rejected']) == 1 and not calls
    assert '- [ ] T001' in tasks.read_text()
    assert 'exit 7' in (project/'code/.tasks/T001.scripts_study.sh.log').read_text()
    write(project, mechanical, 'printf "computed successfully\\n"\n')
    assert 'FAILED-IN-EXECUTION' not in tasks.read_text()
    assert review(project, tasks)['accepted'] == 1 and len(calls) == 1


def test_edit_without_rerun_cannot_erase_real_failure(tmp_path, monkeypatch):
    project, tasks, mechanical = setup(tmp_path)
    write(project, mechanical, 'exit 8\n')
    write(project, mechanical, 'exit 0\n', execute=False)
    monkeypatch.setattr(tv, 'verify_task', lambda **kw: pytest.fail('failure reached semantic reviewer'))
    assert len(review(project, tasks)['rejected']) == 1


def test_legacy_checked_failure_invalidates_even_matching_acceptance_cache(tmp_path, monkeypatch):
    project, tasks, mechanical = setup(tmp_path)
    (project/'scripts').mkdir()
    (project/'scripts/study.sh').write_text('exit 7\n')
    rest = 'T001 Execute scripts/study.sh <!-- FAILED-IN-EXECUTION: scripts/study.sh exit=7 -->'
    tasks.write_text('- [X] ' + rest + '\n')
    memory = project/'.specify/memory'
    memory.mkdir(parents=True)
    digest = tv._evidence_hash(rest+'\n\n'+tv.gather_evidence(project, rest))
    (memory/'task_verify_cache.yaml').write_text(yaml.safe_dump({'T001': {'c': True, 'h': digest}}))
    assert tv.verified_done_keys(project, tasks) == set()
    monkeypatch.setattr(tv, 'verify_task', lambda **kw: pytest.fail('failure reached semantic reviewer'))
    assert len(review(project, tasks)['rejected']) == 1


def test_only_actual_successful_failed_paths_are_cleared():
    from llmxive.speckit.task_lines import clear_retried_execution_failures
    text = '- [ ] T001 Run scripts/a.sh <!-- keep audit --> <!-- FAILED-IN-EXECUTION: scripts/a.sh exit=1; scripts/b.sh exit=-1 (TIMEOUT) -->\n- [X] T001a Unrelated\n'
    assert clear_retried_execution_failures(text, 'T001', {'scripts/a.sh'}) == text
    result = clear_retried_execution_failures(text, 'T001', {'scripts/a.sh', 'scripts/b.sh'})
    assert result == '- [ ] T001 Run scripts/a.sh <!-- keep audit -->\n- [X] T001a Unrelated\n'
