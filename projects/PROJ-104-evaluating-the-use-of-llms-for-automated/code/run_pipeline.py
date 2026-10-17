"""Single entry point for the LLM fidelity evaluation pipeline.

``python -m code.run_pipeline --sample 5`` runs the Phase-0 plumbing
smoke test; ``python -m code.run_pipeline --full`` runs every
implemented pipeline stage in order. Stages that arrive with later
tasks are reported as pending; the run still exits 0 so the run-book
stays executable at every point of the project.
"""

from __future__ import annotations

import argparse
import time

from llmxive_toolkit import get_logger, paths

from code.generation import CommitPair, generate_documentation
from code.power_analysis import run_power_analysis

log = get_logger(__name__)

# Tiny hard-coded commit pair used ONLY as a Phase-0 plumbing
# self-check of the entry point (never analysis data).
SMOKE_TEST_PAIR = CommitPair(
    commit_hash="smoke0deadbeef",
    commit_message="Fix plumbing smoke test for the pipeline entry point",
    prev_doc_snippet="The pipeline plumbing is documented here.",
    repository_name="pipeline-selfcheck",
)

# Stages implemented so far, in pipeline order.
STAGES = {
    "power_analysis": run_power_analysis,
}

# Stages that arrive with later tasks (T003-T010).
PENDING_STAGES = [
    "data_extraction (T003)",
    "gold_annotation (T004)",
    "generation (T005)",
    "entity_extraction_surface (T006)",
    "entity_extraction_intent (T007)",
    "fidelity_scoring (T008)",
    "statistical_analysis (T009)",
    "visualization (T010)",
]


def run_smoke_test() -> paths.root.__class__:
    """Run the Phase-0 plumbing self-check and write its output file."""
    generated = generate_documentation(SMOKE_TEST_PAIR)
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    content = (
        "# Phase-0 plumbing self-check output\n"
        f"commit_hash: {SMOKE_TEST_PAIR.commit_hash}\n"
        "This is a plumbing self-check of the CPU-only generation "
        "module wiring. It produces no analysis data and no "
        "reported metrics; the real experiment data arrives with "
        "T003 (commit-pair extraction).\n\n"
        "--- generated ---\n"
        f"{generated}\n"
    )
    out_path.write_text(content, encoding="utf-8")
    log.info("Smoke test wrote %s", out_path)
    return out_path


def run_full_pipeline() -> int:
    """Run every implemented pipeline stage in order; return exit code."""
    implemented = []
    log.info("Running stage: smoke_test (Phase 0 plumbing self-check)")
    run_smoke_test()
    implemented.append("smoke_test")
    for name, stage_fn in STAGES.items():
        log.info("Running stage: %s", name)
        stage_fn()
        implemented.append(name)
    print(f"implemented stages: {', '.join(implemented)}")
    print(f"pending stages (later tasks): {', '.join(PENDING_STAGES)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LLM fidelity evaluation pipeline entry point"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="run the Phase-0 plumbing self-check (N is informational)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="run every implemented pipeline stage",
    )
    args = parser.parse_args(argv)

    if args.full:
        return run_full_pipeline()

    n = args.sample if args.sample is not None else 5
    start = time.time()
    run_smoke_test()
    elapsed = time.time() - start
    print(f"Smoke test OK ({elapsed:.1f}s, sample size {n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())