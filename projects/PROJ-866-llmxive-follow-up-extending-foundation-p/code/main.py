"""
code.main
------------

Orchestrator script for the llmXive follow‑up project.

The original placeholder has been replaced with a minimal but functional
command‑line interface that supports the ``--analyze`` flag required by
task **T070**.  When invoked with ``--analyze`` the script delegates to
``analysis.tradeoff_model.main`` which:

* loads all processed execution logs from ``data/processed``,
* fits a logistic trade‑off curve,
* writes ``data/results/tradeoff_curve.csv``,
* writes ``data/results/threshold_report.json`` (the JSON keys required
  by the specification).

The script can be extended in the future to support ``--generate`` and
``--compress`` flags, but those are not needed for this task.
"""

import argparse
import sys
from pathlib import Path

def _run_analyze() -> None:
    """
    Execute the analysis pipeline.

    This function imports the analysis module lazily so that the heavy
    dependencies (numpy, pandas, scipy) are only loaded when required.
    """
    try:
        from analysis.tradeoff_model import main as analysis_main
    except ImportError as exc:
        sys.stderr.write(f"Failed to import analysis module: {exc}\\n")
        sys.exit(1)

    # The analysis module provides its own argument parser; we simply
    # invoke its ``main`` function with default arguments.
    analysis_main()

def main(argv: list = None) -> None:
    """
    Entry point for ``python code/main.py``.

    Supported flags:
    * ``--analyze`` – run the statistical analysis and generate the two
      core result artifacts.
    """
    parser = argparse.ArgumentParser(
        description="Project orchestrator – currently supports analysis."
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run the analysis pipeline and produce core result files.",
    )
    args = parser.parse_args(argv)

    if args.analyze:
        _run_analyze()
    else:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()
