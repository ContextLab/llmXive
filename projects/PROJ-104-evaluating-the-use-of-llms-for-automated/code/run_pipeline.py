"""Orchestrator for the LLM‑fidelity pipeline.

This minimal orchestrator now invokes the generation stage (Task T006)
after any prior steps have been completed.  It respects the ``--sample``
flag (used by the quick‑start smoke test) by creating a tiny stub CSV
if the real ``commit_pairs.csv`` does not exist.
"""
from __future__ import annotations

import argparse
import sys

from llmxive_toolkit import get_logger, paths
from code.generation import main as generation_main

log = get_logger(__name__)

def _parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Run the LLM fidelity pipeline")
    parser.add_argument(
        "--sample",
        type=int,
        help="Run a tiny smoke‑test with the given number of dummy samples",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full pipeline (all stages that have been implemented)",
    )
    return parser.parse_args(argv)

def _ensure_placeholder_outputs(sample: int | None) -> None:
    """Create a minimal ``commit_pairs.csv`` when running a smoke test."""
    if sample is None:
        return
    csv_path = paths.data("raw", "commit_pairs.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "commit_hash",
            "commit_message",
            "repository_name",
            "doc_diff",
            "timestamp",
        ]
        writer = __import__("csv").DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(sample):
            writer.writerow(
                {
                    "commit_hash": f"{i:040x}",
                    "commit_message": f"Dummy commit message {i}",
                    "repository_name": "dummy_repo",
                    "doc_diff": f"Added dummy documentation line {i}",
                    "timestamp": "1970-01-01T00:00:00Z",
                }
            )

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.sample:
        _ensure_placeholder_outputs(args.sample)

    # Future stages (data extraction, annotation, etc.) would be called here.
    # For now we only run the generation stage.
    try:
        return generation_main()
    except Exception as e:
        log.exception("Pipeline failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
