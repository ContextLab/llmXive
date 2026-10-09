"""Exercise persisted production paper writes, independent receipts and final gates."""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive.agents import task_verifier as tv
from llmxive.backends.base import ChatResponse
from llmxive.speckit.paper_implement_cmd import PaperImplementerAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName


@pytest.fixture
def paper(tmp_path, monkeypatch):
    repo = Path(__file__).resolve().parents[2]
    (tmp_path / 'agents').symlink_to(repo / 'agents')
    project = tmp_path / 'projects/PROJ-901-paper'
    feature = project / 'paper/specs/001-paper'
    feature.mkdir(parents=True)
    (feature / 'spec.md').write_text('Create a paper using the accepted research, one task at a time.')
    (feature / 'plan.md').write_text('Create source, then compose results.')
    (feature / 'tasks.md').write_text('- [ ] T001 [kind:latex-build] Create paper/source/main.tex as a compilable article scaffold.\n'
                                     '- [ ] T002 [kind:prose] Write paper/source/results.tex from the accepted report.\n')
    memory = project / 'paper/.specify/memory'
    memory.mkdir(parents=True)
    (memory / 'constitution.md').write_text('PAPER: preserve measured disagreements.')
    (project / '.specify/memory').mkdir(parents=True)
    (project / '.specify/memory/constitution.md').write_text('RESEARCH: different constraints.')
    (project / 'paper/methods_results.md').write_text('Observed p=11 reverses the predicted ordering; do not claim uniformity.')
    (project / 'data').mkdir()
    (project / 'data/measured.csv').write_text('p,value\n11,0.42\n')
    ctx = SlashCommandContext(project.name, project, 'run-test', 'pipeline-task', [], [],
                              tmp_path / 'unused', BackendName.DARTMOUTH, [], 'test-model', '1.0.0', 'paper_implementer')
    agent = PaperImplementerAgent()
    monkeypatch.setattr(tv, 'verify_task', lambda **kw: tv.TaskVerdict(True, 'Selected task artifact matches.'))
    return agent, ctx, feature / 'tasks.md'


def proposal(task='T001', artifacts=None, verdict='completed'):
    return ChatResponse(yaml.safe_dump({'task_id': task, 'verdict': verdict, 'artifacts': artifacts or []}),
                        'test-model', 'dartmouth')


TEX = '\\documentclass{article}\n\\begin{document}\nScaffold.\n\\end{document}\n'


def test_empty_source_bootstraps_real_file_and_verifies_before_next_task(paper, monkeypatch):
    agent, ctx, tasks = paper
    calls = []
    def verify(**kwargs):
        assert (ctx.project_dir / 'paper/source/main.tex').read_text() == TEX
        assert '[~] T001' in tasks.read_text()  # never trust author's checkbox mid-review
        calls.append(kwargs)
        return tv.TaskVerdict(True, 'Actual persisted scaffold is present.')
    monkeypatch.setattr(tv, 'verify_task', verify)
    monkeypatch.setattr(agent, '_finalize', lambda *a: pytest.fail('full panel must wait for all tasks'), raising=False)
    assert not (ctx.project_dir / 'paper/source').exists()
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'paper/source/main.tex', 'contents': TEX}]))
    assert (ctx.project_dir / 'paper/source/main.tex').read_text() == TEX
    assert len(calls) == 1
    assert '[X] T001' in tasks.read_text() and '[ ] T002' in tasks.read_text()
    assert tv.verified_done_keys(ctx.project_dir, tasks, model='test-model') == {'T001'}
    assert not (ctx.project_dir / '.specify/memory/task_verify_cache.yaml').exists()
    assert agent.mechanical_step(ctx)['next_task_id'] == 'T002'
    assert not (ctx.project_dir / 'paper/.specify/memory/human_input_needed.yaml').exists()


def test_context_supplies_actual_report_data_paper_constitution_and_continuation(paper):
    agent, ctx, tasks = paper
    tasks.write_text(tasks.read_text().replace('scaffold.', 'scaffold.\n  Preserve article format and amsthm.'))
    prompt = '\n'.join(m.content for m in agent.build_prompt(ctx, agent.mechanical_step(ctx)))
    assert 'methods_results.md' in prompt and 'p=11 reverses' in prompt and '11,0.42' in prompt
    assert 'PAPER: preserve' in prompt and 'RESEARCH: different' not in prompt
    assert 'Preserve article format and amsthm.' in prompt
    assert '(unused' not in prompt


@pytest.mark.parametrize('response', [proposal(verdict='failed'), proposal(verdict='atomize'), proposal(task='T999'), ChatResponse('not YAML', 'test-model', 'dartmouth')])
def test_failure_protocol_does_not_inherit_skipped_as_complete(paper, response):
    agent, ctx, tasks = paper
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), response)
    assert '[ ] T001' in tasks.read_text()
    assert (ctx.project_dir / 'paper/.tasks/T001.proposal.log').is_file()


