"""Run‑pipeline entry point.

This module provides three public callables used by the quick‑start
documentation and the test suite:

* ``run_smoke_test()`` – executes a minimal end‑to‑end smoke test that
  generates a single documentation file using the ``generation`` module.
* ``run_full_pipeline()`` – runs the complete pipeline stages that have
  been implemented so far:
  1. Power‑analysis (T002)
  2. Data extraction (T003)
  3. Gold‑standard annotation (T004)
  4. (Placeholder) further stages are announced but not required for the
     current contract tests.
* ``main()`` – command‑line entry point used via ``python -m code.run_pipeline``.

The implementation deliberately avoids importing heavy model‑loading code
during the ``--sample`` smoke‑test path to keep execution fast (<30 s).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Local imports – these modules already exist in the repository.
from code.generation import generate_documentation, CommitPair
from code.power_analysis import run_power_analysis
from code.data_extraction import main as data_extraction_main
from code.gold_annotation import main as gold_annotation_main

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _write_smoke_output() -> Path:
    """Write a single deterministic documentation file for the smoke test.

    The file is written to ``data/generated/phi3-mini/sample_test.txt``.
    """
    # Create a synthetic commit pair that mimics the structure used in the
    # generation module's smoke‑test path.
    dummy_pair = CommitPair(
        commit_hash="dummyhash",
        commit_message="Fix typo in README",
        repository_name="dummy-repo",
        doc_diff="--- a/README.md\n+++ b/README.md\n@@\n-Old line\n+Corrected line\n",
        timestamp="2024-01-01T00:00:00Z",
    )
    # The generation module returns a deterministic string.
    output_text = generate_documentation(dummy_pair, model_id="phi3-mini")
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output_text, encoding="utf-8")
    log.info("Wrote smoke‑test output to %s", out_path)
    return out_path

# ----------------------------------------------------------------------
# Public pipeline stages
# ----------------------------------------------------------------------
def run_smoke_test() -> int:
    """Phase‑0 smoke test.

    Generates a single documentation file and exits with status 0 on
    success, non‑zero on failure.
    """
    try:
        _write_smoke_output()
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        log.exception("Smoke test failed: %s", exc)
        return 1

def run_full_pipeline() -> int:
    """Execute all implemented pipeline stages sequentially.

    Returns ``0`` on success, ``1`` on any failure.
    """
    try:
        # 1. Power analysis (already implemented in T002)
        log.info("Running power analysis...")
        run_power_analysis()

        # 2. Data extraction – this is the core of T003.
        log.info("Running data extraction (T003)…")
        extraction_exit = data_extraction_main()
        if extraction_exit != 0:
            log.error("Data extraction failed with exit code %d", extraction_exit)
            return 1

        # 3. Gold‑standard annotation (T004) – runs after the CSV exists.
        log.info("Running gold‑standard annotation (T004)…")
        annotation_exit = gold_annotation_main()
        if annotation_exit != 0:
            log.error("Gold annotation failed with exit code %d", annotation_exit)
            return 1

        # Additional stages (generation, entity extraction, etc.) are
        # optional for the current contract tests and will be added in
        # later tasks.
        log.info("Full pipeline completed successfully.")
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        log.exception("Full pipeline failed: %s", exc)
        return 1

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the LLM fidelity evaluation pipeline."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sample",
        type=int,
        metavar="N",
        help="Run the Phase‑0 smoke test (ignores N, kept for compatibility).",
    )
    group.add_argument(
        "--full",
        action="store_true",
        help="Execute the complete pipeline (power analysis, data extraction, …).",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """Entry point used by ``python -m code.run_pipeline``."""
    args = _parse_args(argv)

    if args.sample is not None:
        log.info("Running smoke test (sample=%s)", args.sample)
        return run_smoke_test()
    if args.full:
        log.info("Running full pipeline")
        return run_full_pipeline()
    # Should never reach here because argparse enforces exclusivity.
    parser = argparse.ArgumentParser()
    parser.error("No action specified")
    return 1  # pragma: no cover

if __name__ == "__main__":
    raise SystemExit(main())
