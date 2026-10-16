"""
Convenience runner for Task T001.

This script orchestrates the two download steps (SMILES and FQY) and
ensures that the seed configuration is loaded.  It is executed by the
CI verification step to produce the required raw files under
``data/raw/`` and to confirm that ``results/seeds.json`` matches the
configuration in ``code/config/seeds.yaml``.
"""

import argparse
import sys
from pathlib import Path

# Import the seed configuration side‑effect (sets seeds and asserts)
import code.config.seed_config  # noqa: F401

# Helper to invoke the individual download entry points
from src.data.download_smiles import main as download_smiles_main
from src.data.download_fqy import main as download_fqy_main

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Download raw SMILES and FQY files and verify seeds"
    )
    parser.add_argument(
        "--smiles-url",
        required=True,
        help="URL for the SMILES parquet file",
    )
    parser.add_argument(
        "--fqy-url",
        required=True,
        help="URL for the FQY JSON file",
    )
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = _parse_args(argv)

    # Define output locations using llmxive_toolkit path helpers
    from llmxive_toolkit import paths

    smiles_path = paths.data("raw", "smiles.parquet")
    fqy_path = paths.data("raw", "fqy.json")

    # Download SMILES
    rc = download_smiles_main(
        ["--url", args.smiles_url, "--output", str(smiles_path)]
    )
    if rc != 0:
        print("SMILES download failed", file=sys.stderr)
        return rc

    # Download FQY
    rc = download_fqy_main(
        ["--url", args.fqy_url, "--output", str(fqy_path)]
    )
    if rc != 0:
        print("FQY download failed", file=sys.stderr)
        return rc

    print("All raw files downloaded and verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
