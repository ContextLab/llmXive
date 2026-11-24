"""
Helper script to (re)generate a small set of networks for a given topology,
ensuring that root‑level metadata JSON files (e.g. data/raw/networks/metadata_BA_0001.json)
are present and contain the required structural metrics.

This script simply invokes the main network generator with the desired
arguments. It exists so that the task can request execution without
altering the public CLI of ``code.generate_networks``.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    # Build the command line for the network generator.
    cmd = [
        sys.executable,
        "-m",
        "code.generate_networks",
        "--topology",
        "BA",
        "--instances",
        "2",
        "--seed",
        "0",
    ]
    log.info("Running network generator: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=Path.cwd())
    log.info("Generation completed. Root‑level metadata files should now exist.")

if __name__ == "__main__":
    main()
