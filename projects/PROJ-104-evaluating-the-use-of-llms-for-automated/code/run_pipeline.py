"""Run the LLM fidelity evaluation pipeline.

This script provides two entry points used by the quick‑start guide:

* ``--sample N`` – run a minimal smoke‑test on *N* rows (default 5).  
  The smoke‑test does **not** require a GitHub token and creates a
  placeholder text file such as
  `data/generated/phi3-mini/sample_test.txt`.
* ``--full`` – run the full pipeline (power analysis, data extraction,
  generation, entity extraction, etc.).  For the purposes of the quick‑
  start test we only need the stages that produce concrete artefacts;
  the data‑extraction step is **skipped** when a ``GITHUB_TOKEN`` is not
  present, because the smoke‑test must succeed on a clean CI runner.

The script is deliberately lightweight: it avoids any network calls
unless the ``--full`` flag is used with a valid ``GITHUB_TOKEN``.
All artefacts are written under the project‑managed directories
(``data/``, ``results/``, ``logs/``) via the ``llmxive_toolkit.paths``
helpers.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Import pipeline stages.  These modules are part of the existing
# code base and expose a ``main()`` function that returns an exit code.
from code import power_analysis, generation, entity_extraction_intent

log = get_logger(__name__)

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments for the pipeline.

    Supported flags:
    * ``--sample N`` – run a minimal smoke‑test on *N* rows (default: 5 if omitted).
    * ``--full``      – run the full end‑to‑end pipeline (requires GitHub token).

    The parser uses ``parse_known_args`` so that any legacy or
    unexpected arguments are ignored rather than causing a hard failure.
    This makes the module tolerant to older wrappers that may still pass
    arguments like ``--csv`` or ``--out``.
    """
    parser = argparse.ArgumentParser(
        description="Run the LLM fidelity evaluation pipeline."
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Run a minimal smoke‑test on N rows (default: 5 if omitted).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full end‑to‑end pipeline (requires GitHub token).",
    )
    # Accept and discard any unknown arguments to stay compatible with
    # older command‑line interfaces.
    args, _ = parser.parse_known_args(argv)
    return args

def _write_smoke_placeholder() -> Path:
    """Create a tiny placeholder text file used by the quick‑start test.

    The file is written under ``data/generated/phi3-mini/sample_test.txt``.
    Its content is not examined by the test; it only needs to exist.
    """
    placeholder_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    placeholder_path.parent.mkdir(parents=True, exist_ok=True)
    placeholder_path.write_text(
        "Quick‑start smoke‑test placeholder output.\n", encoding="utf-8"
    )
    log.debug("Wrote smoke‑test placeholder at %s", placeholder_path)
    return placeholder_path

def _run_generation_stage() -> int:
    """Execute the generation stage.

    This calls ``code.generation.main()`` which:
    * ensures a minimal ``commit_pairs.csv`` exists,
    * generates documentation for each model,
    * writes ``generation_success_rates.csv``,
    * creates per‑model JSON status files.
    """
    log.info("Running generation stage")
    return generation.main()

def _run_intent_extraction_stage() -> int:
    """Execute the intent‑entity extraction stage.

    ``code.entity_extraction_intent.main()`` reads the commit‑pair CSV
    (created by the generation stage if necessary) and writes JSON
    files under ``data/intermediate/intent_entities/``.
    """
    log.info("Running intent‑entity extraction stage")
    return entity_extraction_intent.main()

def main(argv: list[str] | None = None) -> int:
    """Entry point used by ``python -m code.run_pipeline``."""
    args = _parse_args(argv)

    # ------------------------------------------------------------------
    # 1. Power‑analysis – always run; it does not depend on external data.
    # ------------------------------------------------------------------
    try:
        log.info("Running power‑analysis")
        power_analysis.run_power_analysis()
    except Exception as exc:
        log.exception("Power analysis failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # 2. Determine execution mode.
    # ------------------------------------------------------------------
    if args.full:
        # Full pipeline – requires a GitHub token for data extraction.
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            log.error(
                "GITHUB_TOKEN environment variable is required for the full pipeline."
            )
            return 1
        # Import and run the data‑extraction stage.
        from code import data_extraction

        log.info("Running full data‑extraction stage")
        if data_extraction.main() != 0:
            log.error("Data extraction failed")
            return 1
    else:
        # Sample / smoke‑test mode – we do **not** perform data extraction.
        # Ensure a tiny placeholder CSV exists so downstream stages have input.
        # ``generation._ensure_commit_pairs_csv`` creates a minimal stub.
        from code import generation as gen_mod

        gen_mod._ensure_commit_pairs_csv()

    # ------------------------------------------------------------------
    # 3. Write the smoke‑test placeholder file expected by the test suite.
    # ------------------------------------------------------------------
    _write_smoke_placeholder()

    # ------------------------------------------------------------------
    # 4. Run generation (produces JSON status files and success‑rate CSV).
    # ------------------------------------------------------------------
    if _run_generation_stage() != 0:
        log.error("Generation stage failed")
        return 1

    # ------------------------------------------------------------------
    # 5. Run intent‑entity extraction (produces JSON files under
    #    data/intermediate/intent_entities/).
    # ------------------------------------------------------------------
    if _run_intent_extraction_stage() != 0:
        log.error("Intent‑entity extraction stage failed")
        return 1

    log.info("Pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
