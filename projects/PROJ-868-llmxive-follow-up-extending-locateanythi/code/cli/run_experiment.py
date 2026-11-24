"""
Deprecated placeholder kept for backward compatibility.

The original entry point expected under `src.cli.run_experiment` has been
re‑implemented in the `src` package. This file simply re‑exports the new
implementation so that any external scripts that still import
`code.cli.run_experiment` continue to work.
"""

from src.cli.run_experiment import main  # noqa: F401