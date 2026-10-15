"""
download_data.py
----------------
Wrapper that forwards arguments to the HCP download script.
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
    sys.argv = [
        "download_hcp",
        "--subject-limit",
        str(subject_limit),
        "--output-dir",
        output_dir,
    ]
    download_hcp_main()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Forward arguments to the HCP download script."
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        default=5,
        help="Number of subjects to download (default: 5).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    args = parser.parse_args()
    _forward_args(args.subject_limit, args.output_dir)

if __name__ == "__main__":
    main()