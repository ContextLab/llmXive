"""
Linting and formatting helper module.

Provides convenient functions to construct the command‑line invocations for
Black (code formatter) and Ruff (linter) using the project's configuration
files (`pyproject.toml` for Black and the same file for Ruff).  The module
also offers simple wrappers that execute the commands and return the exit
status, making it easy to integrate linting checks into CI scripts or the
project's run‑pipeline wrapper.

The configuration files themselves already exist at the repository root
(`pyproject.toml` and `.ruff.toml`).  Black automatically reads its settings
from `pyproject.toml`; Ruff does the same when invoked without an explicit
config path because the file is discovered automatically.  The helper
functions therefore need only specify the executable and the target path.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------

def get_ruff_command() -> List[str]:
    """
    Return the command list for invoking Ruff in check mode.

    Ruff reads its configuration from ``pyproject.toml`` (or ``.ruff.toml``)
    automatically, so the command does not need to specify a config file
    explicitly.

    Returns
    -------
    List[str]
        The command that can be passed to ``subprocess.run``.
    """
    return ["ruff", "check", "."]


def get_black_command() -> List[str]:
    """
    Return the command list for invoking Black in check‑only mode.

    Black also reads its configuration from ``pyproject.toml`` automatically.
    The ``--check`` flag makes Black verify formatting without rewriting files.

    Returns
    -------
    List[str]
        The command that can be passed to ``subprocess.run``.
    """
    return ["black", "--check", "."]


def get_format_check_command() -> List[str]:
    """
    Alias for :func:`get_black_command` – retained for backward compatibility
    with earlier versions of the helper module.

    Returns
    -------
    List[str]
        Same as :func:`get_black_command`.
    """
    return get_black_command()


def get_lint_check_command() -> List[str]:
    """
    Alias for :func:`get_ruff_command` – retained for backward compatibility.

    Returns
    -------
    List[str]
        Same as :func:`get_ruff_command`.
    """
    return get_ruff_command()


# ---------------------------------------------------------------------------
# Execution wrappers
# ---------------------------------------------------------------------------

def _run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """
    Execute a command via ``subprocess.run`` and return the exit code.

    Parameters
    ----------
    cmd : List[str]
        Command and arguments to execute.
    cwd : Optional[Path]
        Working directory for the subprocess.  If ``None``, the current
        process's working directory is used (typically the project root).

    Returns
    -------
    int
        The subprocess exit code (``0`` indicates success).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        # Echo command output for debugging / CI logs
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError as exc:
        # This typically means the requested tool is not installed.
        print(f"Command not found: {cmd[0]}", file=sys.stderr)
        raise RuntimeError(str(exc)) from exc

def run_formatter(path: Optional[Path] = None) -> int:
    """
    Run Black in ``--check`` mode on the given path (or the project root).

    Parameters
    ----------
    path : Optional[Path]
        Directory or file to format.  If ``None``, the project root is used.

    Returns
    -------
    int
        Exit code from Black (``0`` if no formatting violations).
    """
    target = path or Path(__file__).parent.parent
    cmd = get_black_command()
    # Replace the generic ``.`` with the explicit target path to avoid
    # accidental execution in the wrong directory when ``path`` is supplied.
    cmd[-1] = str(target)
    return _run_command(cmd, cwd=target.parent)

def run_linter(path: Optional[Path] = None) -> int:
    """
    Run Ruff in check mode on the given path (or the project root).

    Parameters
    ----------
    path : Optional[Path]
        Directory or file to lint.  If ``None``, the project root is used.

    Returns
    -------
    int
        Exit code from Ruff (``0`` if no linting violations).
    """
    target = path or Path(__file__).parent.parent
    cmd = get_ruff_command()
    # Ruff also accepts a path argument; replace the generic ``.``.
    cmd[-1] = str(target)
    return _run_command(cmd, cwd=target.parent)

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Simple CLI that runs both the formatter and the linter sequentially.

    The exit code of the script mirrors the first non‑zero status code
    encountered (formatter first, then linter).  This behaviour matches the
    expectations of typical CI pipelines where any failure should cause the
    job to fail.
    """
    fmt_status = run_formatter()
    if fmt_status != 0:
        sys.exit(fmt_status)

    lint_status = run_linter()
    sys.exit(lint_status)


if __name__ == "__main__":
    main()
