"""Pipeline entry point for the LLM fidelity evaluation project.

Phase 0 (T001): a minimal runnable smoke test. It loads one tiny
hard-coded synthetic commit pair (used ONLY to test the plumbing,
never as analysis data), invokes the CPU-only generation module, and
writes a single output file to ``data/generated/phi3-mini/sample_test.txt``.

Later phases (T003+) extend this entry point with ``--full`` for the
end-to-end run over the real dataset.
"""

from __future__ import annotations

import argparse
import time

from llmxive_toolkit import get_logger, paths

from code.generation import CommitPair, generate_documentation

log = get_logger(__name__)

# One tiny synthetic commit pair, used ONLY as a smoke test of the
# plumbing. It is never part of the analysis dataset (see T003 for the
# real data extraction from pandas/requests/scikit-learn/flask/django).
SMOKE_TEST_PAIR = CommitPair(
    commit_hash="0" * 40,
    commit_message="DOC: clarify retry behaviour of Session.request in docs",
    repository_name="smoke-test",
    prev_doc_snippet="Session.request(...) sends the request and returns the response.",
)


def run_smoke_test() -> "paths.root.__class__":
    """Run the Phase-0 plumbing smoke test and write its output file."""
    start = time.time()
    output_text = generate_documentation(SMOKE_TEST_PAIR, model_id="phi3-mini")
    out_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(output_text)
    elapsed = time.time() - start
    log.info("smoke test complete in %.2fs; wrote %s", elapsed, out_path)
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LLM fidelity evaluation pipeline")
    parser.add_argument(
        "--sample",
        type=int,
        default=5,
        help="number of samples for a smoke-test / small run (Phase 0 uses 1 synthetic pair)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="run the full end-to-end pipeline over the real dataset (implemented in T003+)",
    )
    args = parser.parse_args(argv)

    if args.full:
        # Full pipeline stages are implemented by tasks T002-T010.
        raise NotImplementedError(
            "the full pipeline is implemented by tasks T002-T010; "
            "use --sample for the Phase-0 smoke test"
        )

    out_path = run_smoke_test()
    print(f"Smoke test OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