def test_semantic_rejection_and_refused_artifact_never_count_complete(paper, monkeypatch):
    agent, ctx, tasks = paper
    monkeypatch.setattr(tv, 'verify_task', lambda **kw: tv.TaskVerdict(False, 'Scaffold omits requested article content.'))
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'paper/source/main.tex', 'contents': TEX}]))
    assert '[ ] T001' in tasks.read_text()
    prompt = agent.build_prompt(ctx, agent.mechanical_step(ctx))[-1].content
    assert 'Scaffold omits requested article content.' in prompt
    tasks.write_text('- [ ] T001 Implement code/inject.py\n- [ ] T002 Write paper/source/results.tex\n')
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'code/inject.py', 'contents': 'def broken(:\n'}]))
    assert '[ ] T001' in tasks.read_text()
    assert 'SyntaxError' in (ctx.project_dir / 'paper/.tasks/T001.artifact-write.log').read_text()
    assert not (ctx.project_dir / 'code/.tasks/T001.artifact-write.log').exists()


@pytest.mark.parametrize('path', ['../escaped.tex', 'paper/.specify/memory/proofreader_flags.yaml', 'paper/specs/001-paper/tasks.md', 'data/measured.csv', 'code/undeclared.py'])
def test_paper_author_cannot_write_control_evidence_or_undeclared_outputs(paper, path):
    agent, ctx, tasks = paper
    before = tasks.read_text()
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': path, 'contents': 'fake'}]))
    assert tasks.read_text() == before
    assert (ctx.project_dir / 'data/measured.csv').read_text() == 'p,value\n11,0.42\n'


def test_deferred_verification_resumes_without_author_rewrite(paper, monkeypatch):
    agent, ctx, tasks = paper
    verdicts = iter([tv.TaskVerdict(None, 'temporary outage'), tv.TaskVerdict(True, 'verified')])
    monkeypatch.setattr(tv, 'verify_task', lambda **kw: next(verdicts))
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'paper/source/main.tex', 'contents': TEX}]))
    assert '[~] T001' in tasks.read_text()
    mechanical = agent.mechanical_step(ctx)
    assert mechanical['deterministic_write'] is True
    agent.write_artifacts(ctx, mechanical, ChatResponse('', 'deterministic-no-llm', 'dartmouth'))
    assert '[X] T001' in tasks.read_text()


def test_paper_rejection_registry_does_not_reuse_research_task_id(paper, monkeypatch):
    from llmxive.state import unverifiable
    agent, ctx, tasks = paper
    unverifiable.record_unverifiable(ctx.project_id, 'T001', 'Old research rejection', repo_root=ctx.project_dir.parent.parent)
    monkeypatch.setattr(tv, 'verify_task', lambda **kw: tv.TaskVerdict(False, 'Paper scaffold rejected'))
    for n in range(tv.REJECT_CAP):
        agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'paper/source/main.tex', 'contents': TEX + f'% retry {n}\n'}]))
    assert unverifiable.recorded_keys(ctx.project_id, repo_root=ctx.project_dir.parent.parent) == {'T001', 'paper:T001'}
    assert '[ ] T001' in tasks.read_text()


def test_declared_support_script_really_executes_and_uses_only_paper_task_logs(paper, monkeypatch):
    import sys

    from llmxive import sandbox
    agent, ctx, tasks = paper
    tasks.write_text('- [ ] T001 Implement and execute code/inject.py to write paper/source/macros.tex.\n'
                     '- [ ] T002 Write paper/source/results.tex\n')
    monkeypatch.setattr(sandbox, 'ensure_venv', lambda *a, **kw: Path(sys.executable))
    script = "from pathlib import Path\np=Path('paper/source/macros.tex')\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text('Measured value: 0.42')\nprint('macros written')\n"
    def verify(**kwargs):
        assert 'macros written' in kwargs['evidence']
        assert 'paper/.tasks/' in kwargs['evidence']
        assert 'OLD RESEARCH' not in kwargs['evidence']
        return tv.TaskVerdict(True, 'Actual subprocess succeeded and produced the expected file.')
    monkeypatch.setattr(tv, 'verify_task', verify)
    (ctx.project_dir / 'code/.tasks').mkdir(parents=True)
    (ctx.project_dir / 'code/.tasks/T001.code_inject.py.log').write_text('# code/inject.py (exit 1, 1s, ok=False)\nOLD RESEARCH')
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'code/inject.py', 'contents': script, 'execute': True}]))
    assert (ctx.project_dir / 'paper/source/macros.tex').read_text() == 'Measured value: 0.42'
    assert '[X] T001' in tasks.read_text()


