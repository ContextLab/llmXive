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
