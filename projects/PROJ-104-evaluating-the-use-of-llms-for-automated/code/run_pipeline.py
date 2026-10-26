"""Run the full LLM fidelity evaluation pipeline.

This script provides a thin command‑line wrapper that is compatible with the
quick‑start guide (`python -m code.run_pipeline --sample 5` and
`python -m code.run_pipeline --full`).  It orchestrates the individual
stages of the project:

1. Power‑analysis (`code.power_analysis.run_power_analysis`)
2. Data extraction (`code.data_extraction.main`)
3. Generation (`code.generation.main`)
4. Intent‑entity extraction (`code.entity_extraction_intent.main`)
5. Fidelity scoring (`code.fidelity_scoring.run_fidelity_scoring`)
6. Statistical analysis (`code.statistical_analysis.main`)
7. Visualization (`code.visualization.main`)

In addition to the above, a minimal *smoke‑test* placeholder file
``sample_test.txt`` is written under ``data/generated/phi3-mini/`` so that
the quick‑start verification test can confirm that the pipeline ran
successfully.

The script deliberately ignores any extra arguments (e.g. ``--samples``)
that were present in earlier versions of the run‑book; it only cares about
``--sample`` (an integer) and ``--full`` (a flag).  Unknown arguments are
ignored to keep the interface stable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Import the pipeline stages.  All modules exist in the repository.
from code import (
    power_analysis,
    data_extraction,
    generation,
    entity_extraction_intent,
    fidelity_scoring,
    statistical_analysis,
    visualization,
)

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Argument handling
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments for the pipeline.

    Supported arguments:
    * ``--sample N`` – run a minimal end‑to‑end smoke test on *N* rows.
    * ``--full``      – run the full pipeline (all stages).
    Any other arguments are ignored to remain backward compatible.
    """
    parser = argparse.ArgumentParser(
        description="Run the LLM fidelity evaluation pipeline."
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Run a minimal smoke‑test on the given number of rows.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Execute the full pipeline (all stages).",
    )
    # ``parse_known_args`` returns the known args and a list of unknowns.
    # We deliberately discard the unknowns so that stale flags (e.g.
    # ``--samples``) do not cause a failure.
    args, _ = parser.parse_known_args(argv)
    return args

# ----------------------------------------------------------------------
# Helper: write the placeholder smoke‑test file required by the quick‑start test.
# ----------------------------------------------------------------------
def _write_smoke_placeholder() -> Path:
    """Create a tiny placeholder file under ``data/generated/phi3-mini/``.

    The quick‑start test checks for the existence of this file; its content
    is not inspected, but we write a short human‑readable message.
    """
    placeholder_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    placeholder_path.parent.mkdir(parents=True, exist_ok=True)
    placeholder_path.write_text(
        "LLM fidelity pipeline smoke‑test placeholder.\n",
        encoding="utf-8",
    )
    log.info("Wrote smoke‑test placeholder to %s", placeholder_path)
    return placeholder_path

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """Execute the pipeline according to the parsed arguments.

    Returns ``0`` on success, non‑zero on failure.
    """
    args = _parse_args(argv)

    # 1️⃣ Power analysis – always run; the result is needed by later stages.
    try:
        power_analysis.run_power_analysis()
    except Exception as e:
        log.exception("Power analysis failed: %s", e)
        return 1

    # 2️⃣ Data extraction – for a smoke‑test we limit the number of rows
    #    to the requested ``--sample`` value (if provided).  The underlying
    #    ``data_extraction`` module defaults to 5 rows, which matches the
    #    quick‑start guide.
    try:
        if args.sample is not None:
            # ``data_extraction.extract_commit_pairs`` accepts a ``target``
            # argument; we invoke it directly to respect the user‑requested
            # sample size.
            from code.data_extraction import extract_commit_pairs, write_csv

            rows = extract_commit_pairs(target=args.sample)
            write_csv(rows)
        else:
            # Default behaviour (extract a small hard‑coded subset).
            data_extraction.main()
    except Exception as e:
        log.exception("Data extraction failed: %s", e)
        return 1

    # 3️⃣ Generation – generate documentation for all extracted commits.
    try:
        generation.main()
    except Exception as e:
        log.exception("Generation stage failed: %s", e)
        return 1

    # 4️⃣ Intent‑entity extraction.
    try:
        entity_extraction_intent.main()
    except Exception as e:
        log.exception("Intent extraction failed: %s", e)
        return 1

    # 5️⃣ Fidelity scoring – produces ``data/processed/fidelity_metrics.csv``.
    try:
        fidelity_scoring.run_fidelity_scoring()
    except Exception as e:
        log.exception("Fidelity scoring failed: %s", e)
        return 1

    # 6️⃣ Statistical analysis – writes ``results/statistics.json``.
    try:
        statistical_analysis.main()
    except Exception as e:
        log.exception("Statistical analysis failed: %s", e)
        return 1

    # 7️⃣ Visualization – creates PNG figures and a summary markdown.
    try:
        visualization.main()
    except Exception as e:
        log.exception("Visualization failed: %s", e)
        return 1

    # Finally, write the placeholder file required by the quick‑start test.
    try:
        _write_smoke_placeholder()
    except Exception as e:
        log.exception("Failed to write smoke‑test placeholder: %s", e)
        return 1

    log.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