def test_finalization_runs_panel_then_reverification_then_real_proofreader_dispatch(paper, monkeypatch):
    from llmxive.agents.proofreader import proofreader_clean
    from llmxive.speckit.paper_implement_cmd import paper_implementation_review_current
    agent, ctx, tasks = paper
    tasks.write_text(tasks.read_text().splitlines()[0] + '\n')
    events = []
    def verify(**kwargs):
        events.append('verify')
        return tv.TaskVerdict(True, 'Scaffold matches.')
    monkeypatch.setattr(tv, 'verify_task', verify)
    monkeypatch.setattr('llmxive.backends.router.make_backend', lambda *a: object())
    monkeypatch.setattr('llmxive.convergence.reviewspecs.build_paper_implement_reviewspec', lambda **kw: object())
    def panel(spec, artifacts, **kw):
        assert '[X] T001' in tasks.read_text()
        assert 'p=11 reverses' in artifacts['__results_md__']
        key = next(k for k in artifacts if k.endswith('main.tex'))
        artifacts[key] += '% independently reviewed\n'
        events.append('panel')
        return SimpleNamespace(converged=True, kickback=None, response_history=[SimpleNamespace(artifacts_changed=[key])])
    monkeypatch.setattr('llmxive.convergence.engine.run_convergence', panel)
    def proofread_chat(messages, **kw):
        assert 'independently reviewed' in messages[-1].content
        events.append('proofreader')
        return ChatResponse('verdict: clean\nflags: []\n', 'test-model', 'dartmouth')
    # Actual ProofreaderAgent.run -> build_messages -> handler -> source-bound receipt.
    monkeypatch.setattr('llmxive.agents.base.chat_with_fallback', proofread_chat)
    monkeypatch.setattr('llmxive.agents.base.runlog.append_entry', lambda *a, **kw: None)
    monkeypatch.setattr('llmxive.agents.latex_build.build_paper', lambda *a, **kw: {'ok': True})
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'paper/source/main.tex', 'contents': TEX}]))
    assert events == ['verify', 'panel', 'verify', 'proofreader']
    assert proofreader_clean(ctx.project_id, repo_root=ctx.project_dir.parent.parent)
    assert paper_implementation_review_current(ctx.project_dir, tasks.parent, model="test-model")
    (ctx.project_dir / 'paper/source/main.tex').write_text(TEX + '% later edit\n')
    assert not paper_implementation_review_current(ctx.project_dir, tasks.parent, model="test-model")
    assert not proofreader_clean(ctx.project_id, repo_root=ctx.project_dir.parent.parent)


def test_all_checked_legacy_tasks_cannot_bypass_independent_review(paper, monkeypatch):
    from llmxive.pipeline.graph import _paper_complete_preconditions_met
    agent, ctx, tasks = paper
    tasks.write_text(tasks.read_text().replace('[ ]', '[X]'))
    assert not _paper_complete_preconditions_met(ctx.project_id, ctx.project_dir, repo_root=ctx.project_dir.parent.parent)
    step = agent.mechanical_step(ctx)
    assert step['deterministic_write'] and not step['skip_llm']
    agent.write_artifacts(ctx, step, ChatResponse('', 'deterministic-no-llm', 'dartmouth'))
    assert '[X]' not in tasks.read_text()  # actual missing artifacts reject deterministically


