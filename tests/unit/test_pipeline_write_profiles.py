"""Real Git repositories and a local bare remote exercise cron profile boundaries."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from llmxive.checks.pipeline_writes import unexpected_writes

ROOT = Path(__file__).resolve().parents[2]


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.STDOUT).decode().strip()


@pytest.fixture
def repository(tmp_path):
    repo = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    repo.mkdir()
    git(repo, 'init', '-b', 'main')
    git(repo, 'config', 'user.name', 'Test')
    git(repo, 'config', 'user.email', 'test@example.invalid')
    for name in ['scripts/ci/commit-and-push.sh', 'src/llmxive/checks/pipeline_writes.py',
                 'src/llmxive/checks/repository_layout.py']:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    for name in ['README.md', 'docs/old.txt', 'projects/PROJ-1/data/input.csv', 'state/status.json']:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('original')
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'initial')
    git(repo, 'init', '--bare', str(remote))
    git(repo, 'remote', 'add', 'origin', str(remote))
    git(repo, 'push', '-u', 'origin', 'main')
    return repo, remote


def run_helper(repo, *profile):
    env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH'],
               PRE_COMMIT_ALLOW_NO_CONFIG='1', COMMIT_PUSH_ATTEMPTS='1', RUNNER_TEMP=str(repo.parent))
    return subprocess.run(['bash', 'scripts/ci/commit-and-push.sh', 'test output', *profile],
                          cwd=repo, env=env, text=True, capture_output=True, timeout=30)


def test_pages_profile_pushes_only_real_docs_changes_and_default_refuses_them(repository):
    repo, remote = repository
    before = git(repo, 'rev-parse', 'HEAD')
    (repo / 'docs/old.txt').unlink()
    (repo / 'docs/index.html').write_text('<p>new site</p>')
    denied = run_helper(repo)
    assert denied.returncode != 0 and 'docs/' in denied.stdout
    assert git(repo, 'diff', '--cached', '--name-only') == ''
    assert git(repo, 'rev-parse', 'HEAD') == before
    accepted = run_helper(repo, 'pages')
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert 'verified' in accepted.stdout
    assert git(repo, 'diff', '--name-only', before, 'HEAD').splitlines() == ['docs/index.html', 'docs/old.txt']
    assert git(remote, 'rev-parse', 'main') == git(repo, 'rev-parse', 'HEAD')
    assert git(remote, 'show', 'main:docs/index.html') == '<p>new site</p>'
    assert git(remote, 'show', 'main:README.md') == 'original'


@pytest.mark.parametrize('forbidden', ['README.md', 'projects/PROJ-1/data/input.csv', 'state/status.json'])
def test_pages_profile_refuses_mixed_writes_without_staging_or_pushing(repository, forbidden):
    repo, remote = repository
    before = git(remote, 'rev-parse', 'main')
    (repo / 'docs/index.html').write_text('site')
    (repo / forbidden).write_text('unauthorized change')
    denied = run_helper(repo, 'pages')
    assert denied.returncode != 0 and forbidden in denied.stdout
    assert git(repo, 'diff', '--cached', '--name-only') == ''
    assert git(remote, 'rev-parse', 'main') == before
    assert (repo / forbidden).read_text() == 'unauthorized change'  # retained for diagnosis


@pytest.mark.parametrize('profile', ['research', 'pages'])
def test_guard_sees_protected_source_of_cross_boundary_rename(repository, profile):
    repo, _ = repository
    target = 'docs/README.md' if profile == 'pages' else 'projects/PROJ-1/README.md'
    git(repo, 'mv', 'README.md', target)
    assert unexpected_writes(repo, profile=profile) == ['README.md']


@pytest.mark.parametrize('profile', ['research', 'pages'])
def test_worktree_restore_cannot_hide_unsafe_staged_change(repository, profile):
    repo, _ = repository
    (repo / 'README.md').write_text('staged unauthorized')
    git(repo, 'add', 'README.md')
    (repo / 'README.md').write_text('original')
    assert git(repo, 'diff', 'HEAD', '--name-only') == ''  # old guard missed this
    assert unexpected_writes(repo, profile=profile) == ['README.md']


def test_unknown_profile_fails_before_staging_and_deleted_docs_root_is_staged(repository):
    repo, remote = repository
    before = git(remote, 'rev-parse', 'main')
    shutil.rmtree(repo / 'docs')
    denied = run_helper(repo, '../../')
    assert denied.returncode != 0 and 'invalid choice' in denied.stderr
    assert git(repo, 'diff', '--cached', '--name-only') == ''
    assert git(remote, 'rev-parse', 'main') == before
    accepted = run_helper(repo, 'pages')
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert git(remote, 'ls-tree', '--name-only', 'main', 'docs') == ''


def test_default_profile_pushes_project_state_and_dashboard_outputs(repository):
    repo, remote = repository
    paths = ['projects/PROJ-1/.specify/revisions/round-1/tasks.md',
             'state/status.json', 'web/data/projects.json']
    before = git(repo, 'rev-parse', 'HEAD')
    for name in paths:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('new output')
    result = run_helper(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert git(repo, 'diff', '--name-only', before, 'HEAD').splitlines() == sorted(paths)
    for name in paths:
        assert git(remote, 'show', 'main:' + name) == 'new output'
    assert git(remote, 'show', 'main:README.md') == 'original'
    assert git(remote, 'show', 'main:docs/old.txt') == 'original'


@pytest.mark.parametrize('profile,path', [('research', 'state/status.json'), ('pages', 'docs/old.txt')])
@pytest.mark.parametrize('conflict', [False, True])
def test_shallow_tick_rebases_disjoint_updates_and_preserves_conflicts(repository, tmp_path, profile, path, conflict):
    repo, remote = repository
    # Use file://: local-path clones ignore --depth and would not test CI's case.
    shallow = tmp_path / 'shallow'
    git(tmp_path, 'clone', '--depth=1', '--branch=main', remote.as_uri(), str(shallow))
    assert git(shallow, 'rev-parse', '--is-shallow-repository') == 'true'
    other = path if conflict else 'projects/PROJ-1/data/input.csv'
    (repo / other).write_text('newer peer result')
    git(repo, 'add', other)
    git(repo, 'commit', '-m', 'peer progress')
    git(repo, 'push', 'origin', 'main')
    peer_head = git(remote, 'rev-parse', 'main')
    (shallow / path).write_text('this tick result')
    result = run_helper(shallow, profile)
    if conflict:
        assert result.returncode != 0
        assert 'refusing to overwrite newer work' in result.stderr
        assert git(remote, 'rev-parse', 'main') == peer_head
        assert git(remote, 'show', 'main:' + path) == 'newer peer result'
        assert '+this tick result' in (tmp_path / 'llmxive-unpushed.patch').read_text()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert 'verified' in result.stdout
        assert git(remote, 'show', 'main:' + other) == 'newer peer result'
        assert git(remote, 'show', 'main:' + path) == 'this tick result'
        git(remote, 'merge-base', '--is-ancestor', peer_head, 'main')
