"""Execute the generated CLI with its declared arguments and original requirements."""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive import sandbox
from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent

CLI = '''import argparse, json, os
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--max-n', required=True)
p.add_argument('--prime', required=True)
p.add_argument('--label', default='')
a = p.parse_args()
assert 'DARTMOUTH_CHAT_API_KEY' not in os.environ
Path('result.json').write_text(json.dumps(vars(a)))
'''


@pytest.mark.parametrize('prime', ['5', 5, 5.0])
def test_implementer_executes_required_cli_arguments_as_literal_strings(tmp_path, monkeypatch, prime):
    import json
    project = tmp_path / 'projects/PROJ-901-argv'
    feature = project / 'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature / 'tasks.md'
    tasks.write_text('- [ ] T001 Run the specified CLI and write result.json\n')
    monkeypatch.setenv('DARTMOUTH_CHAT_API_KEY', 'test-secret-not-for-child')
    literal = 'a b; $(touch SHOULD_NOT_EXIST)'
    document = {'task_id':'T001', 'verdict':'completed', 'artifacts':[
        {'path':'code/run.py','contents':CLI,'execute':True,
         'args':['--max-n','1000','--prime',prime,'--label',literal]}]}
    ImplementerAgent().write_artifacts(SimpleNamespace(project_dir=project),
        {'tasks_path':str(tasks), 'feature_dir':str(feature),
         'next_task_id':'T001','all_complete':False},
        ChatResponse(text=yaml.safe_dump(document), model='test', backend='dartmouth'))
    assert json.loads((project/'result.json').read_text()) == {
        'max_n':'1000','prime':str(prime),'label':literal}
    assert not (project/'SHOULD_NOT_EXIST').exists()
    assert '- [X] T001' in tasks.read_text()
    log = (project/'code/.tasks/T001.code_run.py.log').read_text()
    assert '--max-n' in log and '--prime' in log
    # Missing required arguments is still a genuine failure, never masked.
    failed = sandbox.run_python_script(project_dir=project, script_relpath='code/run.py')
    assert not failed.ok and failed.returncode == 2


@pytest.mark.parametrize('args', ['--max-n 1000', [1000], ['bad\x00arg']])
def test_invalid_argv_fails_without_running(tmp_path, args):
    result = sandbox.run_python_script(project_dir=tmp_path, script_relpath='run.py', script_args=args)
    assert not result.ok and 'list of strings' in result.stderr
    assert not (tmp_path/'.venv').exists()


def test_implementer_receives_active_spec_plan_runbook_and_original_idea(tmp_path):
    repo = tmp_path
    (repo/'agents').symlink_to(Path(__file__).resolve().parents[2]/'agents')
    project = repo/'projects/PROJ-901-context'
    feature = project/'specs/002-current'
    feature.mkdir(parents=True)
    docs = {'spec.md':'FR-001: p=5,7,11 and N=1000,10000,100000,1000000.',
        'plan.md':'Reuse code/src/utils/sieve.py; do not replace the validated routine.',
        'quickstart.md':'python code/run.py --max-n 1000 --prime 5'}
    for name, content in docs.items():
        (feature/name).write_text(content)
    (project/'idea').mkdir()
    (project/'idea/question.md').write_text('Report finite observations without claiming a new theorem.')
    logs = project/'code/.tasks'
    logs.mkdir(parents=True)
    (logs/'T001.code_run.py.log').write_text('Arguments: []\nerror: required arguments --max-n, --prime')
    (logs/'T002.other.py.log').write_text('Unrelated old execution failure')
    prompt = ImplementerAgent().build_prompt(SimpleNamespace(project_dir=project,project_id=project.name),
        {'feature_dir':str(feature),'tasks_text':'- [ ] T001 Connect the CLI',
         'next_task_id':'T001','next_task_line':'T001 Connect the CLI',
         'completed_task_ids':[]})[-1].content
    for content in docs.values():
        assert content in prompt
    assert 'without claiming a new theorem' in prompt

    assert 'error: required arguments --max-n, --prime' in prompt
    assert 'Unrelated old execution failure' not in prompt


@pytest.mark.parametrize('value', [True, None, {'unexpected': 5}, float('nan')])
def test_numeric_normalization_does_not_coerce_other_yaml_values(tmp_path, value):
    project = tmp_path/'projects/PROJ-901-invalid-argv'
    feature = project/'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature/'tasks.md'
    tasks.write_text('- [ ] T001 Run the CLI\n')
    document = {'task_id': 'T001', 'verdict': 'completed', 'artifacts': [
        {'path': 'code/run.py', 'contents': CLI, 'execute': True,
         'args': ['--max-n', '1000', '--prime', value]}]}
    ImplementerAgent().write_artifacts(SimpleNamespace(project_dir=project),
        {'tasks_path': str(tasks), 'feature_dir': str(feature),
         'next_task_id': 'T001', 'all_complete': False},
        ChatResponse(text=yaml.safe_dump(document), model='test', backend='dartmouth'))
    assert not (project/'result.json').exists()
    assert not (project/'.venv').exists()
    assert 'list of strings' in (project/'code/.tasks/T001.code_run.py.log').read_text()
