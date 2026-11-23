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


@pytest.mark.parametrize('existing,proposed', [
    ('docs/API.md', 'docs/api.md'),
    ('docs/API.md', 'Docs/new.md'),
    ('docs/caf\u00e9.md', 'docs/cafe\u0301.md'),
])
def test_case_collision_preserves_existing_bytes_and_reaches_retry_prompt(tmp_path, existing, proposed):
    ctx, feature, tasks = _context(tmp_path)
    original = ctx.project_dir / existing
    original.parent.mkdir(parents=True)
    original.write_bytes(b'original scientific evidence\n')
    agent = ImplementerAgent()
    _write(agent, ctx, feature, tasks, [{'path': proposed, 'contents': 'replacement'}])
    assert original.read_bytes() == b'original scientific evidence\n'
    assert '- [ ] T002' in tasks.read_text()
    diagnosis = (ctx.project_dir/'code/.tasks/T002.artifact-write.log').read_text()
    assert 'case-insensitive path collision' in diagnosis
    assert 'Use the existing spelling or a distinct filename' in diagnosis
    assert diagnosis in agent.build_prompt(ctx, agent.mechanical_step(ctx))[-1].content
    assert [p for p in original.parent.iterdir() if p.is_file()] == [original]


def test_existing_exact_filename_remains_editable(tmp_path):
    ctx, feature, tasks = _context(tmp_path)
    target = ctx.project_dir/'docs/API.md'
    target.parent.mkdir()
    target.write_text('old')
    _write(ImplementerAgent(), ctx, feature, tasks, [{'path':'docs/API.md', 'contents':'updated'}])
    assert target.read_text() == 'updated'
    assert not (ctx.project_dir/'code/.tasks/T002.artifact-write.log').exists()


def test_same_proposal_cannot_create_two_case_aliases(tmp_path):
    ctx, feature, tasks = _context(tmp_path)
    _write(ImplementerAgent(), ctx, feature, tasks, [
        {'path':'docs/API.md', 'contents':'first variant'},
        {'path':'docs/api.md', 'contents':'conflicting variant'},
    ])
    assert (ctx.project_dir/'docs/API.md').read_text() == 'first variant'
    assert len(list((ctx.project_dir/'docs').iterdir())) == 1
    assert '- [ ] T002' in tasks.read_text()
    assert 'case-insensitive path collision' in (ctx.project_dir/'code/.tasks/T002.artifact-write.log').read_text()


def test_empty_completed_reports_escalate_then_replan_without_acceptance(tmp_path):
    """The live canary repeated empty completion reports with no recovery signal."""
    from datetime import UTC, datetime

    from llmxive.pipeline import graph
    from llmxive.state import execution_status, unverifiable
    from llmxive.types import Project, Stage

    ctx, feature, tasks = _context(tmp_path)
    now = datetime.now(UTC)
    project = Project(id=ctx.project_id, title='X', field='math',
                      current_stage=Stage.IN_PROGRESS, created_at=now, updated_at=now,
                      speckit_research_dir='specs/001-study')
    for tier in range(3):
        for attempt in range(3):
            # New agent instance reproduces separate scheduled invocations.
            _write(ImplementerAgent(), ctx, feature, tasks, [])
            assert '- [ ] T002' in tasks.read_text()
            assert unverifiable.has_unverifiable(ctx.project_id, repo_root=tmp_path) == (attempt == 2)
        stage = graph._decide_next_stage(project, ctx.project_dir, repo_root=tmp_path)
        assert stage == (Stage.IN_PROGRESS if tier < 2 else Stage.CLARIFIED)
        assert execution_status.model_tier(ctx.project_id, repo_root=tmp_path) == (tier + 1 if tier < 2 else 0)
        assert not unverifiable.has_unverifiable(ctx.project_id, repo_root=tmp_path)
    assert execution_status.replan_rounds(ctx.project_id, repo_root=tmp_path) == 1
    assert not execution_status.is_ok(ctx.project_id, repo_root=tmp_path)
    assert '- [X]' not in tasks.read_text()
    assert 'Artifact proposal refused' in (ctx.project_dir/'.specify/memory'/graph.KICKBACK_FEEDBACK_FILENAME).read_text()


def test_writable_retry_and_changed_task_reset_consecutive_refusals(tmp_path):
    from llmxive.state import unverifiable

    ctx, feature, tasks = _context(tmp_path)
    for _ in range(2):
        _write(ImplementerAgent(), ctx, feature, tasks, [])
    _write(ImplementerAgent(), ctx, feature, tasks, [{'path':'code/census.py', 'contents':'VALUE=1\n'}])
    tasks.write_text(tasks.read_text().replace('[X]', '[ ]'))
    _write(ImplementerAgent(), ctx, feature, tasks, [])
    assert not unverifiable.has_unverifiable(ctx.project_id, repo_root=tmp_path)
    tasks.write_text(tasks.read_text().replace('Implement code/census.py', 'Implement a revised code/census.py'))
    for _ in range(2):
        _write(ImplementerAgent(), ctx, feature, tasks, [])
    assert not unverifiable.has_unverifiable(ctx.project_id, repo_root=tmp_path)
    _write(ImplementerAgent(), ctx, feature, tasks, [])
    assert unverifiable.has_unverifiable(ctx.project_id, repo_root=tmp_path)


