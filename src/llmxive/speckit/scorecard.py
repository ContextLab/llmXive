"""One number per criterion per attempt, kept over time, for every task.

A task's verdict used to be prose plus accept/reject, and nothing recorded what
had been measured on the way. Batch 1 of the 2026-10-11 reliability runs,
rebuilt from the verifier's saved calls: 44 observations made a passing check
fail against 64 that made a failing one pass, and 393 of 499 consecutive
observations changed nothing. None of that was visible to the pipeline.

The harness, never a model, appends one line per observation to
``<memory dir>/scorecard.jsonl``::

    {"at": ..., "task": "T005", "definition": "<hash>", "source": "run",
     "values": {"run:code/a.py --n 10": 1, "test:tests/test_a.py::test_sum": 0}}

``definition`` is the hash of what the task asked for when the observation was
made: a re-plan reuses task ids for different work, and their histories must
not be read as one.

Criteria and their values:

* ``run:<script> <arguments>`` -- 1 when that command exited 0, else 0.
* ``test:<pytest node id>`` -- 1 when the test passed, else 0.
* ``files`` -- 0 when a required file is missing or invalid.
* ``judge`` -- 1 when the independent verifier accepted the task, else 0.
* ``kept`` -- 0 when an attempt was discarded for breaking a passing test.

``None`` means the check could not be run, which is not a failure.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path

LOGGER = logging.getLogger(__name__)

SCORECARD_NAME = "scorecard.jsonl"
#: ``path::test PASSED`` as ``pytest -v`` prints it, with or without the progress column.
_PYTEST_LINE = re.compile(r"^(\S+::\S+) (PASSED|FAILED|ERROR)\b", re.MULTILINE)

Values = dict[str, int | None]

_held: list[tuple[Path, str]] | None = None


@contextlib.contextmanager
def suspended() -> Iterator[list[tuple[Path, str]]]:
    """Record nothing inside the block: a candidate that is tried and put back
    is not part of the task's history; the one that is applied is. Yields the
    rows the block would have recorded, for :func:`replay` if it is the one."""
    global _held
    previous, _held = _held, []
    try:
        yield _held
    finally:
        _held = previous


def replay(rows: list[tuple[Path, str]]) -> None:
    """Record rows that were held back by :func:`suspended`."""
    for memory_dir, line in rows:
        _append(memory_dir, line)


def scorecard_path(memory_dir: Path) -> Path:
    return memory_dir / SCORECARD_NAME


def pytest_outcomes(stdout: str) -> Values:
    """``{pytest node id: 1 or 0}`` from a ``pytest -v`` session."""
    return {node: int(outcome == "PASSED") for node, outcome in _PYTEST_LINE.findall(stdout)}


def run_values(script: str, args: object, returncode: int, stdout: str, *, is_test: bool) -> Values:
    """The criteria one executed script or test module settles.

    The same script run with other arguments is another check: 33 of 112
    scripts in batch 1 ran under two or more tasks.
    """
    command = " ".join([script, *(str(arg) for arg in args)]) if isinstance(args, list) and not is_test else script
    values: Values = {f"run:{command}": int(returncode == 0)}
    if is_test:
        values.update({f"test:{node}": value for node, value in pytest_outcomes(stdout).items()})
    return values


def record(memory_dir: Path, task: str, source: str, values: Values, *, definition: str = "") -> None:
    """Append one observation. A measurement never fails the step it measures."""
    if not values:
        return
    line = json.dumps({
        "at": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "task": task, "definition": definition, "source": source, "values": values,
    }, sort_keys=True)
    if _held is not None:
        _held.append((memory_dir, line))
        return
    _append(memory_dir, line)


def _append(memory_dir: Path, line: str) -> None:
    try:
        memory_dir.mkdir(parents=True, exist_ok=True)
        with scorecard_path(memory_dir).open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    except OSError as exc:
        LOGGER.warning("[scorecard] could not append to %s: %s", scorecard_path(memory_dir), exc)


def history(memory_dir: Path, task: str | None = None, *, definition: str | None = None) -> list[dict]:
    """Every observation in the order it was made, optionally for one task
    and one definition of it."""
    try:
        text = scorecard_path(memory_dir).read_text(encoding="utf-8")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue  # a torn final line from an interrupted run
        if isinstance(row, dict) and isinstance(row.get("values"), dict) and (task is None or row.get("task") == task) and (
                definition is None or row.get("definition") == definition):
            rows.append(row)
    return rows


def current(memory_dir: Path, task: str, *, definition: str | None = None) -> Values:
    """The latest value of every criterion ever observed for ``task``."""
    state: Values = {}
    for row in history(memory_dir, task, definition=definition):
        state.update(row["values"])
    return state


def delta(before: Values, after: Values) -> tuple[list[str], list[str]]:
    """``(improved, regressed)``: criteria that went 0 -> 1 and 1 -> 0.

    A criterion seen for the first time, or one that could not be run, is
    neither: only a measured change counts.
    """
    improved = sorted(k for k, v in after.items() if v == 1 and before.get(k) == 0)
    regressed = sorted(k for k, v in after.items() if v == 0 and before.get(k) == 1)
    return improved, regressed


__all__ = [
    "SCORECARD_NAME",
    "Values",
    "current",
    "delta",
    "history",
    "pytest_outcomes",
    "record",
    "run_values",
    "scorecard_path",
]
