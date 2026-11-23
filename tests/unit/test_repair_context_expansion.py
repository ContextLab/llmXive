"""Rejected patches are regenerated from real source before acceptance gates."""
import json

import pytest

from llmxive.repair import runner


@pytest.fixture
def repair_repo(tmp_path):
    source = 'src/llmxive/answer.py'
    related = 'tests/unit/test_answer.py'
    regression = 'tests/unit/test_repair_answer.py'
    for name, content in ((source, 'def answer(): return 0\n'),
                          (related, 'def test_existing(): assert True\n')):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    output = tmp_path / 'evidence'
    output.mkdir()
    proposal = {
        'title': 'Correct answer', 'explanation': 'Observed zero',
        'edits': {source: [{'old': 'return 0', 'new': 'return 42'}]},
        'files': {regression: 'from llmxive.answer import answer\ndef test_answer(): assert answer() == 42\n'},
        'regression': regression, 'related_tests': [related], '_producer_model': 'test',
    }
    return tmp_path, output, source, related, proposal


def test_unread_patch_is_discarded_then_regenerated_from_actual_source(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    calls = []
    def ask(prompt, **kwargs):
        calls.append(prompt)
        if len(calls) == 1:
            wrong = dict(proposal, edits={source: [{'old': 'invented text', 'new': 'wrong'}]})
            return wrong
        assert 'def answer(): return 0' in prompt
        assert 'previous proposal edited unread files' in prompt
        return proposal
    monkeypatch.setattr(runner, '_ask', ask)
    result = runner.propose_fix(repo, {}, output, [source, related], {}, {})
    assert len(calls) == 2
    assert result['files'][source] == 'def answer(): return 42\n'
    assert (repo / source).read_text() == 'def answer(): return 0\n'
    assert json.loads((output / 'proposal-response.json').read_text())['edits'][source][0]['old'] == 'invented text'
    assert (output / 'proposal-response-revision-1.json').exists()
    assert json.loads((output / 'source-context.json').read_text())[source] == (repo / source).read_text()


def test_missing_regression_contents_can_be_corrected(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    calls = []
    def ask(prompt, **kwargs):
        calls.append(prompt)
        return dict(proposal, files={}) if len(calls) == 1 else proposal
    monkeypatch.setattr(runner, '_ask', ask)
    result = runner.propose_fix(repo, {}, output, [source, related], {}, {source: (repo/source).read_text()})
    assert proposal['regression'] in result['files']
    assert 'repair must contain 2-5 files' in calls[1]


def test_syntax_error_is_corrected_before_sandbox(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    calls = []

    def ask(prompt, **kwargs):
        calls.append(prompt)
        if len(calls) == 1:
            return dict(proposal, edits={source: [{'old': 'return 0', 'new': 'return ('}]})
        assert f'{source}:1:' in prompt
        assert 'SyntaxError' in prompt and 'never closed' in prompt
        return proposal

    monkeypatch.setattr(runner, '_ask', ask)
    result = runner.propose_fix(repo, {}, output, [source, related], {},
                                {source: (repo/source).read_text()})
    assert len(calls) == 2
    assert result['files'][source] == 'def answer(): return 42\n'
    assert (repo/source).read_text() == 'def answer(): return 0\n'
    assert 'SyntaxError' in (output/'proposal-validation.json').read_text()


def test_repeated_invalid_patch_exhausts_three_calls_without_mutation(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    calls = []
    def ask(prompt, **kwargs):
        calls.append(prompt)
        return dict(proposal, edits={source: [{'old': 'nonexistent', 'new': 'wrong'}]})
    monkeypatch.setattr(runner, '_ask', ask)
    with pytest.raises(ValueError, match='exactly once'):
        runner.propose_fix(repo, {}, output, [source, related], {}, {source: (repo/source).read_text()})
    assert len(calls) == 3
    assert (repo/source).read_text() == 'def answer(): return 0\n'
    assert not (output/'proposal.json').exists()


@pytest.mark.parametrize('target', ['../outside.py', 'src/llmxive/repair/runner.py', 'src/llmxive/link.py'])
def test_expansion_cannot_read_forbidden_or_symlink_source(repair_repo, monkeypatch, target):
    repo, output, source, related, proposal = repair_repo
    secret = repo/'outside.py'
    secret.write_text('SENSITIVE SENTINEL')
    if target.endswith('link.py'):
        (repo/target).symlink_to(secret)
    calls = []
    def ask(prompt, **kwargs):
        assert 'SENSITIVE SENTINEL' not in prompt
        calls.append(prompt)
        return dict(proposal, edits={target: [{'old': 'x', 'new': 'y'}]})
    monkeypatch.setattr(runner, '_ask', ask)
    with pytest.raises(ValueError):
        runner.propose_fix(repo, {}, output, [source, related, target], {}, {})
    assert len(calls) == 3
    assert secret.read_text() == 'SENSITIVE SENTINEL'


def test_expansion_retains_total_byte_and_file_caps(repair_repo):
    repo, _output, source, _related, _proposal = repair_repo
    with pytest.raises(ValueError, match='250 KB'):
        runner.read_context(repo, [source], [source], {'existing': 'x'*250_000})
    with pytest.raises(ValueError, match='12 total'):
        runner.read_context(repo, [source], [source], {str(n): '' for n in range(12)})


def test_run_reaches_unchanged_baseline_gate_only_after_rereading(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    responses = iter([
        {'paths': [related], 'problem': 'zero instead of 42'},
        proposal,
        proposal,
    ])
    monkeypatch.setattr(runner, '_ask', lambda *a, **k: next(responses))
    def baseline(path, tests, log, **kwargs):
        assert (path/source).read_text() == 'def answer(): return 0\n'
        assert (path/proposal['regression']).is_file()
        assert tests == [proposal['regression']]
        raise RuntimeError('reached real baseline gate')
    monkeypatch.setattr(runner, 'isolated_tests', baseline)
    with pytest.raises(RuntimeError, match='reached real baseline gate'):
        runner.run(repo, {}, output)
    assert (repo/source).read_text() == 'def answer(): return 0\n'


def test_oversized_selection_corrects_before_single_proposal_and_baseline(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    large = 'src/llmxive/large.py'
    (repo/large).write_text('#' + 'x'*250_000)
    prompts = []
    proposals = []
    baselines = []
    original_propose = runner.propose_fix

    def ask(prompt, **kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:
            assert f'"{large}": 250001' in prompt
            return {'paths': [large], 'problem': 'zero instead of 42'}
        if len(prompts) == 2:
            assert '250001 bytes > 250000 bytes' in prompt
            assert 'PREVIOUS SELECTION REJECTED' in prompt
            return {'paths': [source, related], 'problem': 'zero instead of 42'}
        return proposal

    def propose(*args, **kwargs):
        proposals.append(args[-1])
        return original_propose(*args, **kwargs)

    def baseline(path, tests, log, **kwargs):
        baselines.append(tests)
        assert (path/source).read_text() == 'def answer(): return 0\n'
        assert (path/proposal['regression']).is_file()
        raise RuntimeError('reached unchanged baseline gate')

    monkeypatch.setattr(runner, '_ask', ask)
    monkeypatch.setattr(runner, 'propose_fix', propose)
    monkeypatch.setattr(runner, 'isolated_tests', baseline)
    with pytest.raises(RuntimeError, match='reached unchanged baseline gate'):
        runner.run(repo, {}, output)
    assert len(prompts) == 3  # two selections, one proposal
    assert len(proposals) == len(baselines) == 1
    assert set(proposals[0]) == {source, related}
    assert json.loads((output/'selection-response.json').read_text())['paths'] == [large]
    assert json.loads((output/'selection-response-revision-1.json').read_text())['paths'] == [source, related]
    assert json.loads((output/'selection.json').read_text())['paths'] == [source, related]
    assert (repo/source).read_text() == 'def answer(): return 0\n'


@pytest.mark.parametrize('kind', ['oversized', 'outside_inventory', 'too_many', 'not_strings'])
def test_selection_exhaustion_never_reaches_proposal_or_reads_untrusted_source(
        repair_repo, monkeypatch, kind):
    repo, output, source, _related, _proposal = repair_repo
    large = 'src/llmxive/large.py'
    (repo/large).write_text('#' + 'x'*250_000)
    secret = repo/'private.txt'
    secret.write_text('SECRET SELECTION SENTINEL')
    paths = {'oversized': [large], 'outside_inventory': ['private.txt'],
             'too_many': [source]*7, 'not_strings': [{}]}[kind]
    calls = []

    def ask(prompt, **kwargs):
        assert 'SECRET SELECTION SENTINEL' not in prompt
        calls.append(prompt)
        return {'paths': paths, 'problem': 'test invalid selection'}

    monkeypatch.setattr(runner, '_ask', ask)
    monkeypatch.setattr(runner, 'propose_fix', lambda *a, **k: pytest.fail('invalid proposal reached'))
    monkeypatch.setattr(runner, 'isolated_tests', lambda *a, **k: pytest.fail('invalid baseline reached'))
    with pytest.raises(ValueError):
        runner.run(repo, {}, output)
    assert len(calls) == 3
    assert len(list(output.glob('selection-validation*.json'))) == 3
    assert not (output/'source-context.json').exists()
    assert secret.read_text() == 'SECRET SELECTION SENTINEL'


def test_overflow_can_replace_context_then_reach_unchanged_baseline_gate(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    old = 'src/llmxive/old_context.py'
    (repo / old).write_text('#' + 'x' * 249_990)
    prompts = []

    def ask(prompt, **kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:
            return {'paths': [old], 'problem': 'wrong answer through existing caller'}
        if len(prompts) == 2:
            return proposal  # Append-only expansion would exceed the unchanged cap.
        if len(prompts) == 3:
            assert '250 KB' in prompt
            return {'context_paths': [source, related], 'reason': 'Replace irrelevant large context'}
        assert 'def answer(): return 0' in prompt
        return proposal

    def baseline(path, tests, log, **kwargs):
        assert (path / source).read_text() == 'def answer(): return 0\n'
        assert tests == [proposal['regression']]
        raise RuntimeError('unchanged isolated baseline gate reached')

    monkeypatch.setattr(runner, '_ask', ask)
    monkeypatch.setattr(runner, 'isolated_tests', baseline)
    with pytest.raises(RuntimeError, match='unchanged isolated baseline gate reached'):
        runner.run(repo, {}, output)
    assert len(prompts) == 4  # one selection, exactly three bounded proposal turns
    final_context = json.loads((output / 'source-context.json').read_text())
    assert set(final_context) == {source, related}
    assert final_context[source] == (repo / source).read_text()
    assert (repo / old).stat().st_size == 249_991


def test_proposal_gets_exact_baseline_tests_and_invalid_related_path_feedback(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    invented = 'tests/unit/test_repair_previous_attempt.py'
    prompts = []

    def ask(prompt, **kwargs):
        prompts.append(prompt)
        assert f'EXISTING_RELATED_TESTS:\n["{related}"]' in prompt
        if len(prompts) == 1:
            return dict(proposal, related_tests=[invented])
        assert f'related tests must exist in the baseline: {invented!r}' in prompt
        return proposal

    monkeypatch.setattr(runner, '_ask', ask)
    result = runner.propose_fix(repo, {}, output, [source, related], {},
                                {source: (repo / source).read_text()})
    assert len(prompts) == 2
    assert result['related_tests'] == [related]
    assert not (repo / invented).exists()


@pytest.mark.parametrize('kind', ['outside', 'unknown', 'symlink', 'oversized', 'too_many',
                                  'not_strings', 'mixed_proposal', 'only_requests'])
def test_context_replacement_cannot_bypass_scope_budget_or_candidate_gates(repair_repo, monkeypatch, kind):
    repo, output, source, _related, proposal = repair_repo
    secret = repo / 'outside.py'
    secret.write_text('PRIVATE_CONTEXT_SENTINEL')
    link = repo / 'src/llmxive/link.py'
    link.symlink_to(secret)
    large = repo / 'src/llmxive/large.py'
    large.write_text('#' + 'x' * 250_000)
    paths = {'outside': ['../outside.py'], 'unknown': ['src/llmxive/invented.py'],
             'symlink': ['src/llmxive/link.py'], 'oversized': ['src/llmxive/large.py'],
             'too_many': [source] * 13, 'not_strings': [{}],
             'mixed_proposal': [source], 'only_requests': [source]}[kind]
    prompts = []

    def ask(prompt, **kwargs):
        prompts.append(prompt)
        assert 'PRIVATE_CONTEXT_SENTINEL' not in prompt
        request = {'context_paths': paths, 'reason': 'Inspect real source'}
        return dict(proposal, **request) if kind == 'mixed_proposal' else request

    monkeypatch.setattr(runner, '_ask', ask)
    monkeypatch.setattr(runner, 'isolated_tests', lambda *a, **k: pytest.fail('request reached execution'))
    with pytest.raises(ValueError):
        runner.propose_fix(repo, {}, output, runner.selectable_files(repo), {},
                           {source: (repo / source).read_text()})
    assert len(prompts) == 3
    assert not (output / 'proposal.json').exists()
    assert not (repo / proposal['regression']).exists()
    assert secret.read_text() == 'PRIVATE_CONTEXT_SENTINEL'
    assert (repo / source).read_text() == 'def answer(): return 0\n'
    if kind == 'only_requests':
        assert 'three-turn proposal budget' in (output / 'proposal-validation-revision-2.json').read_text()


def test_replaced_away_source_must_be_reread_before_editing(repair_repo, monkeypatch):
    repo, output, source, related, proposal = repair_repo
    responses = iter([{'context_paths': [related], 'reason': 'Inspect fixture conventions'},
                      proposal, proposal])
    prompts = []

    def ask(prompt, **kwargs):
        prompts.append(prompt)
        return next(responses)

    monkeypatch.setattr(runner, '_ask', ask)
    result = runner.propose_fix(repo, {}, output, [source, related], {},
                               {source: (repo / source).read_text()})
    assert result['files'][source] == 'def answer(): return 42\n'
    assert 'previous proposal edited unread files' in prompts[2]
    assert set(json.loads((output / 'source-context-revision-1.json').read_text())) == {related}
    assert set(json.loads((output / 'source-context-revision-2.json').read_text())) == {source, related}
    assert json.loads((output / 'context-request.json').read_text())['replaced_paths'] == [source]


def test_a_selection_that_overflows_is_fitted_in_the_models_own_order(repair_repo, monkeypatch):
    """Run 38089862803, attempt 3: three rounds, the same over-budget files, a crash.

    The model was given every size and the budget and returned 275 KB three
    times. Fitting is arithmetic, so the runner does it: files are kept in the
    order the model listed them, one that would overflow is dropped WHOLE, and
    smaller ones after it still get in. No second selection turn is spent.
    """
    repo, output, source, related, proposal = repair_repo
    big_a, big_b = 'src/llmxive/big_a.py', 'src/llmxive/big_b.py'
    (repo/big_a).write_text('#' + 'a'*150_000)
    (repo/big_b).write_text('#' + 'b'*120_000)
    prompts = []
    seen = []

    def ask(prompt, **kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:
            return {'paths': [big_a, big_b, source, related], 'problem': 'zero instead of 42'}
        return proposal

    original_propose = runner.propose_fix

    def propose(*args, **kwargs):
        seen.append((args[-2], args[-1]))
        return original_propose(*args, **kwargs)

    def baseline(path, tests, log, **kwargs):
        raise RuntimeError('reached unchanged baseline gate')

    monkeypatch.setattr(runner, '_ask', ask)
    monkeypatch.setattr(runner, 'propose_fix', propose)
    monkeypatch.setattr(runner, 'isolated_tests', baseline)
    with pytest.raises(RuntimeError, match='reached unchanged baseline gate'):
        runner.run(repo, {}, output)
    assert len(prompts) == 2, 'one selection and one proposal: no turn spent on arithmetic'
    selection, context = seen[0]
    assert list(context) == [big_a, source, related]
    assert context[big_a] == (repo/big_a).read_text(), 'kept files are complete, never truncated'
    assert selection['dropped_for_size'] == [big_b]
    assert json.loads((output/'selection-fit.json').read_text()) == {
        'kept': [big_a, source, related], 'dropped_for_size': [big_b]}
    assert json.loads((output/'selection.json').read_text())['paths'] == [big_a, source, related]
    # The model's own answer is preserved as it gave it.
    assert json.loads((output/'selection-response.json').read_text())['paths'] == [big_a, big_b, source, related]
    # The proposer is told what it is not looking at and how to get it.
    assert 'SELECTED BUT NOT IN SOURCE' in prompts[1] and big_b in prompts[1].split('SELECTED BUT NOT IN SOURCE')[1].split('FILE_BYTES')[0]


def test_fitting_decides_size_and_nothing_else(repair_repo):
    repo, _output, source, related, _proposal = repair_repo
    assert runner.fit_selection(repo, [source, related], [source, related]) == ([source, related], [])
    # A path that is not selectable is left for read_context to refuse.
    kept, dropped = runner.fit_selection(repo, ['private.txt', source], [source])
    assert (kept, dropped) == (['private.txt', source], [])
    with pytest.raises(ValueError, match='not in FILES'):
        runner.read_context(repo, kept, [source], {})
