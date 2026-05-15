"""T035a: FR-010 coverage audit — every speckit artifact writer guards via _real_only_guard.

This is a static-analysis test: we walk every .py file under src/llmxive/speckit/
and assert that any file that writes a `.md` artifact also imports or invokes
the guard (`assert_real_or_raise` or `guard_emit`).
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


SPECKIT_ROOT = Path(__file__).resolve().parents[2] / "src" / "llmxive" / "speckit"


def _file_writes_md_artifact(source: str) -> bool:
    """Return True if the file appears to write a .md artifact."""
    # Heuristic: looks for `.write_text(...)` calls where the target path
    # might be a .md file (we look for `.md"` substring in same line).
    if ".write_text(" not in source:
        return False
    for line in source.splitlines():
        if ".write_text(" in line and (".md" in line or '"spec' in line or '"plan' in line or '"tasks' in line):
            return True
    return False


def _file_uses_guard(source: str) -> bool:
    """Return True if the file imports / invokes _real_only_guard."""
    return (
        "_real_only_guard" in source
        or "assert_real_or_raise" in source
        or "guard_emit" in source
    )


class TestGuardCoverage(unittest.TestCase):
    def test_every_md_writer_imports_guard(self) -> None:
        offenders: list[Path] = []
        for py in SPECKIT_ROOT.glob("*.py"):
            if py.name in ("__init__.py", "_real_only_guard.py"):
                continue
            source = py.read_text()
            if _file_writes_md_artifact(source) and not _file_uses_guard(source):
                offenders.append(py)
        self.assertFalse(
            offenders,
            f"speckit files that write .md but don't reference _real_only_guard: "
            f"{[str(p.name) for p in offenders]}. Per spec 010 FR-010, every artifact "
            f"write MUST be preceded by assert_real_or_raise() or guard_emit().",
        )


class TestGuardModuleExists(unittest.TestCase):
    def test_guard_is_importable(self) -> None:
        # Sanity: the guard module must exist and expose its API.
        from llmxive.speckit._real_only_guard import (
            assert_real_or_raise,
            guard_emit,
            is_real,
            TemplateRefused,
        )
        # Smoke: the public surface is callable.
        self.assertTrue(callable(assert_real_or_raise))
        self.assertTrue(callable(guard_emit))
        self.assertTrue(callable(is_real))
        self.assertTrue(issubclass(TemplateRefused, Exception))


if __name__ == "__main__":
    unittest.main()
