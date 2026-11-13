"""Which script last wrote each of a project's output files.

Two scripts that each write the whole of one file erase each other's work
whenever the earlier one is run again. Canary 12 (2026-10-11): a methods
document with its citation was regenerated as a bare table by a later rerun of
the analysis driver, the task that wrote the methods was rejected three times
for "no citation", and nothing shown to either model said where the text went.

The implementer's execution loop takes a :func:`snapshot` before and after each
run and passes the difference to :func:`record`, which keeps the latest writer
of every file in ``<task log dir>/output-writers.json`` and reports the files a
run took over from a different script. The report goes into that run's log,
which both the implementer and the task verifier read.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

REGISTRY_NAME = "output-writers.json"
#: Directories whose contents are never a script's research output.
_SKIPPED_ANYWHERE = {".venv", ".git", "__pycache__", ".tasks", ".pytest_cache", ".specify", ".ipynb_checkpoints"}
#: How many ordinary (not taken-over) files one log section names.
_MAX_LISTED = 40
#: Planning documents, written by the pipeline's own stages.
_SKIPPED_AT_ROOT = {"specs", "idea"}


def snapshot(project_root: Path) -> dict[str, tuple[int, int]]:
    """``{relative path: (size, mtime_ns)}`` for every candidate output file."""
    seen: dict[str, tuple[int, int]] = {}
    for current, dirs, files in os.walk(project_root):
        at_root = Path(current) == project_root
        dirs[:] = [d for d in dirs if d not in _SKIPPED_ANYWHERE and not (at_root and d in _SKIPPED_AT_ROOT)]
        for name in files:
            path = Path(current) / name
            try:
                stat = path.lstat()
            except OSError:
                continue
            seen[path.relative_to(project_root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return seen


def changed(before: dict[str, tuple[int, int]], after: dict[str, tuple[int, int]]) -> list[str]:
    """Files created or modified between two snapshots, sorted."""
    return sorted(rel for rel, state in after.items() if before.get(rel) != state)


def record(
    log_dir: Path, script: str, task_id: str, files: list[str], *, owns: bool = True,
) -> dict[str, tuple[str, str]]:
    """Make ``script`` the writer of ``files``; return the ones it took over.

    The result maps each file whose previous writer was a DIFFERENT script to
    that ``(script, task id)``. A script rewriting its own output, and the run
    script's own source file, are not takeovers.

    ``owns=False`` is a test run: a test that executes the script it checks
    makes the script rewrite its own output. The script stays the recorded
    writer and nothing is reported as taken over.
    """
    if not owns:
        return {}
    registry = log_dir / REGISTRY_NAME
    try:
        writers = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        writers = {}
    if not isinstance(writers, dict):
        writers = {}
    taken: dict[str, tuple[str, str]] = {}
    for rel in files:
        if rel == script:
            continue
        previous = writers.get(rel)
        if isinstance(previous, dict) and previous.get("script") not in (None, script):
            taken[rel] = (str(previous["script"]), str(previous.get("task", "")))
        writers[rel] = {"script": script, "task": task_id}
    if files:
        log_dir.mkdir(parents=True, exist_ok=True)
        registry.write_text(json.dumps(writers, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return taken


def last_writer(project_root: Path, rel: str, log_dir: str = "code/.tasks") -> tuple[str, str] | None:
    """``(script, task id)`` of the run that last wrote ``rel``, if one is recorded."""
    try:
        entry = json.loads((project_root / log_dir / REGISTRY_NAME).read_text(encoding="utf-8")).get(rel)
    except (OSError, ValueError, AttributeError):
        return None
    if not isinstance(entry, dict) or not entry.get("script"):
        return None
    return str(entry["script"]), str(entry.get("task", ""))


def log_section(script: str, files: list[str], taken: dict[str, tuple[str, str]]) -> str:
    """The ``## files written by this run`` section of an execution log."""
    lines = []
    plain = 0
    for rel in files:
        if rel == script:
            continue
        if rel not in taken:
            # A run that writes thousands of files must not crowd the log out
            # of what its readers are shown; every takeover is always listed.
            plain += 1
            if plain > _MAX_LISTED:
                continue
        if rel in taken:
            other, task = taken[rel]
            lines.append(f"- `{rel}` — replaces the version written by `{other}`"
                         + (f" ({task})" if task else "")
                         + ". Whatever only that script put in the file is gone; "
                           "one script should write the whole file.")
        else:
            lines.append(f"- `{rel}`")
    if plain > _MAX_LISTED:
        lines.append(f"- ... and {plain - _MAX_LISTED} more")
    return "## files written by this run\n\n" + ("\n".join(lines) if lines else "(none)") + "\n"


def put_back_section(files: list[str]) -> str:
    """The files a test session changed, which the platform put back when it ended."""
    if not files:
        return ""
    return ("\n## files this test session changed (put back as they were when it ended)\n\n"
            + "\n".join(f"- `{rel}`" for rel in sorted(files)) + "\n\n"
            "A test's output is its pytest session. Write test files under pytest's `tmp_path`.\n")


__all__ = ["REGISTRY_NAME", "changed", "last_writer", "log_section", "put_back_section", "record", "snapshot"]