def test_refused_proposal_counter_redacts_secrets_and_preserves_other_track(tmp_path, monkeypatch):
    from llmxive.state import unverifiable

    ctx, feature, tasks = _context(tmp_path)
    secret = 'test-only-artifact-secret'
    monkeypatch.setenv('DARTMOUTH_CHAT_API_KEY', secret)
    unverifiable.record_unverifiable(ctx.project_id, 'paper:T002', 'paper failure', repo_root=tmp_path)
    for _ in range(3):
        _write(ImplementerAgent(), ctx, feature, tasks, [{'path':f'../{secret}.py', 'contents':'X=1'}])
    record = next((ctx.project_dir/'.specify/memory/artifact_refusals').glob('*.json')).read_text()
    assert secret not in record and '<redacted>' in record
    assert unverifiable.recorded_keys(ctx.project_id, repo_root=tmp_path) == {'T002', 'paper:T002'}


def test_paper_delegate_neither_consumes_nor_clears_research_refusal_budget(tmp_path):
    from llmxive.state import unverifiable

    ctx, feature, tasks = _context(tmp_path)
    for _ in range(2):
        _write(ImplementerAgent(), ctx, feature, tasks, [])
    saved = next((ctx.project_dir/'.specify/memory/artifact_refusals').glob('*.json'))
    before = saved.read_bytes()
    paper_feature = ctx.project_dir/'paper/specs/001-paper'
    paper_feature.mkdir(parents=True)
    paper_tasks = paper_feature/'tasks.md'
    paper_tasks.write_text('- [ ] T002 Write paper/source/main.tex\n')
    for artifacts in [[], [], [], [{'path':'paper/source/main.tex', 'contents':'A draft.'}]]:
        ImplementerAgent().write_artifacts(ctx,
            {'tasks_path':str(paper_tasks), 'feature_dir':str(paper_feature),
             'next_task_id':'T002', 'all_complete':False, 'task_log_dir':'paper/.tasks'},
            ChatResponse(text=yaml.safe_dump({'task_id':'T002', 'verdict':'completed',
                                             'artifacts':artifacts}), model='test', backend='dartmouth'))
        assert saved.read_bytes() == before
        assert not unverifiable.has_unverifiable(ctx.project_id, repo_root=tmp_path)
    _write(ImplementerAgent(), ctx, feature, tasks, [])
    assert unverifiable.recorded_keys(ctx.project_id, repo_root=tmp_path) == {'T002'}


@pytest.mark.parametrize('link_kind', ['parent', 'file', 'internal_file'])
@pytest.mark.parametrize('artifacts', [[], [{'path':'code/census.py', 'contents':'VALUE=1\n'}]])
def test_refusal_store_never_reads_writes_or_deletes_symlink_target(tmp_path, link_kind, artifacts):
    from llmxive.speckit.implement_cmd import _artifact_refusal_path

    ctx, feature, tasks = _context(tmp_path)
    path = _artifact_refusal_path(ctx, 'T002')
    outside = (ctx.project_dir/'unrelated' if link_kind == 'internal_file' else tmp_path/'outside')
    outside.mkdir()
    target = outside/path.name
    target.write_bytes(b'private preserved bytes')
    if link_kind == 'parent':
        path.parent.parent.mkdir(parents=True)
        path.parent.symlink_to(outside, target_is_directory=True)
    else:
        path.parent.mkdir(parents=True)
        path.symlink_to(target)
    with pytest.raises(ValueError, match='artifact refusal store'):
        _write(ImplementerAgent(), ctx, feature, tasks, artifacts)
    assert target.read_bytes() == b'private preserved bytes'
    assert '- [ ] T002' in tasks.read_text()


def test_missing_optional_model_metadata_does_not_break_refusal_recording(tmp_path):
    from llmxive.state import unverifiable

    ctx, feature, tasks = _context(tmp_path)
    for _ in range(3):
        ImplementerAgent().write_artifacts(ctx,
            {'tasks_path':str(tasks), 'feature_dir':str(feature),
             'next_task_id':'T002', 'all_complete':False},
            SimpleNamespace(text='task_id: T002\nverdict: completed\nartifacts: []\n'))
    assert unverifiable.recorded_keys(ctx.project_id, repo_root=tmp_path) == {'T002'}
    assert '- [ ] T002' in tasks.read_text()
