"""An implementer attempt that breaks a passing test is not kept.

The project's tests are run before the attempt and again after it, in the same
process and environment. If a test that passed before now fails, or a test
module the attempt rewrote has fewer passing tests than it had, every file is
put back as it was, the task is marked as a failed execution naming the test
module, and the attempt's own record says which tests broke. The next attempt
starts from the state that passed.

What this does not do: it does not require an attempt to improve anything.
Batch 1 of the 2026-10-11 reliability runs: 25 of the 39 retries that the
verifier went on to accept changed no executed check, and none of the 13 that
made a passing check fail was accepted.

Only the research track is covered; a paper task's attempt is left alone.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from llmxive.project_files import is_pytest_module
from llmxive.speckit import scorecard

LOGGER = logging.getLogger(__name__)

RESEARCH_LOG_DIR = "code/.tasks"
#: Never copied and never restored: environments and caches the harness owns.
_SKIPPED = {".venv", ".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".runtime-home"}
#: Measurements survive a discarded attempt: the history is the point.
_KEPT_NAMES = {scorecard.SCORECARD_NAME}
#: A project larger than this is not copied; its attempts are not guarded.
MAX_SNAPSHOT_BYTES = 500 * 1024 * 1024
TEST_TIMEOUT_S = 300
#: The tests run before and after an attempt. A suite slower than this is not
#: run for the guard (batch 1 suites took under 7 s; batch 5 ones 53-70 s).
MAX_GUARD_SECONDS = 120.0


def _walk(root: Path) -> dict[str, tuple[int, int]]:
    seen: dict[str, tuple[int, int]] = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIPPED]
        for name in files:
            path = Path(current) / name
            if path.is_symlink():
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            seen[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return seen


def _test_modules(files: dict[str, tuple[int, int]]) -> list[str]:
    return sorted(rel for rel in files if is_pytest_module(Path(rel).name))


def _module_of(item: str) -> str:
    return item.split("::", 1)[0].split(" (", 1)[0]


def own_modules(project_root: Path, task_id: str, modules: list[str], log_dir: str) -> set[str]:
    """The test modules this task has run and no other task has.

    Read from the per-task run records the implementer keeps: a module with a
    record under this task's id and under no other. A module two tasks ran is
    shared work and belongs to neither.
    """
    logs = project_root / log_dir
    own = set()
    for rel in modules:
        name = rel.replace("/", "_") + ".log"
        if not (logs / f"{task_id}.{name}").is_file():
            continue
        if any(path.name != f"{task_id}.{name}" for path in logs.glob(f"*.{name}")):
            continue
        own.add(rel)
    return own


def regressions(before: scorecard.Values, after: scorecard.Values, rewritten: set[str]) -> list[str]:
    """What an attempt broke, as test node ids or one line per weakened module.

    A test that passed and now fails is broken. A passing test that is no
    longer reported is broken too, unless the attempt rewrote its module: a
    rewrite may rename tests, and is judged on how many of them pass.
    """
    broken = []
    for node, value in before.items():
        module = node.split("::", 1)[0]
        if value == 1 and (after.get(node) == 0 or (node not in after and module not in rewritten)):
            broken.append(node)
    for module in sorted(rewritten):
        had = sum(1 for node, value in before.items() if value == 1 and node.split("::", 1)[0] == module)
        has = sum(1 for node, value in after.items() if value == 1 and node.split("::", 1)[0] == module)
        if has < had and not any(node.split("::", 1)[0] == module for node in broken):
            broken.append(f"{module} ({had} tests passed before this attempt, {has} pass after it)")
    return sorted(broken)


class Snapshot:
    """A copy of a project's files that can be put back any number of times."""

    def __init__(self, project_root: Path, store: Path, files: dict[str, tuple[int, int]]) -> None:
        self.project_root, self.store, self.files = project_root, store, files

    @classmethod
    def take(cls, project_root: Path) -> Snapshot | None:
        """``None`` when the project is too large to copy."""
        files = _walk(project_root)
        if sum(size for size, _ in files.values()) > MAX_SNAPSHOT_BYTES:
            LOGGER.warning("[ratchet] %s is too large to copy", project_root.name)
            return None
        store = Path(tempfile.mkdtemp(prefix="llmxive-attempt-"))
        for rel in files:
            target = store / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(project_root / rel, target)
        return cls(project_root, store, files)

    def restore(self) -> list[str]:
        """Put every file back; return what had changed."""
        now = _walk(self.project_root)
        undone = []
        for rel in sorted(now):
            if rel not in self.files and Path(rel).name not in _KEPT_NAMES:
                (self.project_root / rel).unlink(missing_ok=True)
                undone.append(rel)
        for rel, state in sorted(self.files.items()):
            if now.get(rel) != state and Path(rel).name not in _KEPT_NAMES:
                target = self.project_root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.store / rel, target)
                undone.append(rel)
        return undone

    def close(self) -> None:
        shutil.rmtree(self.store, ignore_errors=True)


