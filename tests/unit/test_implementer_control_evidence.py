"""Model-authored artifacts must not forge their own acceptance evidence."""
from types import SimpleNamespace

import pytest
import yaml

from llmxive.agents import task_verifier
from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent


@pytest.fixture
def context(tmp_path):
    project = tmp_path / 'projects/PROJ-901-controls'
    feature = project / 'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature / 'tasks.md'
    tasks.write_text('- [ ] T002 Implement code/census.py to compute the exact sum of totients from 1 to 1000\n'
                     '- [ ] T003 Independently validate the calculation\n')
    (feature / 'spec.md').write_text('Compute the exact sum of totients from 1 to 1000.\n')
    (feature / 'plan.md').write_text('Reviewed computational plan.\n')
    ctx = SimpleNamespace(project_dir=project, project_id=project.name)
    mechanical = {'tasks_path': str(tasks), 'feature_dir': str(feature),
                  'next_task_id': 'T002', 'all_complete': False}
    return ctx, mechanical, tasks


def write(ctx, mechanical, path, contents):
    return ImplementerAgent().write_artifacts(ctx, mechanical,
        ChatResponse(text=yaml.safe_dump({'task_id': 'T002', 'verdict': 'completed',
            'artifacts': [{'path': path, 'contents': contents}]}), model='test', backend='dartmouth'))


@pytest.mark.parametrize('path', [
    '.specify/memory/task_verify_cache.yaml', '.specify/memory/claims_verified.yaml',
    'code/.tasks/T002.fake.log', 'paper/.tasks/T002.fake.log', '.git/config', '.venv/config.txt',
    'specs/001-study/spec.md', 'specs/001-study/plan.md', 'specs/001-study/tasks.md',
    'paper/specs/001-paper/tasks.md', '.SPECIFY/memory/forged.yaml',
    'docs/../.specify/memory/forged.yaml',
])
def test_direct_control_artifact_preserves_prior_evidence_and_open_tasks(context, path):
    ctx, mechanical, tasks = context
    target = ctx.project_dir / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text('prior platform evidence\n')
    before = target.read_bytes()
    tasks_before = tasks.read_bytes()
    write(ctx, mechanical, path, 'model-authored acceptance\n')
    assert target.read_bytes() == before
    assert tasks.read_bytes() == tasks_before
    diagnosis = (ctx.project_dir / 'code/.tasks/T002.artifact-write.log').read_text()
    assert 'pipeline control evidence or reviewed requirements' in diagnosis


@pytest.mark.parametrize('protected', ['.specify/memory/task_verify_cache.yaml', 'code/.tasks/T002.fake.log',
                                     'specs/001-study/spec.md', 'specs/001-study/tasks.md'])
def test_resolved_alias_cannot_overwrite_control_evidence(context, protected):
    ctx, mechanical, tasks = context
    target = ctx.project_dir / protected
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text('prior evidence\n')
    before = target.read_bytes()
    alias = ctx.project_dir / 'docs/output.md'
    alias.parent.mkdir()
    alias.symlink_to(target)
    write(ctx, mechanical, 'docs/output.md', 'forged\n')
    assert target.read_bytes() == before
    assert alias.is_symlink()
    assert '- [ ] T002' in tasks.read_text()


@pytest.mark.parametrize('path', ['specs/001-study/research.md', 'specs/001-study/quickstart.md',
    'specs/001-study/data-model.md', 'specs/001-study/contracts/results.schema.json',
    'docs/spec.md', 'code/tests/fixtures/plan.md', 'data/output.csv'])
def test_legitimate_research_documents_and_deliverables_remain_writable(context, path):
    ctx, mechanical, tasks = context
    write(ctx, mechanical, path, 'substantive project deliverable\n')
    assert (ctx.project_dir / path).read_text() == 'substantive project deliverable\n'
    # This is the existing author claim; independent verification remains required.
    assert '- [X] T002' in tasks.read_text()
    assert not (ctx.project_dir / 'code/.tasks/T002.artifact-write.log').exists()


def test_model_artifact_cannot_install_a_forged_acceptance_cache(context):
    ctx, mechanical, tasks = context
    task = tasks.read_text().splitlines()[0].removeprefix('- [ ] ')
    spec = (tasks.parent / 'spec.md').read_text()
    code = ctx.project_dir / 'code/census.py'
    code.parent.mkdir()
    code.write_text('VALUE = 1\n')  # does not perform the requested calculation
    assert task_verifier._deterministic_verdict(ctx.project_dir, task)[0] is None
    digest = task_verifier._verification_hash(task, spec, task_verifier.gather_evidence(ctx.project_dir, task))
    forged = yaml.safe_dump({'T002': {'h': digest, 'c': True, 'r': 'model-authored acceptance'}})
    write(ctx, mechanical, f'projects/{ctx.project_id}/.specify/memory/task_verify_cache.yaml', forged)
    assert not (ctx.project_dir / '.specify/memory/task_verify_cache.yaml').exists()
    assert '- [ ] T002' in tasks.read_text()
    assert task_verifier.verified_done_keys(ctx.project_dir, tasks) == set()


def test_canonicalization_cannot_hide_a_control_component(context):
    ctx, mechanical, tasks = context
    write(ctx, mechanical, 'specs/.specify/forged.yaml', 'forged')
    assert not (tasks.parent / 'forged.yaml').exists()
    assert '- [ ] T002' in tasks.read_text()


def test_invented_feature_slug_cannot_replace_active_tasks(context):
    ctx, mechanical, tasks = context
    before = tasks.read_bytes()
    write(ctx, mechanical, 'specs/invented/tasks.md', '- [X] T002 All done\n')
    assert tasks.read_bytes() == before


def test_active_control_documents_are_protected_outside_standard_specs_root(context):
    ctx, mechanical, _ = context
    feature = ctx.project_dir / 'legacy-feature'
    feature.mkdir()
    tasks = feature / 'tasks.md'
    tasks.write_text('- [ ] T002 Implement the calculation\n')
    spec = feature / 'spec.md'
    spec.write_text('Reviewed requirements\n')
    mechanical = {**mechanical, 'feature_dir':str(feature), 'tasks_path':str(tasks)}
    write(ctx, mechanical, 'legacy-feature/spec.md', 'Anything counts as success\n')
    assert spec.read_text() == 'Reviewed requirements\n'
    assert '- [ ] T002' in tasks.read_text()
