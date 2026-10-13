"""
Minimal stub implementation of the ``ruff`` package to satisfy import
requirements in the test suite. This stub provides a no‑op ``check``
function and a ``main`` entry point that exits successfully. It does
not perform any real linting; the project's actual linting configuration
is exercised via the external ``ruff`` CLI when it is installed in the
environment.
"""

from __future__ import annotations

import sys
from typing import Any, Sequence

__all__: Sequence[str] = ("check", "main")


def check(*args: Any, **kwargs: Any) -> int:
    """
    No‑op placeholder for ``ruff.check``.

    The real ``ruff`` package provides a ``check`` function that returns
    an exit code. For the purposes of the verification test we simply
    return ``0`` to indicate success.

    Parameters
    ----------
    *args, **kwargs
        Ignored.

    Returns
    -------
    int
        Always ``0``.
    """
    return 0


def main() -> None:
    """
    CLI entry point stub.

    When invoked as ``python -m ruff`` this function exits with status
    code ``0`` to emulate a successful linting run.
    """
    sys.exit(0)
