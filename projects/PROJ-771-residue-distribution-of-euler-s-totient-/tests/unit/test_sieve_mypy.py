"""
Unit test for the ``sieve`` module:
- Ensures that ``mypy`` type‑checks the ``code`` package without errors.
- Verifies that every public callable (functions and classes) defined in
  ``code/sieve.py`` has a non‑empty docstring.
"""

import subprocess
import sys
import inspect
from pathlib import Path

# Ensure the project root (parent of the ``code`` directory) is on ``sys.path``.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the ``sieve`` module from the ``code`` package.
import sieve  # type: ignore

def test_mypy_passes() -> None:
    """Run ``mypy`` on the ``code`` package and assert a zero exit code."""
    result = subprocess.run(
        ["mypy", "code"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # If mypy fails, include its output in the assertion message for debugging.
    assert result.returncode == 0, f"mypy failed with output:\n{result.stdout}"

def _is_public(member_name: str) -> bool:
    """Helper to decide whether a name is considered public."""
    return not member_name.startswith("_")

def test_all_public_callables_have_docstrings() -> None:
    """
    Inspect the ``sieve`` module and assert that each public function or class
    defines a non‑empty docstring.
    """
    public_members = [
        (name, obj)
        for name, obj in inspect.getmembers(sieve)
        if _is_public(name)
    ]

    missing_doc = []
    for name, obj in public_members:
        # Functions, classes, and dataclasses are the public callables we care about.
        if inspect.isfunction(obj) or inspect.isclass(obj):
            doc = inspect.getdoc(obj)
            if not doc:
                missing_doc.append(name)

    assert not missing_doc, f"The following public callables lack docstrings: {missing_doc}"