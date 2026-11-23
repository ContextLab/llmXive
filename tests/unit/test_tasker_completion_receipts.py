"""Planning may preserve verified work, but cannot self-certify implementation."""
import json
from pathlib import Path
from types import SimpleNamespace

from llmxive.agents import task_verifier as tv
from llmxive.convergence.revisers.tasks_reviser import TasksReviser
from llmxive.speckit.tasks_cmd import TaskerAgent
from tests.integration.test_tasks_reviser import _FakeBackend


def _project(tmp_path, monkeypatch):
    (tmp_path/'agents').symlink_to(Path(__file__).resolve().parents[2]/'agents')
    project = tmp_path/'projects/PROJ-901-completion'
    tasks = project/'specs/001-study/tasks.md'
    tasks.parent.mkdir(parents=True)
    (tasks.parent/'spec.md').write_text('Preserve the specified computation.\n')
    (tasks.parent/'plan.md').write_text('Run the existing producer and review its outputs.\n')
    (project/'code').mkdir()
    (project/'code/run.py').write_text('print(sum(range(100)))\n')
    tasks.write_text('- [X] T001 Implement code/run.py\n')
    monkeypatch.setattr(tv,'verify_task',lambda **kw:tv.TaskVerdict(True,'independent code review'))
    mem = project/'.specify/memory'
    tv.run_verification_pass(project,tasks,already_verified=set(),
        spec_context=(tasks.parent/"spec.md").read_text(),
        notes_path=mem/'notes.md',state_path=mem/'task_verify.yaml')
    assert tv.verified_done_keys(project,tasks) == {'T001'}
    return project,tasks


def test_new_checkmarks_require_current_receipt_and_leave_existing_state_untouched(tmp_path,monkeypatch):
    project,tasks = _project(tmp_path,monkeypatch)
    original = tasks.read_bytes()
    proposed = tasks.read_text()+'- [X] T002 Produce data/missing.csv\n'
    revised = tv.preserve_verified_completion(project,tasks,proposed)
    assert '- [X] T001' in revised and '- [ ] T002' in revised
    assert tasks.read_bytes() == original
    changed = proposed.replace('Implement code/run.py','Implement code/run.py and validate all outputs')
    assert '- [ ] T001' in tv.preserve_verified_completion(project,tasks,changed)
    (project/'code/run.py').write_text('raise RuntimeError("changed")\n')
    assert '- [ ] T001' in tv.preserve_verified_completion(project,tasks,proposed)


def test_tasker_reopens_unverified_work_before_task_analysis(tmp_path,monkeypatch):
    project,tasks = _project(tmp_path,monkeypatch)
    proposed = tasks.read_text()+''.join(
        f'- [X] T{i:03d} Produce and verify data/result_{i}.csv for the specified study\n'
        for i in range(2,6))
    seen = []
    def analyze(self,**kwargs):
        seen.append(tasks.read_text())
    monkeypatch.setattr(TaskerAgent,'_run_engine_path',analyze)
    monkeypatch.setenv('LLMXIVE_TASKER_LEGACY','0')
    TaskerAgent().write_artifacts(SimpleNamespace(project_dir=project),
        {'tasks_path':str(tasks),'spec_path':str(tasks.parent/'spec.md'),
         'plan_path':str(tasks.parent/'plan.md')},SimpleNamespace(text=proposed))
    assert len(seen) == 1
    assert seen[0].count('[X]') == 1 and seen[0].count('[ ]') == 4


def test_task_reviser_cannot_reintroduce_false_completion(tmp_path,monkeypatch):
    project,tasks = _project(tmp_path,monkeypatch)
    key = str(tasks.relative_to(tmp_path))
    response = {'new_tasks_md':tasks.read_text()+'- [X] T002 Produce data/missing.csv\n','responses':[]}
    reviser = TasksReviser(backend=_FakeBackend(response_text=json.dumps(response)),
        repo_root=tmp_path,project_id=project.name)
    updated,_ = reviser.revise({key:tasks.read_text(),
        key.replace('tasks.md','spec.md'):(tasks.parent/'spec.md').read_text(),
        key.replace('tasks.md','plan.md'):(tasks.parent/'plan.md').read_text()},[])
    assert '- [X] T001' in updated[key]
    assert '- [ ] T002' in updated[key]
