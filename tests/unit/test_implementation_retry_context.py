"""A retry needs the actual failed source and can execute it without rewriting."""
from types import SimpleNamespace

import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent
from tests.unit.test_implementer_feedback_injection import _project, _ctx, _MECH
from tests.unit.test_task_execution_gate import setup, write


def test_failure_source_reaches_prompt_when_task_only_names_output(tmp_path):
    project=_project(tmp_path)
    source=project/'code/verify_all.py'
    source.write_text("MANIFEST_PATH = 'state/projects/PROJ-old.yaml'\nprint(MANIFEST_PATH)\n")
    logs=project/'code/.tasks';logs.mkdir()
    (logs/'T010.code_verify_all.py.log').write_text(
        '# code/verify_all.py (exit 1)\nArguments: ["--check"]\nFileNotFoundError\n')
    prompt=ImplementerAgent().build_prompt(_ctx(project.parent.parent,project),
        {**_MECH,'next_task_line':'- [ ] T010 Verify data/results/ and document results'})
    assert source.read_text().strip() in prompt[-1].content
    assert 'OMIT `contents`' in prompt[0].content


def test_execute_existing_script_without_overwriting_clears_failure(tmp_path):
    project,tasks,mechanical=setup(tmp_path)
    write(project,mechanical,'test -f data/ready\n')
    assert 'FAILED-IN-EXECUTION' in tasks.read_text()
    script=project/'scripts/study.sh'
    before=script.read_bytes();mtime=script.stat().st_mtime_ns
    (project/'data').mkdir();(project/'data/ready').write_text('prerequisite now exists')
    ImplementerAgent().write_artifacts(SimpleNamespace(project_dir=project),mechanical,
        ChatResponse(text=yaml.safe_dump({'verdict':'completed','artifacts':[
            {'path':'scripts/study.sh','execute':True,'args':[]}]}),model='test',backend='dartmouth'))
    assert script.read_bytes()==before and script.stat().st_mtime_ns==mtime
    assert 'FAILED-IN-EXECUTION' not in tasks.read_text()
    assert 'exit 0' in (project/'code/.tasks/T001.scripts_study.sh.log').read_text()
