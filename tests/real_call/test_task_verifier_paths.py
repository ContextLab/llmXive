"""Real semantic checks for canonical artifact paths and substantive omissions."""

import os

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
    (project / 'code/main.py').write_text('print("analysis")\n')
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
        (feature / 'quickstart.md').write_text(
            'From the repository root, run:\n'
            f'```sh\npython projects/PROJ-1/code/main.py{suffix}\n```\n'
        )
    verdict = tv.verify_task(
        task_text=task,
        evidence=tv.gather_evidence(project, task),
        fallback_backends=(),
    )
    assert observed_models == [tv.DEFAULT_MODEL]
    assert verdict.complete is expected, verdict.reason
