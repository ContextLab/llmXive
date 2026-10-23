"""Entry point for the end‑to‑end efficiency‑reasoning pipeline.

For the purpose of the current task (T001) this script only ensures that
the τ‑bench dataset is downloaded.  All other pipeline stages are
placeholders; they accept the same CLI arguments as documented in the
quickstart guide but simply ignore them.

The script respects a ``--skip-download`` flag so that downstream runs can
reuse a cached dataset.
"""

import argparse
import sys

# The download implementation lives in ``code/download_tau_c_bench.py``.
# Importing it via the module name works because the project root is on
# ``PYTHONPATH`` when the runner executes ``python -m src.pipelines.run_all``.
from download_tau_c_bench import main as download_main


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
    """Run the pipeline (currently only the download step)."""
    if argv is None:
        argv = sys.argv[1:]

    args = _parse_args(argv)

    if not args.skip_download:
        # The download script raises on failure, which will abort this
        # pipeline run with a clear error message.
        download_main()
    else:
        # When skipping, we still verify that the expected file exists.
        # This mirrors the behaviour of the full pipeline which would
        # assume a cached dataset.
        from llmxive_toolkit import paths

        expected = paths.data("raw", "τc_bench", "tasks.json")
        if not expected.is_file():
            raise FileNotFoundError(
                f"Dataset was skipped but {expected} does not exist."
            )

    # Placeholder for future stages – they will be added in later tasks.
    print("Pipeline step completed (download only).")


if __name__ == "__main__":
    main()