"""download_data.py
-----------------
Wrapper CLI for the HCP data acquisition step.

This module provides the entry point used in the project's quickstart
(`python -m src.download_data`). It forwards arguments to the core
implementation in ``src.data.download_hcp`` while handling the optional
``--hcp-token`` argument (by populating the ``HCP_TOKEN`` environment
variable) and passing through ``--subject-limit`` and ``--output-dir``.
"""

import argparse
import os
import sys

from src.data.download_hcp import main as download_hcp_main

def _forward_args(subject_limit: int, output_dir: str) -> None:
    """
    Re‑invoke the original ``download_hcp`` CLI with the appropriate
    arguments.  The function manipulates ``sys.argv`` so that the
    imported ``download_hcp_main`` sees the expected command‑line
    parameters without needing to spawn a subprocess.
    """
    # Preserve the original argv for safety.
    original_argv = sys.argv[:]
    try:
        sys.argv = [
            "download_hcp.py",
            "--subject-limit",
            str(subject_limit),
            "--output-dir",
            output_dir,
        ]
        download_hcp_main()
    finally:
        # Restore argv to avoid side‑effects for callers.
        sys.argv = original_argv

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download HCP time series and behavioural data (wrapper)."
    )
    parser.add_argument(
        "--hcp-token",
        type=str,
        required=False,
        help="HCP access token. If supplied, it overrides the HCP_TOKEN env var.",
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        default=200,
        help="Maximum number of subjects to download (default: 200).",
    )
    parser.add_argument(
        "--fd-threshold",
        type=float,
        default=0.2,
        help="Motion threshold (not used here; kept for CLI compatibility).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    args = parser.parse_args()

    if args.hcp_token:
        os.environ["HCP_TOKEN"] = args.hcp_token

    # Forward the relevant arguments to the core implementation.
    _forward_args(args.subject_limit, args.output_dir)

if __name__ == "__main__":
    main()
