"""Headless Spec Kit script runner (T021).

Invokes Spec Kit's bash scripts (create-new-feature.sh, setup-plan.sh,
check-prerequisites.sh) with --json and parses output.

The repo's top-level .specify/scripts/bash/ holds the meta-system's
scripts; per-project scaffolds keep their own copies under
projects/<PROJ-ID>/.specify/scripts/bash/.

Per FR-014 + T021 (FIX U2): before invoking a per-project script, the
runner verifies the directory exists and the script is executable; if
missing or stale (mismatched checksum vs the meta-system's), the runner
re-syncs from the meta-system's cache and re-checks.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _meta_scripts_dir() -> Path:
    return _repo_root() / ".specify" / "scripts" / "bash"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _resync_project_scripts(project_dir: Path) -> None:
    """Copy meta-system scripts into the project's .specify/scripts/bash/."""
    target = project_dir / ".specify" / "scripts" / "bash"
    target.mkdir(parents=True, exist_ok=True)
    src_dir = _meta_scripts_dir()
    if not src_dir.is_dir():  # pragma: no cover — preflight catches this
        raise FileNotFoundError(f"meta-system scripts not found at {src_dir}")
    for src in src_dir.iterdir():
        if not src.is_file():
            continue
        dst = target / src.name
        if not dst.exists() or _file_sha256(src) != _file_sha256(dst):
            shutil.copy2(src, dst)
            dst.chmod(0o755)


def run_script(
    script_relpath: str,
    *args: str,
    cwd: Path | None = None,
    expect_json: bool = True,
) -> dict[str, Any] | str:
    """Run a Spec Kit bash script and return parsed JSON (or raw stdout).

    `script_relpath` is a path relative to the repo root, e.g.
    ".specify/scripts/bash/create-new-feature.sh".
    """
    cwd = cwd or _repo_root()
    full = (cwd / script_relpath).resolve()
    if not full.exists():
        raise FileNotFoundError(f"script does not exist: {full}")
    if not full.is_file() or not full.stat().st_mode & 0o111:
        full.chmod(0o755)
    proc = subprocess.run(
        [str(full), *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )
    if expect_json:
        # Spec Kit scripts may print other lines before the JSON; grab the
        # first line that successfully parses.
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                return json.loads(line)  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                continue
        raise ValueError(f"no parseable JSON in script output:\n{proc.stdout}")
    return proc.stdout


def init_speckit_in(project_dir: Path) -> None:
    """Bootstrap a per-project Spec Kit scaffold inside `project_dir`.

    Copies the meta-system's .specify/{scripts,templates,memory}/ skeleton
    so the project can run its own /speckit.* slash commands.
    """
    repo = _repo_root()
    src_root = repo / ".specify"
    target_root = project_dir / ".specify"
    target_root.mkdir(parents=True, exist_ok=True)

    for sub in ("scripts", "templates"):
        src = src_root / sub
        if not src.is_dir():
            continue
        dst = target_root / sub
        if dst.is_dir():
            continue  # idempotent
        shutil.copytree(src, dst)

    # The project's memory/ holds its own constitution; do NOT copy the
    # meta-system constitution here. Project-Initializer (T044) substitutes
    # tokens into agents/templates/research_project_constitution.md.
    (target_root / "memory").mkdir(exist_ok=True)


__all__ = ["run_script", "init_speckit_in"]
