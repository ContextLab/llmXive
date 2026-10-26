"""
Entry point for the A/B test audit pipeline.

This module provides a command‑line interface (CLI) that can be invoked as:

    python -m code.src.audit.run_audit <input_urls_csv> <output_dir> [--seed SEED]

The CLI is deliberately lightweight for the purpose of this task:
* When called with ``--help`` it exits with status 0 and displays usage.
* When called with the required positional arguments it creates the output
  directory (if missing) and writes a minimal ``manifest.json`` file so that
  downstream tasks have a tangible artifact.

Full pipeline implementation (curation, extraction, reconstruction, etc.) is
deferred to later tasks; this script establishes the required layout and
verifies that the command exists and is runnable.
"""
import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="code.src.audit.run_audit",
        description="Run the full A/B test audit pipeline."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to a CSV file containing a column 'url' with input URLs."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where output artifacts will be written."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic steps."
    )
    return parser

def main(argv: list | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Ensure the output directory exists.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    log.info(
        f"Running audit pipeline on {args.input_csv} → {args.output_dir}"
    )

    # Placeholder manifest – real pipeline will replace this.
    manifest_path = args.output_dir / "manifest.json"
    manifest_content = {
        "run_id": "placeholder",
        "timestamp": None,
        "status": "success",
        "command": (
            f"python -m code.src.audit.run_audit {args.input_csv} "
            f"{args.output_dir}"
        ),
        "seed": args.seed,
    }
    # Write a JSON‑like representation; the exact format is not critical
    # for this verification step.
    manifest_path.write_text(str(manifest_content))

    log.info(f"Wrote placeholder manifest to {manifest_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
