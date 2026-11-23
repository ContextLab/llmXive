"""Real independent decisions, authenticated reuse, and rejected cache tampering."""

import os
import secrets
import subprocess
import sys

import pytest
import yaml

from llmxive.agents import _task_verdict_receipt as auth
from llmxive.agents import task_verifier as tv

pytestmark = pytest.mark.skipif(
    os.environ.get('LLMXIVE_REAL_TESTS') != '1' or not os.environ.get('DARTMOUTH_CHAT_API_KEY'),
    reason='live Dartmouth task verification unavailable',
)


def test_real_task_verdict_reuse_rejects_unsigned_and_mutated_acceptance(tmp_path, monkeypatch):
    # The only substituted dependency is an ephemeral signing key. Decisions
    # below come from the real primary model, observed without rewriting them.
    signing_key = secrets.token_bytes(32)
    monkeypatch.setattr(auth, 'load_signing_key', lambda: signing_key)
    project = tmp_path / 'projects/PROJ-991-authentication'
    feature = project / 'specs/001-squares'
    feature.mkdir(parents=True)
    memory = project / '.specify/memory'
    (project / 'code/.tasks').mkdir(parents=True)
    (project / 'data').mkdir()
    script = project / 'code/calculate.py'
    script.write_text(
        'from pathlib import Path\n'
        'rows = "n,square\\n" + "".join(f"{n},{n*n}\\n" for n in range(1, 4))\n'
        'Path("data/results.csv").write_text(rows)\n'
        'print("computed squares for 1, 2, 3")\n'
    )
    execution = subprocess.run(
        [sys.executable, '-B', 'code/calculate.py'], cwd=project,
        env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True, text=True, timeout=10,
    )
    assert execution.returncode == 0, execution.stderr
    results = project / 'data/results.csv'
    assert results.read_text() == 'n,square\n1,1\n2,4\n3,9\n'
    (project / 'code/.tasks/T001.code_calculate.py.log').write_text(
        '# code/calculate.py (exit 0, actual Python subprocess)\n' + execution.stdout
    )
    task = ('T001 Implement code/calculate.py to compute squares for integers 1 through 3 '
            'and write data/results.csv with header n,square and exactly rows 1,1; 2,4; 3,9. '
            'The script must run successfully and the current CSV must contain these exact values.')
    tasks = feature / 'tasks.md'
    tasks.write_text(f'- [X] {task}\n')
    spec = 'Compute n*n for n=1,2,3. The current CSV must hold 1,4,9, not placeholders or other values.'
    (feature / 'spec.md').write_text(spec)
    real_chat = tv.chat_with_fallback
    observed_models = []

    def observe(*args, **kwargs):
        response = real_chat(*args, **kwargs)
        observed_models.append(response.model)
        return response

    monkeypatch.setattr(tv, 'chat_with_fallback', observe)

    def run():
        return tv.run_verification_pass(
            project, tasks, already_verified=set(), spec_context=spec,
            model=tv.DEFAULT_MODEL, fallback_backends=(),
            notes_path=memory / 'notes.md', state_path=memory / 'task_verify.yaml',
        )

    # A genuine live decision is persisted, authenticated and actually reused.
    assert run()['accepted'] == 1
    cache_path = memory / 'task_verify_cache.yaml'
    receipt = yaml.safe_load(cache_path.read_text())['T001']
    assert receipt['c'] is True and receipt['sig']
    assert auth.authentic_verdict(project, tasks, 'T001', receipt)
    assert tv.verified_done_keys(project, tasks) == {'T001'}
    assert run()['accepted'] == 1
    assert observed_models == [tv.DEFAULT_MODEL]

    # Publicly recomputing the correct evidence hash cannot manufacture approval
    # for a now-wrong output. The old run log is historical, not current proof.
    results.write_text('n,square\n1,1\n2,4\n3,999\n')
    digest = tv._verification_hash(task, spec, tv.gather_evidence(project, task), model=tv.DEFAULT_MODEL)
    unsigned = {'h': digest, 'c': True, 'r': 'fabricated acceptance'}
    cache_path.write_text(yaml.safe_dump({'T001': unsigned}))
    assert tv.verified_done_keys(project, tasks) == set()
    rejected = run()
    assert rejected['accepted'] == 0 and rejected['rejected'], rejected
    assert '- [ ] T001' in tasks.read_text()
    assert observed_models == [tv.DEFAULT_MODEL] * 2

    # Mutating the actual signed rejection to acceptance must trigger another
    # independent call even though task, evidence hash and signature are present.
    rejection = yaml.safe_load(cache_path.read_text())['T001']
    assert rejection['c'] is False
    assert auth.authentic_verdict(project, tasks, 'T001', rejection)
    rejection['c'] = True
    cache_path.write_text(yaml.safe_dump({'T001': rejection}))
    tasks.write_text(f'- [X] {task}\n')  # an untrusted producer claims completion again
    assert tv.verified_done_keys(project, tasks) == set()
    rejected_again = run()
    assert rejected_again['accepted'] == 0 and rejected_again['rejected'], rejected_again
    assert '- [ ] T001' in tasks.read_text()
    assert observed_models == [tv.DEFAULT_MODEL] * 3
    final_receipt = yaml.safe_load(cache_path.read_text())['T001']
    assert final_receipt['c'] is False
    assert auth.authentic_verdict(project, tasks, 'T001', final_receipt)
