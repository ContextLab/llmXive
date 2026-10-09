"""Real semantic checks for canonical artifact paths and substantive omissions."""

import os
import subprocess
import sys

import pytest

from llmxive.agents import task_verifier as tv

pytestmark = pytest.mark.skipif(
    os.environ.get('LLMXIVE_REAL_TESTS') != '1' or not os.environ.get('DARTMOUTH_CHAT_API_KEY'),
    reason='live Dartmouth task verification unavailable',
)


@pytest.mark.parametrize('case,expected', [
    ('canonical-command', True),
    pytest.param('repository-root-command', True, marks=pytest.mark.slow),
    pytest.param('code-directory-command', True, marks=pytest.mark.slow),
    ('missing-required-argument', False),
    ('wrong-project-prefix', False),
    pytest.param('missing-document', False, marks=pytest.mark.slow),
    ('empty-package-marker', True),
])
def test_task_verifier_respects_real_path_evidence(tmp_path, monkeypatch, case, expected):
    # Observe the real route; a fallback must not mask this primary-model check.
    real_chat = tv.chat_with_fallback
    observed_models = []

    def observed_chat(*args, **kwargs):
        response = real_chat(*args, **kwargs)
        observed_models.append(response.model)
        return response

    monkeypatch.setattr(tv, 'chat_with_fallback', observed_chat)
    project = tmp_path / 'projects/PROJ-1'
    feature = project / 'specs/001-current'
    feature.mkdir(parents=True)
    (feature / 'spec.md').write_text('Document the command with the required --limit 1000 argument.')
    (project / 'code').mkdir()
    (project / 'code/main.py').write_text(
        'import argparse\n\n'
        'parser = argparse.ArgumentParser()\n'
        'parser.add_argument("--limit", type=int, required=True)\n'
        'args = parser.parse_args()\n'
        'if not 1 <= args.limit <= 1000:\n'
        '    parser.error("--limit must be between 1 and 1000")\n'
        'print(sum(range(args.limit)))\n'
    )
    # Prove the documented command is executable before asking the model to
    # judge its documentation. Exercise all three supported working directories.
    cwd, script = project, 'code/main.py'
    if case == 'repository-root-command':
        cwd, script = tmp_path, 'projects/PROJ-1/code/main.py'
    elif case == 'code-directory-command':
        cwd, script = project / 'code', 'main.py'
    command = [sys.executable, script, '--limit', '1000']
    execution = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=10)
    assert execution.returncode == 0, execution.stderr
    assert execution.stdout == '499500\n'
    if case == 'missing-required-argument':
        omitted = subprocess.run(command[:-2], cwd=cwd, capture_output=True, text=True, timeout=10)
        assert omitted.returncode == 2
        assert '--limit' in omitted.stderr
    task = (
        'T001 Document the runnable command `python code/main.py --limit 1000` '
        'in specs/001-invented/quickstart.md. This task is documentation only.'
    )
    if case == 'repository-root-command':
        task = ('T001 Document `python projects/PROJ-1/code/main.py --limit 1000` '
                'from the repository root in specs/001-invented/quickstart.md. '
                'This task is documentation only.')
    elif case == 'code-directory-command':
        task = ('T001 Document `cd projects/PROJ-1/code && python main.py --limit 1000` '
                'from the repository root in specs/001-invented/quickstart.md. '
                'This task is documentation only.')
    if case == 'empty-package-marker':
        (project / 'code/__init__.py').touch()
        task = 'T001 Create an intentionally empty code/__init__.py Python package marker.'
    elif case != 'missing-document':
        suffix = '' if case == 'missing-required-argument' else ' --limit 1000'
        documented_project = 'PROJ-2' if case == 'wrong-project-prefix' else 'PROJ-1'
        if case == 'wrong-project-prefix':
            assert not (tmp_path / 'projects/PROJ-2/code/main.py').exists()
        (feature / 'quickstart.md').write_text(
            'From the repository root, run:\n'
            f'```sh\npython projects/{documented_project}/code/main.py{suffix}\n```\n'
        )
    verdict = tv.verify_task(
        task_text=task,
        evidence=tv.gather_evidence(project, task),
        fallback_backends=(),
    )
    assert observed_models == [tv.DEFAULT_MODEL]
    assert verdict.complete is expected, verdict.reason


@pytest.mark.parametrize('correct_dependency', [True, False])
def test_task_verifier_checks_local_import_with_actual_execution(tmp_path, monkeypatch, correct_dependency):
    """An existing indirect module is evidence; a failing test stays incomplete."""
    project = tmp_path / 'projects/PROJ-1'
    (project / 'code/.tasks').mkdir(parents=True)
    (project / 'tests').mkdir()
    (project / 'tests/test_analysis.py').write_text(
        'def test_analyze():\n'
        '    from analysis import analyze\n'
        '    assert analyze(10) == 40\n'
    )
    factor = 4 if correct_dependency else 3
    (project / 'code/analysis.py').write_text(f'def analyze(n):\n    return n * {factor}\n')
    env = {**os.environ, 'PYTHONPATH': str(project / 'code'), 'PYTHONDONTWRITEBYTECODE': '1'}
    execution = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests/test_analysis.py'],
        cwd=project, env=env, capture_output=True, text=True, timeout=20,
    )
    assert execution.returncode == (0 if correct_dependency else 1)
    (project / 'code/.tasks/T001.tests_test_analysis.py.log').write_text(
        f'# tests/test_analysis.py (exit {execution.returncode}, actual pytest subprocess)\n'
        + execution.stdout + execution.stderr
    )
    task = 'T001 Create tests/test_analysis.py verifying analyze(10) equals 40. The test must pass.'
    evidence = tv.gather_evidence(project, task)
    assert 'Local import candidate `code/analysis.py`' in evidence
    real_chat = tv.chat_with_fallback
    observed = []
    def observe(*args, **kwargs):
        response = real_chat(*args, **kwargs)
        observed.append(response.model)
        return response
    monkeypatch.setattr(tv, 'chat_with_fallback', observe)
    verdict = tv.verify_task(task_text=task, evidence=evidence, fallback_backends=())
    assert observed == [tv.DEFAULT_MODEL]
    assert verdict.complete is correct_dependency, verdict.reason