@contextmanager
def files_unchanged(project_root: Path) -> Iterator[list[str]]:
    """Whatever runs inside leaves the project's files as it found them.

    For the harness's own pytest sessions. A project's tests call its scripts
    with small arguments and clear output folders, and the harness runs every
    test before and after each attempt: in batches 4 and 5 (2026-10-12) that
    replaced or removed the results another task had produced in 20 of 131
    rejections (a one-row ``tv_summary.csv`` in place of the twelve-row one, a
    ``rmtree("results")``). A test session is evidence through its output,
    never through what it leaves on disk. Yields a list that holds, once the
    block has ended, the files that were put back. A project too large to copy
    is not protected.
    """
    snapshot = Snapshot.take(project_root)
    put_back: list[str] = []
    try:
        yield put_back
    finally:
        if snapshot is not None:
            try:
                changed = snapshot.restore()
                put_back.extend(changed)
                if changed:
                    LOGGER.info("[ratchet] %s: put back %d file(s) a test session changed: %s",
                                project_root.name, len(changed), ", ".join(changed[:8]))
            finally:
                snapshot.close()


@dataclass
class Attempt:
    """The state of a project just before one implementer attempt."""

    project_root: Path
    task_id: str
    memory_dir: Path
    definition: str
    snapshot: Snapshot
    before: scorecard.Values
    modules: list[str] = field(default_factory=list)
    log_dir: str = RESEARCH_LOG_DIR
    #: How many tests passed after the attempt (set by :meth:`settle`).
    passing_after: int = 0
    #: Test modules with every reported test passing after a kept attempt.
    passing_modules: set[str] = field(default_factory=set)
    #: The task's own tests that passed before a kept attempt and fail after it.
    own_broken: list[str] = field(default_factory=list)

    def settle(self) -> tuple[bool, list[str]]:
        """Run the tests again; keep the attempt or undo it.

        Returns ``(kept, broken)``. The snapshot is removed either way. An
        attempt is undone for breaking a test that is not the task's own (see
        :func:`own_modules`). Breaking only its own tests leaves the work in
        place and lists them in ``own_broken`` for the caller to mark: the
        verifier may have asked for exactly the change that fails them.
        """
        from llmxive import sandbox

        try:
            now = _walk(self.project_root)
            modules = _test_modules(now)
            rewritten = {rel for rel in self.modules if rel in now and now[rel] != self.snapshot.files[rel]}
            if modules:
                with files_unchanged(self.project_root):
                    result = sandbox.run_pytest_modules(
                        project_dir=self.project_root, test_relpaths=modules, timeout_s=TEST_TIMEOUT_S)
                after = scorecard.pytest_outcomes(result.stdout)
                self.passing_after = sum(1 for value in after.values() if value == 1)
                broken = regressions(self.before, after, rewritten)
                if result.timed_out and not broken:
                    broken = [f"the project's tests no longer finish within {TEST_TIMEOUT_S} s"]
                else:
                    own = own_modules(self.project_root, self.task_id, modules, self.log_dir)
                    self.own_broken = [item for item in broken if _module_of(item) in own]
                    broken = [item for item in broken if _module_of(item) not in own]
                failing = {_module_of(node) for node, value in after.items() if value != 1}
                self.passing_modules = {_module_of(node) for node in after} - failing
                output = result.stdout
            else:
                broken = sorted(node for node, value in self.before.items() if value == 1)
                output = "(every test module was removed)"
            if not broken:
                values = {"kept": 1}
                if self.own_broken:
                    values["own_tests_broken"] = len(self.own_broken)
                scorecard.record(self.memory_dir, self.task_id, "attempt", values, definition=self.definition)
                return True, []
            self.own_broken, self.passing_modules = [], set()
            undone = self.snapshot.restore()
            self.passing_after = sum(1 for value in self.before.values() if value == 1)
            scorecard.record(self.memory_dir, self.task_id, "attempt", {"kept": 0}, definition=self.definition)
            self._write_record(broken, undone, output)
            return False, broken
        finally:
            self.snapshot.close()

    def record_path(self) -> Path:
        return self.project_root / RESEARCH_LOG_DIR / f"{self.task_id}.attempt-not-kept.log"

    def _write_record(self, broken: list[str], undone: list[str], output: str) -> None:
        shown = [rel for rel in undone if f"/{RESEARCH_LOG_DIR.split('/')[-1]}/" not in f"/{rel}"]
        body = (
            f"# Attempt at {self.task_id} was NOT kept\n\n"
            "These tests passed before the attempt and did not pass after it:\n\n"
            + "\n".join(f"- `{item}`" for item in broken)
            + "\n\nEvery file was put back as it was before the attempt, so the changes below "
            "are gone. Do the task again without breaking these tests. If a test is itself "
            "wrong, change the test and the code together so that it still passes.\n\n"
            "## files the attempt changed (now restored)\n\n"
            + ("\n".join(f"- `{rel}`" for rel in shown[:60]) or "(none)")
            + f"\n\n## the tests after the attempt\n\n```\n{output[-6000:]}\n```\n"
        )
        path = self.record_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def measure(project_root: Path, *, log_dir: str) -> scorecard.Values | None:
    """The outcome of every project test right now, or ``None`` when attempts
    are not guarded (paper track, no tests, tests too slow to run twice)."""
    from llmxive import sandbox

    if log_dir != RESEARCH_LOG_DIR:
        return None
    modules = _test_modules(_walk(project_root))
    if not modules:
        return None
    with files_unchanged(project_root):
        result = sandbox.run_pytest_modules(project_dir=project_root, test_relpaths=modules, timeout_s=TEST_TIMEOUT_S)
    if result.timed_out or result.duration_s > MAX_GUARD_SECONDS:
        LOGGER.warning("[ratchet] %s: tests took %.0f s; attempts are not guarded",
                       project_root.name, result.duration_s)
        return None
    return scorecard.pytest_outcomes(result.stdout)


def begin(project_root: Path, task_id: str, memory_dir: Path, definition: str, *, log_dir: str,
          before: scorecard.Values | str | None = "measure") -> Attempt | None:
    """Measure and copy the project before an attempt, or ``None`` when there
    is nothing to guard (paper track, no tests, no passing test, tests too
    slow to run twice, or a project too large to copy).

    ``before`` is what :func:`measure` returned for the project as it is now,
    when the caller already has it: several candidate replies tried from one
    restored state share one measurement. Batch 5 (2026-10-12): a retry ran the
    whole suite 8 times at 53-70 s each, 86 of one run's 132 implementing
    minutes.
    """
    if before == "measure":
        before = measure(project_root, log_dir=log_dir)
    if not isinstance(before, dict) or not any(value == 1 for value in before.values()):
        return None  # not guarded, or nothing passes, so nothing can be broken
    snapshot = Snapshot.take(project_root)
    if snapshot is None:
        return None
    return Attempt(project_root, task_id, memory_dir, definition, snapshot, before,
                   _test_modules(snapshot.files), log_dir)

__all__ = ["MAX_SNAPSHOT_BYTES", "Attempt", "begin", "files_unchanged", "measure", "own_modules", "regressions"]
