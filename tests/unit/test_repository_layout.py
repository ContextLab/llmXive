"""Exercise layout enforcement against a real Git index, including sparse paths."""
import subprocess

from llmxive.checks.repository_layout import unexpected_tracked_paths


def test_layout_rejects_downloads_and_unknown_roots_but_preserves_project_data(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    paths = ['README.md', 'projects/PROJ-1/data/article.pdf', 'docs/index.html',
             'article.pdf', 'beir_data/data.json', 'projects-copy/file.csv',
             'data with spaces/a\nfile.csv', 'projects/data/raw/leak.csv',
             'projects/state/checksums.json', 'specs/auto-revisions/PROJ-1/round-1/tasks.md']
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('evidence')
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True)
    # A dirty/untracked personal file is not silently deleted or treated as a
    # tracked leak by this audit. Cron's write guard checks untracked files too.
    (tmp_path / 'personal.txt').write_text('untouched')
    # Sparse files still exist in the index and must not evade the CI guard.
    subprocess.run(['git', 'update-index', '--skip-worktree', 'article.pdf'], cwd=tmp_path, check=True)
    (tmp_path / 'article.pdf').unlink()
    assert unexpected_tracked_paths(tmp_path) == sorted([
        'article.pdf', 'beir_data/data.json', 'projects-copy/file.csv',
        'data with spaces/a\nfile.csv', 'projects/data/raw/leak.csv',
        'projects/state/checksums.json', 'specs/auto-revisions/PROJ-1/round-1/tasks.md',
    ])
    assert (tmp_path / 'personal.txt').read_text() == 'untouched'


def test_pipeline_write_guard_rejects_wrong_project_namespace_and_hygiene_reports_it(tmp_path):
    from llmxive.agents.repository_hygiene import _check_leftover_artifacts
    from llmxive.checks.pipeline_writes import unexpected_writes

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "README.md").write_text("platform")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=t@example.invalid",
                    "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    for name in ["projects/data/raw/leak.csv", "projects/PROJ-1/data/real.csv"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence")
    assert unexpected_writes(tmp_path) == ["projects/data/raw/leak.csv"]
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    assert unexpected_writes(tmp_path) == ["projects/data/raw/leak.csv"]
    flags = _check_leftover_artifacts(tmp_path)
    assert len(flags) == 1 and flags[0].kind == "misplaced_tracked_artifacts"
    assert "projects/data/raw/leak.csv" in flags[0].summary


def test_hygiene_narrative_cannot_call_flagged_layout_clean(tmp_path, monkeypatch):
    import json

    import yaml

    from llmxive.agents import repository_hygiene
    from llmxive.agents.base import AgentContext
    from llmxive.backends.base import ChatResponse

    monkeypatch.setattr(repository_hygiene, "_repo_root", lambda: tmp_path)
    ctx = AgentContext("", "test-hygiene", "", [], metadata={
        "_flags_json": json.dumps([{"kind": "misplaced_tracked_artifacts"}]),
        "_loc_metric_json": "{}",
    })
    repository_hygiene.RepositoryHygieneAgent({}).handle_response(
        ctx, ChatResponse(text="verdict: clean", model="test", backend="test"),
    )
    report = yaml.safe_load((tmp_path / "state/run-log/hygiene/test-hygiene.yaml").read_text())
    assert report["verdict"] == "flagged"
    assert report["flags"] == [{"kind": "misplaced_tracked_artifacts"}]


def test_recovery_verifier_checks_real_git_bytes_modes_and_removed_source(tmp_path):
    import json
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / 'scripts/verify_root_file_recovery.py'
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    source = tmp_path / 'article.pdf'
    source.write_bytes(b'preserved evidence\x00\xff')
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=t@example.invalid',
                    'commit', '-qm', 'before'], cwd=tmp_path, check=True)
    before = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tmp_path).decode().strip()
    blob = subprocess.check_output(['git', 'hash-object', 'article.pdf'], cwd=tmp_path).decode().strip()
    destination = 'state/recovered-downloads/one/article.pdf'
    archived = tmp_path / destination
    archived.parent.mkdir(parents=True)
    source.rename(archived)
    manifest = tmp_path / 'notes/audit-20261008/root-file-recovery.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'snapshot_commit': before, 'groups': [{'files': [{
        'source': 'article.pdf', 'destination': destination, 'mode': '100644',
        'git_blob': blob, 'bytes': archived.stat().st_size,
    }]}]}))
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, check=True)

    def verify():
        return subprocess.run([sys.executable, str(script), '--check-original'],
                              cwd=tmp_path, capture_output=True, text=True)

    assert verify().returncode == 0
    archived.write_bytes(b'changed')
    subprocess.run(['git', 'add', destination], cwd=tmp_path, check=True)
    assert 'recovered bytes/mode differ' in verify().stdout
    archived.write_bytes(b'preserved evidence\x00\xff')
    subprocess.run(['git', 'add', destination], cwd=tmp_path, check=True)
    subprocess.run(['git', 'update-index', '--chmod=+x', destination], cwd=tmp_path, check=True)
    assert 'recovered bytes/mode differ' in verify().stdout
    subprocess.run(['git', 'update-index', '--chmod=-x', destination], cwd=tmp_path, check=True)
    source.write_bytes(archived.read_bytes())
    subprocess.run(['git', 'add', 'article.pdf'], cwd=tmp_path, check=True)
    assert 'original misplaced path still tracked' in verify().stdout
