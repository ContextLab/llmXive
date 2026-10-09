"""A plausible report cannot verify its own invented measurements."""
import yaml

from llmxive.agents import task_verifier as tv


def fixture(tmp_path):
    project=tmp_path/'projects/PROJ-report'
    (project/'docs').mkdir(parents=True)
    (project/'data').mkdir()
    (project/'docs/research.md').write_text('Our unconditional TV was 0.018.\n')
    (project/'data/summary.json').write_text('{"tv_unconditional":0.1452}')
    feature=project/'specs/001-report';feature.mkdir(parents=True)
    tasks=feature/'tasks.md';tasks.write_text('- [X] T001 Write docs/research.md from measured results\n')
    return project,tasks


def test_report_evidence_includes_data_that_contradicts_the_prose(tmp_path):
    project,_=fixture(tmp_path)
    evidence=tv.gather_evidence(project,'Write docs/research.md from measured results')
    assert '0.018' in evidence and '"tv_unconditional":0.1452' in evidence
    assert 'data/summary.json (sha256 ' in evidence
    assert 'report\'s own assertion is not evidence' in tv._SYSTEM_PROMPT


def test_changed_supporting_data_invalidates_accepted_report(tmp_path,monkeypatch):
    project,tasks=fixture(tmp_path)
    # Cache mechanics are isolated from model quality here. The live probe
    # separately checks whether the model rejects this concrete contradiction.
    monkeypatch.setattr(tv,'verify_task',lambda **kw:tv.TaskVerdict(True,'fixture response'))
    memory=project/'.specify/memory'
    tv.run_verification_pass(project,tasks,already_verified=set(),
        notes_path=memory/'notes.md',state_path=memory/'task_verify.yaml')
    assert tv.verified_done_keys(project,tasks)=={'T001'}
    (project/'data/summary.json').write_text('{"tv_unconditional":0.25}')
    assert tv.verified_done_keys(project,tasks)==set()


def test_plain_library_task_does_not_depend_on_unrelated_results(tmp_path):
    project,_=fixture(tmp_path)
    (project/'code').mkdir();(project/'code/library.py').write_text('def identity(x): return x\n')
    evidence=tv.gather_evidence(project,'Implement code/library.py')
    assert 'tv_unconditional' not in evidence


def test_directory_task_gets_file_contents_and_missing_data_is_explicit(tmp_path):
    project,_=fixture(tmp_path)
    assert '0.1452' in tv.gather_evidence(project,'Produce data/')
    (project/'data/summary.json').unlink()
    assert 'No data artifacts available' in tv.gather_evidence(project,'Write docs/research.md')
