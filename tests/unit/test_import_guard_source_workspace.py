"""Root source/test artifacts must not be rejected against legacy code stubs."""
from types import SimpleNamespace

from llmxive import sandbox
from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent, _find_bad_sibling_imports


def test_root_test_written_against_real_root_api_not_deprecated_code_stub(tmp_path):
    project = tmp_path / 'projects/PROJ-901-layout'
    feature = project / 'specs/001-study'
    feature.mkdir(parents=True)
    tasks = feature / 'tasks.md'
    tasks.write_text('- [ ] T004 Write tests/test_plot_verification.py\n')
    for rel in ('src', 'code/src'):
        package = project / rel
        package.mkdir(parents=True)
        (package / '__init__.py').write_text('')
    (project / 'src/plot_tv.py').write_text('def make_plot():\n    return 42\n')
    stub = project / 'code/src/plot_tv.py'
    stub.write_text('"""Deprecated stub."""\n')
    response = ChatResponse(text='''task_id: T004
verdict: completed
artifacts:
  - path: tests/test_plot_verification.py
    contents: |
      from src.plot_tv import make_plot
      def test_plot():
          assert make_plot() == 42
      if __name__ == "__main__":
          test_plot()
          print(make_plot())
''', model='test', backend='dartmouth')
    written = ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project),
        {'tasks_path':str(tasks), 'feature_dir':str(feature),
         'next_task_id':'T004', 'all_complete':False}, response)
    assert (project / 'tests/test_plot_verification.py').is_file()
    assert any(path.endswith('tests/test_plot_verification.py') for path in written)
    # The accepted test is a script in a normal non-package tests directory.
    assert not (project / 'tests/__init__.py').exists()
    result = sandbox.run_python_script(
        project_dir=project, script_relpath='tests/test_plot_verification.py', timeout_s=120)
    assert result.ok, result.stderr
    assert result.stdout.strip() == '42'
    assert stub.read_text() == '"""Deprecated stub."""\n'
    # A name absent from the selected real module still fails the guard.
    assert _find_bad_sibling_imports(
        'from src.plot_tv import invented', project/'code', project/'tests/check.py')
    # A code workspace artifact still resolves its own code/src package.
    assert _find_bad_sibling_imports(
        'from src.plot_tv import make_plot', project/'code', project/'code/src/cli.py')
