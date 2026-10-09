"""Audit the tracked repository layout, including paths absent in sparse checkouts.

This guards additions in ordinary PRs; pipeline_writes separately restricts cron
mutations. Downloaded research files belong inside projects/<id>/, never beside
README.md. This is a Git layout check, not an OS execution sandbox.
"""

import subprocess
from pathlib import Path, PurePosixPath

ROOT_FILES = frozenset({
    '.env.example', '.gitignore', '.gitmodules', 'CLAUDE.md', 'LICENSE',
    'README.md', 'mypy.ini', 'pyproject.toml', 'ruff.toml',
})
ROOT_DIRECTORIES = frozenset({
    '.claude', '.llmxive-system', '.llmxive', '.omc', '.specify', '.github',
    'agents', 'docs', 'eval', 'infra', 'notes', 'papers', 'projects',
    'scripts', 'specs', 'src', 'state', 'tests', 'web',
})


def is_project_path(path: str) -> bool:
    """Require a concrete project namespace, not projects/data or projects/state."""
    parts = PurePosixPath(path).parts
    return len(parts) >= 3 and parts[0] == "projects" and parts[1].startswith("PROJ-")


def unexpected_tracked_paths(repo: Path) -> list[str]:
    """Return misplaced index paths without reading or altering file contents."""
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=repo).decode().split('\0')
    bad = []
    for path in filter(None, paths):
        parts = PurePosixPath(path).parts
        if len(parts) == 1:
            allowed = path in ROOT_FILES
        else:
            allowed = parts[0] in ROOT_DIRECTORIES
            if parts[0] == "projects":
                allowed = is_project_path(path)
        if not allowed:
            bad.append(path)
    return sorted(set(bad))


def main() -> int:
    bad = unexpected_tracked_paths(Path.cwd())
    if bad:
        print('Misplaced tracked files; project artifacts belong in projects/<id>/:')
        print('\n'.join(bad))
        return 1
    print('Repository layout OK: tracked files use documented platform/project roots.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
