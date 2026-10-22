"""
Minimal CLI orchestrator for the corrosion‑prediction pipeline.

Only the ``download`` stage is implemented here because it is the
prerequisite for the current task (T006). The script can be extended
later with additional stages (validate, preprocess, …) without breaking
existing functionality.

The orchestrator follows the convention used in ``quickstart.md``:
    python code/cli/run_pipeline.py --stage <stage_name>

For the ``download`` stage it simply invokes the ``main`` function of
``code.data.download_nist``. Any exception propagates to the caller,
resulting in a non‑zero exit status – exactly what the specification
expects when the dataset is insufficient.
"""

import argparse
import sys

from code.data.download_nist import main as download_main

def run_download_stage() -> None:
    """Execute the NIST download script."""
    download_main()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a single pipeline stage."
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=["download"],  # additional stages can be added later
        help="Pipeline stage to execute.",
    )
    args = parser.parse_args()

    if args.stage == "download":
        run_download_stage()
    else:
        # This branch should never be hit because argparse restricts choices,
        # but it provides a clear error message for future extensions.
        sys.stderr.write(f"Unsupported stage: {args.stage}\\n")
        sys.exit(1)

if __name__ == "__main__":
    main()