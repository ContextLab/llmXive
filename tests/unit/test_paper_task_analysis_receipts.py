"""Completed task review is reused only for the exact unchanged follow-up stage."""
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.backends.base import BackendUnavailable, ChatResponse
from llmxive.speckit.paper_tasks_cmd import PaperTaskerAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.state import project as project_store
from llmxive.types import BackendName, Outcome, Project, Stage


@pytest.fixture
def reviewed(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[2]
    deployed = tmp_path / 'loaded-platform/src/llmxive'
    reviewer = deployed / 'convergence/reviewspecs.py'
    reviewer.parent.mkdir(parents=True)
    reviewer.write_text('REVIEW_POLICY = "initial"\n')
    monkeypatch.setattr('llmxive.speckit._analysis_policy._deployed_source_root', lambda: deployed)
    project = tmp_path / 'projects/PROJ-901-receipt'
    feature = project / 'paper/specs/001-study'
    feature.mkdir(parents=True)
    (feature / 'spec.md').write_text('# Specification\nFR-001: Measure all specified integer inputs.\n')
    (feature / 'plan.md').write_text('# Plan\nCompute the finite residue distribution and verify it.\n')
    for directory in ('agents/prompts', '.specify/templates'):
        shutil.copytree(source / directory, tmp_path / directory)
    now = datetime.now(UTC)
    state = Project(id='PROJ-901-receipt', title='Finite residue study', field='mathematics',
        current_stage=Stage.PAPER_PLANNED, created_at=now, updated_at=now,
        points_research={}, points_paper={}, artifact_hashes={},
        speckit_paper_dir='projects/PROJ-901-receipt/paper/specs/001-study')
    project_store.save(state, repo_root=tmp_path)
    ctx = SlashCommandContext(project_id='PROJ-901-receipt', project_dir=project,
        run_id='run', task_id='task', inputs=[], expected_outputs=[],
        prompt_template_path=tmp_path / 'agents/prompts/paper_tasker.md',
        default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model='test',
        prompt_version='1.0.0', agent_name='paper_tasker')
    monkeypatch.setenv('LLMXIVE_CLAIM_LAYER', '0')
    calls = []
    tasks = '# Finite residue study\n' + '\n'.join(
        f'- [ ] T{i:03d} [kind:prose] Compute and verify residue distribution {i} in code/study_{i}.py'
        for i in range(1, 6))

    def generate(*args, **kwargs):
        calls.append('generate')
        return ChatResponse(text=tasks, model='test', backend='dartmouth')

    def analyze(**kwargs):
        calls.append('analyze')
        return 'CLEAN'

    monkeypatch.setattr('llmxive.speckit.slash_command.chat_with_fallback', generate)
    monkeypatch.setattr('llmxive.speckit.paper_tasks_cmd.run_analyze', analyze)
    monkeypatch.setattr(PaperTaskerAgent, '_run_paper_tasks_panel', lambda *a, **k: calls.append('panel') or True)
    assert PaperTaskerAgent().run(ctx).outcome == Outcome.SUCCESS
    assert calls == ['generate', 'analyze', 'panel']
    project_store.save(state.model_copy(update={'current_stage':Stage.PAPER_TASKED}), repo_root=tmp_path)
    return ctx, state, feature, calls


def test_followup_skips_generation_and_analysis_without_changing_tasks(reviewed):
    ctx, _, feature, calls = reviewed
    before = (feature / 'tasks.md').read_bytes()
    entry = PaperTaskerAgent().run(ctx)
    assert entry.outcome == Outcome.SKIPPED
    assert entry.model_name == 'deterministic-no-llm'
    assert calls == ['generate', 'analyze', 'panel']
    assert (feature / 'tasks.md').read_bytes() == before


@pytest.mark.parametrize('relative', [
    'paper/specs/001-study/contracts/summary.yaml', 'paper/specs/001-study/tasks.md', 'paper/specs/001-study/spec.md', 'paper/specs/001-study/plan.md',
    'paper/.specify/templates/tasks-template.md', 'paper/.specify/memory/constitution.md',
    '.specify/memory/task_verifier_notes.md', 'paper/.specify/memory/kickback_feedback.md',
    'reviews/research/reviewer.md',
])
def test_changed_inputs_force_fresh_work(reviewed, relative):
    ctx, _, _, _ = reviewed
    path = ctx.project_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((path.read_text() if path.exists() else '') + '\nNew scientific constraint\n')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')
    marker = ctx.project_dir / 'paper/.specify/memory/task_analysis.json'
    assert not marker.exists()


def test_replan_never_reuses_receipt(reviewed):
    ctx, state, _, _ = reviewed
    project_store.save(state, repo_root=ctx.project_dir.parent.parent)
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_failed_analysis_does_not_reuse_a_stale_success(reviewed, monkeypatch):
    ctx, state, _, _ = reviewed
    project_store.save(state, repo_root=ctx.project_dir.parent.parent)
    def unavailable(**kwargs):
        raise BackendUnavailable('temporary outage')
    monkeypatch.setattr('llmxive.speckit.paper_tasks_cmd.run_analyze', unavailable)
    with pytest.raises(BackendUnavailable):
        PaperTaskerAgent().run(ctx)
    project_store.save(state.model_copy(update={'current_stage':Stage.PAPER_TASKED}),
        repo_root=ctx.project_dir.parent.parent)
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_post_analysis_citation_edit_invalidates_receipt(reviewed, monkeypatch):
    ctx, state, feature, _ = reviewed
    project_store.save(state, repo_root=ctx.project_dir.parent.parent)
    def edit_after_review(*args, **kwargs):
        path = feature / 'tasks.md'
        path.write_text(path.read_text() + '\nCitation correction changed the document\n')
    monkeypatch.setattr('llmxive.speckit.slash_command._validate_artifact_citations', edit_after_review)
    PaperTaskerAgent().run(ctx)
    project_store.save(state.model_copy(update={'current_stage':Stage.PAPER_TASKED}),
        repo_root=ctx.project_dir.parent.parent)
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_offline_panel_never_produces_receipt(reviewed, monkeypatch):
    ctx, state, _, _ = reviewed
    project_store.save(state, repo_root=ctx.project_dir.parent.parent)
    monkeypatch.setattr(PaperTaskerAgent, '_run_paper_tasks_panel', lambda *a, **k: False)
    PaperTaskerAgent().run(ctx)
    assert not PaperTaskerAgent()._analysis_marker(ctx).exists()


def test_changed_model_invalidates_receipt(reviewed):
    ctx, _, _, _ = reviewed
    ctx.default_model = 'different-model'
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_changed_review_policy_invalidates_receipt(reviewed):
    ctx, _, _, _ = reviewed
    path = ctx.project_dir.parent.parent / 'src/llmxive/convergence/reviewspecs.py'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# Changed reviewer policy')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_malformed_receipt_forces_review(reviewed):
    ctx, _, _, _ = reviewed
    PaperTaskerAgent()._analysis_marker(ctx).write_text('incomplete JSON')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_changed_authoritative_web_policy_invalidates_receipt(reviewed):
    ctx, _, _, _ = reviewed
    path = ctx.project_dir.parent.parent / 'web/about.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<script>citation_title_overlap_threshold: 0.99</script>')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


