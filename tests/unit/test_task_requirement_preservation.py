"""Claim processing cannot replace executable requirements with factual pointers."""
from types import SimpleNamespace
from dataclasses import replace

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.claims.service import process_document
from llmxive.claims.task_requirements import read_task_document
from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.task_lines import TaskFormatError
from llmxive.state import claims


class NoModel:
    def chat(self, *args, **kwargs):
        raise AssertionError('task instructions must not be extracted or rewritten as claims')


RAW = 'Implement an O(N log log N) sieve returning phi_array (uint64) and recording runtime.'


def project_with_pointer(tmp_path, *, artifact='specs/001-study/tasks.md'):
    project = tmp_path/'projects/PROJ-901-requirements'
    tasks = project/'specs/001-study/tasks.md'
    tasks.parent.mkdir(parents=True)
    (tasks.parent/'spec.md').write_text('# Specification\nStudy all specified primes.')
    tasks.write_text('- [ ] T004 {{claim:c_0e451899}} (`src/utils/sieve.py`)\n')
    claims.save(project.name, [Claim(claim_id='c_0e451899', kind=ClaimKind.ENTITY_FACT,
        raw_text=RAW, canonical='sieve complexity', context='task',
        artifact_path=str((project/artifact).relative_to(tmp_path)), source_type='external',
        status=ClaimStatus.VERIFIED, resolved_value='sieve runs in O(N log log N)',
        evidence={}, resolver='test', attempts=1, updated_at='2026-10-09T00:00:00Z')],
        repo_root=tmp_path)
    return project, tasks


@pytest.mark.parametrize('stage', [None, 'tasks', 'paper_tasks'])
def test_requirements_stay_verbatim_across_stages(tmp_path, stage, monkeypatch):
    text = '- [X] T004 '+RAW+'\n- [ ] T005 Analyze p=5,7,11 for N=1,000,000.\n'
    calls=[]
    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError('claim extraction must not consume task requirements')
    monkeypatch.setattr('llmxive.claims.service.extract_claims', forbidden)
    rendered, extracted, gate = process_document(text, artifact_path='projects/P/specs/001/tasks.md',
        project_id='P',backend=NoModel(),model=None,repo_root=tmp_path,stage_label=stage)
    assert rendered == text and extracted == [] and not gate.blocked
    assert calls == []


def test_legacy_pointer_restores_exact_requirement_before_implementation(tmp_path):
    project, tasks = project_with_pointer(tmp_path)
    context = SimpleNamespace(project_dir=project,project_id=project.name)
    result = ImplementerAgent().mechanical_step(context)
    assert RAW in result['next_task_line']
    assert '{{claim:' not in tasks.read_text()
    assert tasks.read_text().startswith('- [ ] T004 ')
    rendered, _, gate = process_document('- [X] T004 {{claim:c_0e451899}}\n',
        artifact_path=str(tasks.relative_to(tmp_path)),project_id=project.name,
        backend=NoModel(),model=None,repo_root=tmp_path)
    assert rendered == '- [X] T004 '+RAW+'\n' and not gate.blocked


def test_unknown_or_wrong_document_pointer_cannot_count_as_a_requirement(tmp_path):
    project,tasks = project_with_pointer(tmp_path,artifact='paper/results.md')
    before = tasks.read_bytes()
    with pytest.raises(TaskFormatError,match='requirements lost'):
        read_task_document(tasks,project,persist=True)
    assert tasks.read_bytes() == before
    _,_,gate = process_document(tasks.read_text(),artifact_path=str(tasks.relative_to(tmp_path)),
        project_id=project.name,backend=NoModel(),model=None,repo_root=tmp_path)
    assert gate.blocked and gate.unresolved_markers == ['c_0e451899']


def test_research_results_still_enter_full_claim_extraction(tmp_path, monkeypatch):
    seen=[]
    def extract(text,**kwargs):
        seen.append(text)
        return []
    monkeypatch.setattr('llmxive.claims.service.extract_claims',extract)
    text='The measured runtime was 0.285 seconds.'
    process_document(text,artifact_path='projects/P/data/results/RESULTS.md',project_id='P',
        backend=NoModel(),model=None,repo_root=tmp_path)
    assert seen == [text]


@pytest.mark.parametrize('cycle', [False, True])
def test_nested_legacy_requirement_recovery_is_bounded(tmp_path, cycle):
    project, tasks = project_with_pointer(tmp_path)
    saved = claims.load(project.name, repo_root=tmp_path)
    outer = replace(saved[0], claim_id='c_05471f12',
                    raw_text='{{claim:c_0e451899}} (legacy citation)')
    if cycle:
        saved[0] = replace(saved[0], raw_text='{{claim:c_05471f12}}')
    claims.save(project.name, [*saved, outer], repo_root=tmp_path)
    tasks.write_text('- [X] T004 {{claim:c_05471f12}}\n')
    if cycle:
        with pytest.raises(TaskFormatError, match='requirements lost'):
            read_task_document(tasks, project, persist=True)
        assert tasks.read_text() == '- [X] T004 {{claim:c_05471f12}}\n'
    else:
        assert read_task_document(tasks, project, persist=True) == (
            '- [X] T004 '+RAW+' (legacy citation)\n')