def test_paper_recovery_uses_free_models_then_planner_and_stops_at_bound(paper, monkeypatch):
    from datetime import UTC, datetime

    from llmxive.agents.lifecycle import is_valid_transition
    from llmxive.pipeline import graph
    from llmxive.state import execution_status, unverifiable
    from llmxive.types import Project, Stage
    _agent, ctx, tasks = paper
    repo = ctx.project_dir.parent.parent
    now = datetime.now(UTC)
    project = Project(id=ctx.project_id, title='Paper recovery', field='test',
                      current_stage=Stage.PAPER_IN_PROGRESS, created_at=now, updated_at=now,
                      speckit_research_dir=f'projects/{ctx.project_id}/specs/001',
                      speckit_paper_dir=str(tasks.parent.relative_to(repo)))
    def reject():
        unverifiable.record_unverifiable(project.id, 'paper:T001', 'Missing scaffold', repo_root=repo)
    unverifiable.record_unverifiable(project.id, 'T001', 'Preserved research failure', repo_root=repo)
    reject()
    seen = []
    monkeypatch.setattr(execution_status, 'bump_model_tier', lambda *a, **kw: seen.append(kw) or 1)
    assert graph._decide_next_stage(project, ctx.project_dir, repo_root=repo) == Stage.PAPER_IN_PROGRESS
    assert seen[0]['free_only'] is True
    assert '[ ] T001' in tasks.read_text()
    def exhausted(*a, **kw):
        raise ValueError('No higher free model')
    monkeypatch.setattr(execution_status, 'bump_model_tier', exhausted)
    reject()
    before = execution_status.replan_rounds(project.id, repo_root=repo)
    assert graph._decide_next_stage(project, ctx.project_dir, repo_root=repo) == Stage.PAPER_CLARIFIED
    assert graph.STAGE_TO_AGENT[Stage.PAPER_CLARIFIED] == 'paper_planner'
    assert is_valid_transition(Stage.PAPER_IN_PROGRESS, Stage.PAPER_CLARIFIED)
    assert execution_status.replan_rounds(project.id, repo_root=repo) == before + 1
    assert 'Missing scaffold' in (ctx.project_dir / 'paper/.specify/memory/kickback_feedback.md').read_text()
    assert not (ctx.project_dir / '.specify/memory/kickback_feedback.md').exists()
    for _ in range(execution_status.MAX_REPLAN_ROUNDS - before - 1):
        reject()
        assert graph._decide_next_stage(project, ctx.project_dir, repo_root=repo) == Stage.PAPER_CLARIFIED
    reject()
    assert graph._decide_next_stage(project, ctx.project_dir, repo_root=repo) == Stage.AGENT_BLOCKED
    assert unverifiable.recorded_keys(project.id, repo_root=repo) == {'T001', 'paper:T001'}


def test_deterministic_write_hook_runs_verification_without_dummy_author_call(paper, monkeypatch):
    agent, ctx, tasks = paper
    tasks.write_text(tasks.read_text().replace('[ ]', '[X]'))
    monkeypatch.setattr('llmxive.speckit.slash_command.chat_with_fallback', lambda *a, **kw: pytest.fail('dummy author call'))
    monkeypatch.setattr('llmxive.speckit.slash_command._validate_artifact_citations', lambda *a, **kw: None)
    monkeypatch.setattr('llmxive.speckit.slash_command.runlog.append_entry', lambda *a, **kw: None)
    result = agent.run(ctx)
    assert '[X]' not in tasks.read_text()
    assert str(tasks.relative_to(ctx.project_dir.parent.parent)) in result.outputs
    assert result.model_name == 'deterministic-no-llm'


def test_repeated_protocol_and_write_refusals_are_bounded(paper):
    from llmxive.state import unverifiable
    agent, ctx, tasks = paper
    for _ in range(3):
        agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(verdict='failed'))
    assert '[ ] T001' in tasks.read_text()
    assert unverifiable.recorded_keys(ctx.project_id, repo_root=ctx.project_dir.parent.parent) == {'paper:final-review'}
    assert 'proposal rejected 3 times' in (ctx.project_dir / 'paper/.specify/memory/implementation_failure.yaml').read_text()


def test_review_receipt_invalidates_on_model_or_policy_change(paper, monkeypatch):
    from llmxive.speckit.paper_implement_cmd import (
        _paper_review_hash,
        _paper_review_policy_hash,
        paper_implementation_review_current,
    )
    agent, ctx, tasks = paper
    agent.write_artifacts(ctx, agent.mechanical_step(ctx), proposal(artifacts=[{'path': 'paper/source/main.tex', 'contents': TEX}]))
    tasks.write_text(tasks.read_text().splitlines()[0] + '\n')
    repo = ctx.project_dir.parent.parent
    receipt = ctx.project_dir / 'paper/.specify/memory/implementation_review.yaml'
    receipt.write_text(yaml.safe_dump({'version': 1, 'hash': _paper_review_hash(ctx.project_dir, tasks.parent),
                                      'policy': _paper_review_policy_hash(repo), 'model': ctx.default_model}))
    assert paper_implementation_review_current(ctx.project_dir, tasks.parent, model=ctx.default_model)
    assert not paper_implementation_review_current(ctx.project_dir, tasks.parent, model='different-free-model')
    (repo / 'web').mkdir()
    (repo / 'web/about.html').write_text('Changed scientific review policy')
    assert not paper_implementation_review_current(ctx.project_dir, tasks.parent, model=ctx.default_model)


def test_track_specific_recovery_preserves_other_track_records(paper):
    from llmxive.state import unverifiable
    _, ctx, _ = paper
    repo = ctx.project_dir.parent.parent
    unverifiable.record_unverifiable(ctx.project_id, 'T001', 'research failure', repo_root=repo)
    unverifiable.record_unverifiable(ctx.project_id, 'paper:T001', 'paper failure', repo_root=repo)
    unverifiable.clear(ctx.project_id, repo_root=repo, track='research')
    assert unverifiable.recorded_keys(ctx.project_id, repo_root=repo) == {'paper:T001'}
