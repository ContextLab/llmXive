"""
Main entry point for the project pipeline.

For the purpose of task T004 we only need to run the dbSNP
common‑SNP fetch step.  The CLI accepts the same arguments that
the quick‑start guide mentions, but they are currently unused
because the pipeline is modular and each stage can be invoked
independently.
"""

import argparse
import sys
from pathlib import Path

# Import the fetch routine that implements the required behaviour.
from data_ingestion.fetch_dbsnp import main as fetch_dbsnp_main

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run the systematic assessment pipeline."
    )
    parser.add_argument(
        "--dbsnp-ftp",
        help="Base FTP URL for dbSNP VCF files",
    )
    parser.add_argument(
        "--jaspar-url",
        help="Base URL for JASPAR PWM download",
    )
    parser.add_argument(
        "--gwas-ftp",
        help="Base FTP URL for GWAS Catalog files",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where pipeline results will be written",
    )
    # Parse known arguments and ignore any extras (e.g., --encode-ftp,
    # --max-tf, etc.) that are present in the quickstart but not yet
    # needed by this stage.
    args, _ = parser.parse_known_args()
    return args

def main():
    # Parse arguments (they are optional for now)
    args = _parse_args()

    # Ensure the requested output directory exists so downstream
    # verification steps (e.g., checksum verification) do not fail.
    if args.output_dir:
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

    # Run the dbSNP fetch step – this creates
    # ``data/raw/snps_raw.parquet`` and logs provenance.
    try:
        fetch_dbsnp_main()
    except Exception as exc:
        print(f"Error during dbSNP fetch: {exc}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()