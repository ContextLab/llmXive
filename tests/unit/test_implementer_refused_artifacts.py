"""A partially refused proposal retains diagnostics and cannot complete its task."""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent


def _context(tmp_path):
    (tmp_path/'agents').symlink_to(Path(__file__).resolve().parents[2]/'agents')
    project = tmp_path/'projects/PROJ-901-refusal'
    feature = project/'specs/001-study'
    feature.mkdir(parents=True)
    (feature/'spec.md').write_text('Produce the implementation and its runnable test.\n')
    tasks = feature/'tasks.md'
    tasks.write_text('- [ ] T002 Implement code/census.py and code/tests/test_census.py\n'
                     '- [ ] T003 Run the full census\n')
    return SimpleNamespace(project_dir=project, project_id=project.name), feature, tasks


def _write(agent, ctx, feature, tasks, artifacts):
    return agent.write_artifacts(ctx,
        {'tasks_path':str(tasks), 'feature_dir':str(feature),
         'next_task_id':'T002', 'all_complete':False},
        ChatResponse(text=yaml.safe_dump({'task_id':'T002','verdict':'completed',
                                         'artifacts':artifacts}), model='test', backend='dartmouth'))


def test_refused_test_keeps_task_open_and_supplies_exact_diagnosis_to_retry(tmp_path):
    ctx, feature, tasks = _context(tmp_path)
    agent = ImplementerAgent()
    invalid = 'def test_census():\n    assert True\n  - path: code/next.py\n'
    written = _write(agent, ctx, feature, tasks, [
        {'path':'code/census.py', 'contents':'VALUE = 42\n'},
        {'path':'code/tests/test_census.py', 'contents':invalid},
        # A refused proposal must not execute a prior or partially updated file.
        {'path':'code/should_not_run.py', 'contents':"from pathlib import Path\nPath('RAN').touch()\n",
         'execute':True},
    ])
    assert (ctx.project_dir/'code/census.py').read_text() == 'VALUE = 42\n'
    assert not (ctx.project_dir/'code/tests/test_census.py').exists()
    assert not (ctx.project_dir/'RAN').exists()
    assert '- [ ] T002' in tasks.read_text()
    assert '- [ ] T003' in tasks.read_text()
    refusal = ctx.project_dir/'code/.tasks/T002.artifact-write.log'
    diagnosis = refusal.read_text()
    assert "refusing to write 'code/tests/test_census.py'" in diagnosis
    assert 'SyntaxError at line 3' in diagnosis
    assert str(refusal.relative_to(tmp_path)) in written
    next_step = agent.mechanical_step(ctx)
    assert next_step['next_task_id'] == 'T002'
    prompt = agent.build_prompt(ctx, next_step)[-1].content
    assert diagnosis in prompt

    _write(agent, ctx, feature, tasks, [
        {'path':'code/tests/test_census.py', 'contents':'def test_census():\n    assert True\n'}])
    assert not refusal.exists()
    assert '- [X] T002' in tasks.read_text()
    assert agent.mechanical_step(ctx)['next_task_id'] == 'T003'


@pytest.mark.parametrize('artifact,reason', [
    ({'path':'code/bad.py','contents':'print(unknown_name)\n'}, 'unresolved names'),
    ({'path':'code/bad.py','contents':'from sibling import nonexistent\n'}, 'imports nonexistent'),
    ({'path':'code/bad.py','contents':'--- a/file.py\n+++ b/file.py\n'}, 'diff-fragment'),
    ({'path':'../escape.py','contents':'VALUE=1\n'}, 'out-of-project'),
    ({'path':'code','contents':'not a file'}, 'directory path'),
    ({'path':'code/empty.py','contents':''}, 'empty contents'),
])
def test_each_artifact_refusal_stays_open_with_persisted_reason(tmp_path, artifact, reason):
    ctx, feature, tasks = _context(tmp_path)
    (ctx.project_dir/'code').mkdir()
    (ctx.project_dir/'code/sibling.py').write_text('VALUE = 42\n')
    _write(ImplementerAgent(), ctx, feature, tasks, [artifact])
    assert '- [ ] T002' in tasks.read_text()
    log = (ctx.project_dir/'code/.tasks/T002.artifact-write.log').read_text()
    assert reason in log


def test_refusal_log_redacts_known_secret_values(tmp_path, monkeypatch):
    ctx, feature, tasks = _context(tmp_path)
    secret = 'test-only-artifact-secret'
    monkeypatch.setenv('DARTMOUTH_CHAT_API_KEY', secret)
    _write(ImplementerAgent(), ctx, feature, tasks, [
        {'path':f'../{secret}.py', 'contents':'VALUE = 1\n'}])
    log = (ctx.project_dir/'code/.tasks/T002.artifact-write.log').read_text()
    assert secret not in log
    assert '<redacted>' in log
    assert '- [ ] T002' in tasks.read_text()


def test_empty_package_marker_is_written_and_imported_as_a_real_package(tmp_path):
    from llmxive import sandbox

    ctx, feature, tasks = _context(tmp_path)
    _write(ImplementerAgent(), ctx, feature, tasks, [
        {'path':'code/study/__init__.py', 'contents':''},
        {'path':'code/study/worker.py', 'contents':'VALUE = 42\n'},
        {'path':'code/check_package.py', 'contents':
         'from pathlib import Path\nimport study\nfrom study.worker import VALUE\n'
         'assert study.__file__ is not None\n'
         'assert Path(study.__file__).name == "__init__.py"\nprint(VALUE)\n'},
    ])
    marker = ctx.project_dir/'code/study/__init__.py'
    assert marker.is_file() and marker.read_bytes() == b''
    assert not (ctx.project_dir/'code/.tasks/T002.artifact-write.log').exists()
    assert '- [X] T002' in tasks.read_text()
    result = sandbox.run_python_script(
        project_dir=ctx.project_dir, script_relpath='code/check_package.py', timeout_s=120)
    assert result.ok, result.stderr
    assert result.stdout.strip() == '42'
