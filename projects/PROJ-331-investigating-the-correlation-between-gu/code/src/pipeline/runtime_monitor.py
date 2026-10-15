"""Utility module for running the full gut‑microbiome‑PD progression pipeline
with explicit runtime monitoring.

This module provides a small wrapper around the existing ``code.src.pipeline.__main__``
entry point.  It is useful for external callers (e.g. CI scripts) that want to
invoke the pipeline programmatically while ensuring that the ``results/runtime_log.txt``
file is created and that the exit status reflects any budget violations.

The implementation deliberately does **not** duplicate any logic from
``__main__.py`` – it simply forwards the command‑line arguments and returns the
integer exit code.  Keeping the wrapper minimal guarantees that any future
changes to the core pipeline (stage ordering, budget limits, etc.) are
automatically respected.
"""

from __future__ import annotations

import sys
from typing import List

# Import the canonical pipeline entry point.
from code.src.pipeline.__main__ import main as pipeline_main


def run_pipeline(argv: List[str] | None = None) -> int:
    """
    Execute the full analysis pipeline.

    Parameters
    ----------
    argv : list of str or None
        Command‑line arguments to pass to the pipeline.  If ``None`` the
        arguments from ``sys.argv[1:]`` are used (the default behaviour
        when the function is called from the command line).

    Returns
    -------
    int
        The exit status returned by ``code.src.pipeline.__main__.main``.
        ``0`` indicates success; any non‑zero value signals a failure
        (e.g. missing inputs or a runtime‑budget breach).
    """
    if argv is None:
        argv = sys.argv[1:]
    return pipeline_main(argv)


def main() -> int:
    """Entry point for ``python -m code.src.pipeline.runtime_monitor``."""
    return run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
