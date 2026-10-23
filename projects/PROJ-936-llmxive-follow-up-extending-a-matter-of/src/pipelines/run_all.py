"""Entry point for the end‑to‑end efficiency‑reasoning pipeline.

For the purpose of the current task (T001) this script ensures that the
τ‑bench dataset is downloaded and that the raw task definitions are
parsed into the canonical CSV required by downstream contract tests.

The script respects a ``--skip-download`` flag so that downstream runs can
reuse a cached dataset.  When the dataset is present (or successfully
downloaded) the script also invokes the ``parse_task_definitions`` module
to produce ``data/derived/task_definitions.csv``.
"""

import argparse
import sys

# The download implementation lives in ``code/download_tau_c_bench.py``.
# Importing it via the module name works because the project root is on
# ``PYTHONPATH`` when the runner executes ``python -m src.pipelines.run_all``.
from download_tau_c_bench import main as download_main

# The parser for the raw JSON → CSV conversion.
from parse_task_definitions import parse_and_write

from llmxive_toolkit import paths


def _parse_args(argv):
    """Parse known arguments, ignoring any others."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="If set, the dataset download step is bypassed.",
    )
    # The following arguments are part of the broader pipeline spec.
    # They are accepted here so that the quick‑start command does not
    # error out, but they are otherwise unused in this minimal run.
    parser.add_argument("--max_tasks", type=int, default=200)
    parser.add_argument("--penalty_threshold", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=42)

    # ``parse_known_args`` returns the known args and a list of the
    # remaining unknown ones, which we deliberately ignore.
    args, _ = parser.parse_known_args(argv)
    return args


def main(argv=None):
    """Run the pipeline (download + parsing)."""
    if argv is None:
        argv = sys.argv[1:]

    args = _parse_args(argv)

    if not args.skip_download:
        # The download script raises on failure, which will abort this
        # pipeline run with a clear error message.
        download_main()
    else:
        # When skipping, verify that the expected file exists.
        expected = paths.data("raw", "τc_bench", "tasks.json")
        if not expected.is_file():
            raise FileNotFoundError(
                f"Dataset was skipped but {expected} does not exist."
            )

    # ------------------------------------------------------------------
    # Parse the raw JSON into the canonical CSV required by the contract
    # test ``tests/contract/test_task_schema.py``.
    # ------------------------------------------------------------------
    csv_path = paths.data("derived", "task_definitions.csv")
    parse_and_write(csv_path)

    print("Pipeline step completed (download + parse).")


if __name__ == "__main__":
    main()