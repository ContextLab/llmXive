"""Run the full research pipeline.

This module provides three entry points:
- ``run_smoke_test``: executes the Phase‑0 plumbing test.
- ``run_full_pipeline``: runs every implemented stage in order.
- ``main``: CLI entry point that parses ``--sample`` and ``--full`` flags.
"""
from __future__ import annotations

import argparse
import sys

from llmxive_toolkit import get_logger, paths

from code.generation import generate_documentation, CommitPair
from code.power_analysis import run_power_analysis
from code.data_extraction import main as data_extraction_main

log = get_logger(__name__)

def run_smoke_test() -> int:
    """Phase‑0 smoke test: generate a single realistic file to verify plumbing."""
    # Use a tiny hard-coded commit pair matching the CommitPair signature.
    # This is a plumbing smoke test only and is never used as analysis data.
    pair = CommitPair(
        commit_hash="smoke_test_hash_001",
        commit_message="Update installation guide for Python 3.11",
        prev_doc_snippet="Installation: Use pip install .",
        repository_name="smoke-test-repo",
    )
    
    # Invoke the generation module (CPU-only)
    output = generate_documentation(pair, model_id="phi3-mini")
    
    # Write to the exact path specified in tasks.md
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    
    log.info("Smoke test output written to %s", out_path)
    return 0

def run_full_pipeline() -> int:
    """Execute all implemented pipeline stages sequentially."""
    # 1. Power analysis
    log.info("Running power analysis...")
    try:
        run_power_analysis()
    except Exception as e:
        log.error("Power analysis failed: %s", e)
        return 1

    # 2. Data extraction
    log.info("Running data extraction...")
    extraction_exit = data_extraction_main()
    if extraction_exit != 0:
        log.error("Data extraction failed with exit code %d", extraction_exit)
        return extraction_exit

    log.info("Full pipeline completed successfully.")
    return 0

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LLM fidelity pipeline")
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Run the Phase-0 plumbing smoke test.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Execute the full pipeline (power analysis + data extraction).",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.sample:
        log.info("Running smoke test with %d sample(s)", args.sample)
        return run_smoke_test()
    if args.full:
        log.info("Running full pipeline")
        return run_full_pipeline()
    
    log.info("No flags supplied; running smoke test by default.")
    return run_smoke_test()

if __name__ == "__main__":
    sys.exit(main())