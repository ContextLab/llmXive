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
#: The tests run twice per attempt. A suite slower than this is not run for
#: the guard (every recorded run in the canary took under 7 s).
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
    #: How many tests passed after the attempt (set by :meth:`settle`).
    passing_after: int = 0

    def settle(self) -> tuple[bool, list[str]]:
        """Run the tests again; keep the attempt or undo it.

        Returns ``(kept, broken)``. The snapshot is removed either way.
        """
        from llmxive import sandbox

        try:
            now = _walk(self.project_root)
            modules = _test_modules(now)
            rewritten = {rel for rel in self.modules if rel in now and now[rel] != self.snapshot.files[rel]}
            if modules:
                result = sandbox.run_pytest_modules(
                    project_dir=self.project_root, test_relpaths=modules, timeout_s=TEST_TIMEOUT_S)
                after = scorecard.pytest_outcomes(result.stdout)
                self.passing_after = sum(1 for value in after.values() if value == 1)
                broken = regressions(self.before, after, rewritten)
                if result.timed_out and not broken:
                    broken = [f"the project's tests no longer finish within {TEST_TIMEOUT_S} s"]
                output = result.stdout
            else:
                broken = sorted(node for node, value in self.before.items() if value == 1)
                output = "(every test module was removed)"
            if not broken:
                scorecard.record(self.memory_dir, self.task_id, "attempt", {"kept": 1}, definition=self.definition)
                return True, []
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


def begin(project_root: Path, task_id: str, memory_dir: Path, definition: str, *, log_dir: str) -> Attempt | None:
    """Measure and copy the project before an attempt, or ``None`` when there
    is nothing to guard (paper track, no tests, no passing test, tests too
    slow to run twice, or a project too large to copy)."""
    from llmxive import sandbox

    if log_dir != RESEARCH_LOG_DIR:
        return None
    modules = _test_modules(_walk(project_root))
    if not modules:
        return None
    result = sandbox.run_pytest_modules(project_dir=project_root, test_relpaths=modules, timeout_s=TEST_TIMEOUT_S)
    before = scorecard.pytest_outcomes(result.stdout)
    if result.timed_out or result.duration_s > MAX_GUARD_SECONDS:
        LOGGER.warning("[ratchet] %s: tests took %.0f s; attempt at %s is not guarded",
                       project_root.name, result.duration_s, task_id)
        return None
    if not any(value == 1 for value in before.values()):
        return None  # nothing passes, so nothing can be broken
    # The tests may write files; copy what they left, which is what the attempt starts from.
    snapshot = Snapshot.take(project_root)
    if snapshot is None:
        return None
    return Attempt(project_root, task_id, memory_dir, definition, snapshot, before, modules)

__all__ = ["MAX_SNAPSHOT_BYTES", "Attempt", "begin", "regressions"]