def test_changed_root_template_guard_invalidates_receipt(reviewed):
    ctx, _, _, _ = reviewed
    path = ctx.project_dir.parent.parent / '.specify/templates/tasks-template.md'
    path.write_text('New template refusal policy')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')


@pytest.mark.parametrize('field,value', [
    ('default_model', 'different-free-model'),
    ('default_backend', BackendName.LOCAL),
    ('fallback_backends', [BackendName.LOCAL]),
    ('prompt_version', '2.0.0'),
])
def test_changed_dispatch_policy_invalidates_and_reruns_analysis(reviewed, field, value):
    ctx, _, feature, calls = reviewed
    before = (feature / 'tasks.md').read_bytes()
    setattr(ctx, field, value)
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')
    assert (feature / 'tasks.md').read_bytes() == before
    assert PaperTaskerAgent().run(ctx).outcome == Outcome.SUCCESS
    assert calls.count('generate') == 2 and calls.count('analyze') == 2
    assert PaperTaskerAgent().run(ctx).outcome == Outcome.SKIPPED
    assert (feature / 'tasks.md').read_bytes() == before


def test_loaded_policy_change_invalidates_despite_unchanged_data_source_copy(reviewed):
    ctx, _, feature, _ = reviewed
    root = ctx.project_dir.parent.parent
    copy = root / 'src/llmxive/convergence/reviewspecs.py'
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_text('REVIEW_POLICY = "old data copy"\n')
    # Establish a new accepted receipt with both independent roots present.
    assert PaperTaskerAgent().run(ctx).outcome == Outcome.SUCCESS
    assert PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')
    before = (feature / 'tasks.md').read_bytes()
    (root / 'loaded-platform/src/llmxive/convergence/reviewspecs.py').write_text('REVIEW_POLICY = "new deployed policy"\n')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')
    assert copy.read_text() == 'REVIEW_POLICY = "old data copy"\n'
    assert (feature / 'tasks.md').read_bytes() == before


def test_runtime_policy_flags_invalidate_but_credentials_do_not(reviewed, monkeypatch):
    ctx, _, _, _ = reviewed
    monkeypatch.setenv('LLMXIVE_PRIVATE_TOKEN', 'test-only-rotated-credential')
    assert PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')
    monkeypatch.setenv('LLMXIVE_CLAIM_LAYER', '1')
    assert not PaperTaskerAgent().mechanical_step(ctx).get('skip_llm')
