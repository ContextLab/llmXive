"""
download_data.py
----------------
Small wrapper that presents a stable ``--subjects`` CLI flag expected by
the pipeline orchestrator.  The underlying implementation lives in
``code.src.data.download_hcp`` which historically used ``--subject-limit``.
This wrapper translates the flag and forwards the call.
"""
import argparse
import sys

from code.src.data.download_hcp import main as _download_hcp_main


def main() -> None:
    """
    CLI entry point matching the signature used by ``pipeline.run_pipeline``.
    """
    parser = argparse.ArgumentParser(
        description="Download HCP data for a given number of subjects."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        required=True,
        help="Number of subjects to download.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base directory for output files.",
    )
    args = parser.parse_args()

    # Translate to the flag set expected by the original script.
    argv = [
        "download_hcp",
        "--subjects",
        str(args.subjects),
        "--output-dir",
        args.output_dir,
    ]
    original_argv = sys.argv
    try:
        sys.argv = argv
        _download_hcp_main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    main()
