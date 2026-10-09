"""Repair diagnosis uses observed routing and the caller's import namespace."""
import json
import sys

import pytest

from llmxive.repair import runner
from llmxive.repair.report import render


def test_dispatch_facts_follow_source_without_executing_it(tmp_path):
    graph = tmp_path / 'src/llmxive/pipeline/graph.py'
    graph.parent.mkdir(parents=True)
    source = '''from llmxive.speckit.implement_cmd import ImplementerAgent as Worker
raise AssertionError("source must never execute")
STAGE_TO_AGENT = {Stage.IN_PROGRESS: "implementer", Stage.VALIDATED: "initializer"}
_SPECKIT_AGENTS = {"implementer": Worker}
'''
    graph.write_text(source)
    evidence = {'failures': [{'stage': 'in_progress'}, {'stage': 'unknown'}]}
    facts = runner.stage_context(tmp_path, evidence)
    assert facts == [{'stage': 'in_progress', 'default_agent': 'implementer',
                      'source': 'src/llmxive/pipeline/graph.py:3',
                      'agent_source': 'src/llmxive/speckit/implement_cmd.py'}]
    # Facts track the current source instead of hardcoding historical routing.
    graph.write_text(source.replace('Stage.IN_PROGRESS: "implementer"',
                                    'Stage.IN_PROGRESS: "recovery"'))
    assert runner.stage_context(tmp_path, evidence)[0]['default_agent'] == 'recovery'
    assert 'agent_source' not in runner.stage_context(tmp_path, evidence)[0]


def test_dispatch_context_does_not_follow_external_source(tmp_path):
    outside = tmp_path / 'outside.py'
    outside.write_text('STAGE_TO_AGENT = {Stage.IN_PROGRESS: "secret"}')
    repo = tmp_path / 'repo'
    graph = repo / 'src/llmxive/pipeline/graph.py'
    graph.parent.mkdir(parents=True)
    graph.symlink_to(outside)
    assert runner.stage_context(repo, {'failures': [{'stage': 'in_progress'}]}) == []


def test_proposal_gets_lookup_bindings_and_stage_facts(tmp_path, monkeypatch):
    source = 'src/llmxive/agents/project_initializer.py'
    text = ('from llmxive.config import repo_root as _repo_root\n'
            'def initialize(): return _repo_root()\n')
    path = tmp_path / source
    path.parent.mkdir(parents=True)
    path.write_text(text)
    graph = tmp_path / 'src/llmxive/pipeline/graph.py'
    graph.parent.mkdir(parents=True)
    graph.write_text('STAGE_TO_AGENT = {Stage.IN_PROGRESS: "implementer"}\n')
    calls = []

    def ask(prompt, **kwargs):
        calls.append(prompt)
        if len(calls) == 1:
            evidence = json.loads(prompt.split('EVIDENCE:\n')[1].split('\nFILES:')[0])
            assert evidence['stage_dispatch_context'][0]['default_agent'] == 'implementer'
            return {'paths': [source], 'problem': 'initialization hypothesis'}
        bindings = json.loads(prompt.split('caller):\n')[1])
        binding = bindings[source][0]
        assert binding['imported_from'] == 'llmxive.config.repo_root'
        assert binding['used_as'] == 'llmxive.agents.project_initializer._repo_root'
        assert 'hypothesis' in prompt and 'assert the caller actually' in prompt
        raise RuntimeError('stop before generating candidate')

    monkeypatch.setattr(runner, '_ask', ask)
    with pytest.raises(RuntimeError, match='stop before'):
        runner.run(tmp_path, {'failures': [{'stage': 'in_progress'}]}, tmp_path / 'output')
    assert len(calls) == 2
    saved = json.loads((tmp_path / 'output/import-bindings.json').read_text())
    assert saved[source][0]['used_as'].endswith('project_initializer._repo_root')
    assert path.read_text() == text
    # The real summary consumes both saved artifacts, rather than leaving them
    # as diagnostic dead ends that only a test or manual inspection can read.
    (tmp_path / 'output').rename(tmp_path / 'attempt-1')
    summary = render(tmp_path)
    assert 'Observed stage default: in_progress → implementer' in summary
    assert ('llmxive.config.repo_root → '
            'llmxive.agents.project_initializer._repo_root') in summary


def test_retry_diagnostics_keep_baseline_and_candidate_distinct(tmp_path, monkeypatch):
    output = tmp_path / 'output'
    monkeypatch.setattr(sys, 'argv', ['repair', '--repo', str(tmp_path), '--output', str(output)])
    monkeypatch.setattr(runner, 'select_evidence', lambda *a: {'failures': [{'stage': 'in_progress'}]})
    calls = []

    def attempt(repo, evidence, destination, **kwargs):
        calls.append(evidence)
        destination.mkdir(parents=True)
        if len(calls) == 1:
            (destination / 'before.log').write_text('baseline defect reproduced')
            (destination / 'after.log').write_text('candidate failed: wrong lookup namespace')
            raise RuntimeError('candidate failed')
        assert evidence['test_diagnostics'] == {
            'before.log': 'baseline defect reproduced',
            'after.log': 'candidate failed: wrong lookup namespace',
        }
        # Compaction must preserve the labels rather than concatenating logs.
        assert json.loads(runner.render_evidence(evidence))['test_diagnostics'] == evidence['test_diagnostics']
        return {'status': 'no_candidate'}

    monkeypatch.setattr(runner, 'run', attempt)
    assert runner.main() == 0
    summary = render(output)
    assert 'before.log (tail):' in summary and 'after.log (tail):' in summary
    assert 'candidate failed: wrong lookup namespace' in summary
    assert 'baseline defect reproduced' in summary
