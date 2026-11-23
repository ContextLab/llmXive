"""Repairs use observed paths and exact edits without truncating source files."""
import json

import pytest

from llmxive.repair.runner import materialize_edits, observe_failure_paths, run


def test_one_bounded_json_correction_retains_both_responses(tmp_path, monkeypatch):
    from llmxive.backends.base import ChatResponse
    from llmxive.repair import runner
    responses = iter([
        ChatResponse(text='{**"paths": []}', model='author', backend='dartmouth'),
        ChatResponse(text='{"skip":"insufficient evidence"}', model='corrector', backend='dartmouth'),
    ])
    monkeypatch.setattr(runner, 'chat_with_fallback', lambda *a, **k: next(responses))
    response_path = tmp_path/'selection-response.txt'
    result = runner._ask('select', response_path=response_path)
    assert result['skip'] == 'insufficient evidence'
    assert result['_producer_model'] == 'corrector'
    assert response_path.read_text() == '{**"paths": []}'
    assert json.loads((tmp_path/'selection-response-format-retry.txt').read_text()) == {
        'skip': 'insufficient evidence'}


def test_exact_edit_preserves_large_unmodified_tail(tmp_path):
    name = 'src/llmxive/large.py'
    text = 'def answer(): return 0\n' + '# untouched\n' * 5000
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_text(text)
    proposal = {'files': {'tests/unit/test_repair_answer.py': 'assert True\n'},
                'edits': {name: [{'old': 'return 0', 'new': 'return 1'}]}}
    result = materialize_edits(proposal, {name: text}, tmp_path)
    assert result['files'][name] == text.replace('return 0', 'return 1')
    assert path.read_text() == text


@pytest.mark.parametrize('old', ['missing', 'same'])
def test_nonunique_edit_is_rejected(tmp_path, old):
    with pytest.raises(ValueError, match='exactly once'):
        materialize_edits({'edits': {'src/llmxive/a.py': [{'old': old, 'new': ''}]}},
                          {'src/llmxive/a.py': 'same same'}, tmp_path)


def test_unread_existing_file_cannot_be_replaced(tmp_path):
    name = 'src/llmxive/hidden.py'
    path = tmp_path/name
    path.parent.mkdir(parents=True)
    path.write_text('preserved')
    with pytest.raises(ValueError, match='was not read'):
        materialize_edits({'files': {name: 'replacement'}}, {}, tmp_path)
    assert path.read_text() == 'preserved'


def test_actual_file_collision_is_supplied_as_evidence(tmp_path):
    project = tmp_path/'projects/PROJ-1-example'
    project.mkdir(parents=True)
    placeholder = project/'src'
    placeholder.write_text('(Directory created)\n')
    evidence = {'project_id': project.name,
                'last_error': "[Errno 20] Not a directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-1-example/src/config'"}
    result = {item['path']: item for item in observe_failure_paths(tmp_path, evidence)}
    assert result['projects/PROJ-1-example/src']['kind'] == 'file'
    assert result['projects/PROJ-1-example/src']['content'] == '(Directory created)\n'
    assert placeholder.read_text() == '(Directory created)\n'


def test_invented_selection_fails_before_source_or_proposal(tmp_path, monkeypatch):
    from llmxive.repair import runner
    calls = []
    def select(*args, **kwargs):
        calls.append(args)
        return {'paths': ['src/llmxive/invented.py']}
    monkeypatch.setattr(runner, '_ask', select)
    with pytest.raises(ValueError, match='not in FILES'):
        run(tmp_path, {}, tmp_path/'output')
    assert len(calls) == 3  # bounded reselection; invalid paths never reach source/proposal


def test_proposal_receives_complete_large_source(tmp_path, monkeypatch):
    from llmxive.repair import runner
    name = 'src/llmxive/large.py'
    text = '# filler\n' * 6000 + 'def tail(): return 42\n'
    path = tmp_path/name
    path.parent.mkdir(parents=True)
    path.write_text(text)
    calls = []
    def ask(prompt, **kwargs):
        calls.append(prompt)
        if len(calls) == 1:
            return {'paths': [name], 'problem': 'tail behavior'}
        assert 'def tail(): return 42' in prompt
        raise RuntimeError('stop before model proposal')
    monkeypatch.setattr(runner, '_ask', ask)
    with pytest.raises(RuntimeError, match='stop before'):
        run(tmp_path, {}, tmp_path/'output')
    assert json.loads((tmp_path/'output/source-context.json').read_text())[name] == text


def test_summary_shows_inspected_source_and_attempted_edit_targets(tmp_path):
    from llmxive.repair.report import render
    attempt = tmp_path/'attempt-1'
    attempt.mkdir()
    (attempt/'source-context.json').write_text(json.dumps({'src/llmxive/a.py': 'source'}))
    (attempt/'proposal-response.json').write_text(json.dumps({
        'edits': {'src/llmxive/a.py': [{'old': 'source', 'new': 'fixed'}]},
        'files': {'tests/unit/test_repair_a.py': 'test'},
    }))
    summary = render(tmp_path)
    assert 'Complete source inspected: `src/llmxive/a.py` (6 bytes)' in summary
    assert 'Exact-edit targets: `src/llmxive/a.py`' in summary
    assert 'File proposals: `tests/unit/test_repair_a.py`' in summary
