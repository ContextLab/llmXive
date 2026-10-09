"""Research shell wrappers must run and failures must gate acceptance."""
import json
import time
from types import SimpleNamespace

import pytest
import yaml

from llmxive import sandbox
from llmxive.backends.base import ChatResponse
from llmxive.execution.analysis_runner import extract_run_commands, run_analysis
from llmxive.speckit.implement_cmd import ImplementerAgent

SCRIPT = '''#!/usr/bin/env bash
set -eu
python - "$@" <<'CODE'
import json, os, sys
from pathlib import Path
assert 'DARTMOUTH_CHAT_API_KEY' not in os.environ
assert 'GH_TOKEN' not in os.environ
assert sys.prefix == os.environ['VIRTUAL_ENV']
Path('data').mkdir(exist_ok=True)
Path('data/results.json').write_text(json.dumps({'total':sum(range(100)), 'label':sys.argv[1:]}))
CODE
'''


def test_implementer_shell_artifact_runs_with_literal_argv_and_venv(tmp_path, monkeypatch):
    project = tmp_path/'projects/PROJ-shell'
    feature = project/'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature/'tasks.md'
    tasks.write_text('- [ ] T001 Run the complete study (scripts/run_full_analysis.sh)\n')
    monkeypatch.setenv('DARTMOUTH_CHAT_API_KEY', 'not-for-child')
    monkeypatch.setenv('GH_TOKEN', 'not-for-child')
    literal = 'a b; $(touch SHOULD_NOT_EXIST)'
    doc = {'verdict': 'completed', 'artifacts': [
        {'path': 'scripts/run_full_analysis.sh', 'contents': SCRIPT,
         'execute': True, 'args': [literal]}]}
    ImplementerAgent().write_artifacts(SimpleNamespace(project_dir=project),
        {'tasks_path':str(tasks),'feature_dir':str(feature),'next_task_id':'T001'},
        ChatResponse(text=yaml.safe_dump(doc),model='test',backend='dartmouth'))
    assert json.loads((project/'data/results.json').read_text()) == {'total':4950,'label':[literal]}
    assert not (project/'SHOULD_NOT_EXIST').exists()
    assert 'ok=True' in (project/'code/.tasks/T001.scripts_run_full_analysis.sh.log').read_text()


def test_runbook_shell_failure_is_not_silently_skipped_after_python_success(tmp_path):
    scripts = tmp_path/'scripts'
    scripts.mkdir()
    (scripts/'study.sh').write_text(SCRIPT)
    (scripts/'check.sh').write_text('exit 7\n')
    quickstart = tmp_path/'quickstart.md'
    quickstart.write_text('```bash\npython -c "print(1)"\nbash scripts/study.sh\nsh scripts/check.sh\n```\n')
    result = run_analysis(tmp_path, quickstart_path=quickstart)
    assert not result.ok
    assert [r.returncode for r in result.commands] == [0,0,7]
    assert result.artifacts_produced == ['data/results.json']
    assert not result.commands[-1].advisory


def test_shell_timeout_stops_python_child_before_late_write(tmp_path):
    sandbox.ensure_venv(tmp_path)
    script = tmp_path/'slow.sh'
    script.write_text("python -c \"import time; from pathlib import Path; time.sleep(1); Path('late').write_text('wrong')\"\n")
    result = sandbox.run_shell_script(project_dir=tmp_path,script_relpath='slow.sh',timeout_s=0.1)
    assert not result.ok and result.timed_out
    time.sleep(1.1)
    assert not (tmp_path/'late').exists()


@pytest.mark.parametrize('path', ['../escape.sh','missing.sh','-c'])
def test_shell_path_failure_never_creates_venv(tmp_path,path):
    result = sandbox.run_shell_script(project_dir=tmp_path,script_relpath=path)
    assert not result.ok and 'project-local' in result.stderr
    assert not (tmp_path/'code/.venv').exists()


def test_direct_script_runbook_and_shell_injection_are_literal(tmp_path):
    assert extract_run_commands('```sh\n./scripts/study.sh --n 10\n```') == ['bash ./scripts/study.sh --n 10']
    (tmp_path/'study.sh').write_text('printf "%s\\n" "$@"\n')
    result = sandbox.run_shell_script(project_dir=tmp_path,script_relpath='study.sh',
        script_args=[';','touch','INJECTED'])
    assert result.ok and result.stdout == ';\ntouch\nINJECTED\n'
    assert not (tmp_path/'INJECTED').exists()


def test_unsupported_execute_artifact_is_a_recorded_failure(tmp_path):
    project = tmp_path/'projects/PROJ-unsupported'
    feature = project/'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature/'tasks.md'
    tasks.write_text('- [ ] T001 Execute the analysis\n')
    doc = {'verdict':'completed','artifacts':[{'path':'study.R','contents':'print(1)','execute':True}]}
    ImplementerAgent().write_artifacts(SimpleNamespace(project_dir=project),
        {'tasks_path':str(tasks),'feature_dir':str(feature),'next_task_id':'T001'},
        ChatResponse(text=yaml.safe_dump(doc),model='test',backend='dartmouth'))
    assert 'FAILED-IN-EXECUTION' in tasks.read_text()
    assert 'requires a .py or .sh' in (project/'code/.tasks/T001.study.R.log').read_text()
