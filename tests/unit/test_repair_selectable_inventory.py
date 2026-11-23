"""Repair selection must not advertise files that context policy rejects."""
import pytest

from llmxive.repair import runner


def test_prompt_inventory_contains_only_selectable_files(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    allowed = ['src/llmxive/project_files.py', 'tests/unit/test_durable_placeholder.py',
               'agents/prompts/implementer.md']
    excluded = ['src/llmxive/repair/runner.py', 'src/llmxive/repair/report.py',
                'tests/unit/conftest.py', 'src/llmxive/__pycache__/cached.py',
                'agents/prompts/invalid.txt']
    for name in [*allowed, *excluded]:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('observed source')
    outside = tmp_path / 'outside.py'
    outside.write_text('external source must not be selectable')
    (repo / 'src/llmxive/external.py').symlink_to(outside)
    (repo / 'src/llmxive/internal.py').symlink_to(repo / allowed[0])
    captured = []

    def select(prompt, **kwargs):
        captured.extend(prompt.split('\nFILES:\n')[1].splitlines())
        return {'skip': 'inventory probe'}

    monkeypatch.setattr(runner, '_ask', select)
    result = runner.run(repo, {}, tmp_path / 'output')
    assert result['status'] == 'no_candidate'
    assert captured == sorted(allowed)
    # Every advertised file survives actual context selection; no policy bypass.
    assert runner.read_context(repo, captured, captured, {}) == {
        name: 'observed source' for name in allowed}


def test_inventory_reuses_policy_instead_of_copying_a_denylist(tmp_path, monkeypatch):
    path = tmp_path / 'src/llmxive/example.py'
    path.parent.mkdir(parents=True)
    path.write_text('source')
    seen = []

    def policy(name):
        seen.append(name)
        raise ValueError('new policy restriction')

    monkeypatch.setattr(runner, 'safe_path', policy)
    assert runner.selectable_files(tmp_path) == []
    assert seen == ['src/llmxive/example.py']


@pytest.mark.parametrize('path', ['src/llmxive/repair/runner.py', 'tests/unit/conftest.py'])
def test_forbidden_manual_selection_remains_rejected(tmp_path, path):
    with pytest.raises(ValueError, match='outside repair scope'):
        runner.read_context(tmp_path, [path], [path], {})
