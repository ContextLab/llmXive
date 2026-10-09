"""The actual research tasks panel receives its promised immutable contracts."""
import json
import shutil
from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.speckit._tasker_engine_bridge import run_tasker_via_engine


@pytest.mark.parametrize("revise", [False, True])
@pytest.mark.parametrize("layout", ["specs/002-current", "specs/group/002-current"])
def test_production_panel_receives_active_contracts_without_writing_them(tmp_path, monkeypatch, revise, layout):
    source = Path(__file__).resolve().parents[2]
    shutil.copytree(source / 'agents', tmp_path / 'agents')
    monkeypatch.setenv('LLMXIVE_CLAIM_LAYER', '0')
    project_id = 'PROJ-999-contract-context'
    feature = tmp_path / 'projects' / project_id / layout
    tasks_key = (feature / 'tasks.md').relative_to(tmp_path).as_posix()
    (feature / 'contracts/nested').mkdir(parents=True)
    tasks = '# Tasks\n' + '\n'.join(
        f'- [ ] T{i:03d} Implement documented computation {i} in code/part{i}.py'
        for i in range(1, 6))
    for name, content in {'tasks.md': tasks, 'spec.md': '# Specification\nCompute all inputs.',
                          'plan.md': '# Plan\nFollow the column contract.',
                          'data-model.md': 'Measurement unit: exactly microseconds.',
                          'contracts/nested/result.yaml': 'required: [elapsed_microseconds]'}.items():
        (feature / name).write_text(content)
    other = feature.parent / '001-obsolete/contracts'
    other.mkdir(parents=True)
    (other / 'old.yaml').write_text('OBSOLETE_CONTRACT_MUST_NOT_APPEAR')
    originals = {p: p.read_bytes() for p in feature.rglob('*') if p.is_file()}
    panel_messages = []
    revision_messages = []

    class Backend:
        def chat(self, messages, **kwargs):
            packet = '\n'.join(m.content for m in messages)
            if 'auditing a revision you just produced' in messages[0].content:
                return ChatResponse(text='ok: true\nproblems: []\n', model='test', backend='test')
            if 'Other panelists cover other aspects' not in messages[0].content:
                revision_messages.append(packet)
                return ChatResponse(text=json.dumps({'new_tasks_md': tasks + '\nDocument elapsed_microseconds.',
                    'responses': [{'concern_id': 'F001', 'response': 'Named contract field.',
                        'what_changed': 'Documented elapsed_microseconds.',
                        'artifacts_changed': [tasks_key]}]}),
                    model='test', backend='test')
            panel_messages.append(packet)
            return ChatResponse(text='---\nverdict: accept\nconcerns: []\n---\n',
                                model='recording-test', backend='test')

    result = run_tasker_via_engine(project_id=project_id, repo_root=tmp_path,
        tasks_path=feature / 'tasks.md', spec_path=feature / 'spec.md',
        plan_path=feature / 'plan.md', analyze_findings=([{'id': 'F001', 'class': 'coverage',
            'text': 'Name elapsed_microseconds from the contract in the output task.'}] if revise else []),
        backend=Backend())
    assert result.convergence.converged
    assert len(panel_messages) >= 4
    assert bool(revision_messages) == revise
    for packet in panel_messages + revision_messages:
        assert 'Measurement unit: exactly microseconds.' in packet
        assert 'required: [elapsed_microseconds]' in packet
        assert 'contracts/nested/result.yaml' in packet
        assert 'OBSOLETE_CONTRACT_MUST_NOT_APPEAR' not in packet
    assert all(p.read_bytes() == contents for p, contents in originals.items() if p.name != "tasks.md")


@pytest.mark.parametrize('escape', ['other_project', 'outside_repo', 'symlink'])
def test_production_bridge_rejects_untrusted_feature_before_model(tmp_path, escape):
    project_id = 'PROJ-999-contract-context'
    repo = tmp_path / 'repo'
    project = repo / 'projects' / project_id
    project.mkdir(parents=True)
    feature = repo / 'projects/PROJ-other/specs/001-foreign'
    if escape == 'outside_repo':
        feature = tmp_path / 'outside/001-foreign'
    feature.mkdir(parents=True)
    (feature / 'data-model.md').write_text('FOREIGN_PRIVATE_BYTES')
    if escape == 'symlink':
        link = project / 'linked-feature'
        link.symlink_to(feature, target_is_directory=True)
        feature = link

    class NeverCalled:
        def chat(self, *args, **kwargs):
            pytest.fail('model called with an untrusted feature')

    with pytest.raises(ValueError, match='Task review context refused'):
        run_tasker_via_engine(project_id=project_id, repo_root=repo,
            tasks_path=feature / 'tasks.md', spec_path=feature / 'spec.md',
            plan_path=feature / 'plan.md', analyze_findings=[], backend=NeverCalled())
