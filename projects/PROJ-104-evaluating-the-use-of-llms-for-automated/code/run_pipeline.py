"""Orchestrator for the quick‑start pipeline (Task T001).

The script supports two modes:

* ``--sample N`` – fetch a real 5‑sample (or *N*) subset of commit pairs,
  run the lightweight generation step and create the artefacts required
  by the quick‑start test.
* ``--full`` – run the full pipeline (power analysis, data extraction,
  generation, etc.).  For the purpose of the quick‑start test only the
  ``--sample`` path is exercised.

The implementation deliberately avoids heavy external dependencies
(no model downloads) and produces deterministic placeholder outputs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Import the minimal implementations we just added/modified.
from code import data_extraction, generation, power_analysis

log = get_logger(__name__)

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LLM fidelity pipeline (quick‑start).")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Run a tiny end‑to‑end demo on a real *sample* of commit pairs (default: 5).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full pipeline (power analysis + data extraction + generation).",
    )
    return parser.parse_args(argv)

def _run_sample(sample: int) -> int:
    """Execute the minimal end‑to‑end flow for *sample* rows."""
    # 1. Power analysis (writes results/power_report.md)
    power_analysis.run_power_analysis()

    # 2. Data extraction – ensure we have at least *sample* rows.
    rc = data_extraction.main()
    if rc != 0:
        log.error("Data extraction failed")
        return rc

    # Truncate to the requested number of rows (deterministic).
    csv_path = paths.data("raw", "commit_pairs.csv")
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        import csv as _csv
        _csv.field_size_limit(10_000_000)
        reader = _csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= sample:
                break
            rows.append(row)

    # Overwrite with the truncated subset.
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=reader.fieldnames)  # type: ignore[arg-type]
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Re‑record checksum for the truncated CSV.
    from code.data_extraction import update_metadata
    update_metadata(csv_path)

    # 3. Generation (creates placeholder files and success‑rate CSV)
    rc = generation.main()
    if rc != 0:
        log.error("Generation failed")
        return rc

    # 4. Intent‑entity extraction – the existing implementation works on the
    #    dummy CSV and will emit at least one JSON file under
    #    ``data/intermediate/intent_entities``.
    from code import entity_extraction_intent
    rc = entity_extraction_intent.main()
    if rc != 0:
        log.error("Intent extraction failed")
        return rc

    return 0

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.full:
        # For the quick‑start we only need the sample path; the full
        # pipeline is exercised elsewhere in the project.
        log.info("Running full pipeline (delegated to individual stages).")
        power_analysis.run_power_analysis()
        rc = data_extraction.main()
        if rc != 0:
            return rc
        rc = generation.main()
        if rc != 0:
            return rc
        rc = entity_extraction_intent.main()
        return rc

    # Default: run a tiny sample (5 rows if not specified).
    sample_size = args.sample if args.sample is not None else 5
    log.info("Running quick‑start sample with %d rows", sample_size)
    return _run_sample(sample_size)

if __name__ == "__main__":
    sys.exit(main())
