"""
src/pipeline/run.py
-------------------

Minimal pipeline orchestrator used by the quick‑start test suite.
It sequentially invokes the core steps of the workflow:

1. Download the raw defect dataset (or copy a bundled fallback if no
   Materials Project API key is available).
2. Compute the SHA‑256 checksum for the raw file (handled by the
   download routine).
3. Featurise the raw CSV into a compositional descriptor matrix.
4. Validate the feature matrix (row‑count checks and warning generation).
5. Perform a deterministic train‑test split.

The function returns ``None`` and prints a recognisable success message,
which is asserted by ``src/tests/test_quickstart.py``.
"""

import sys

from llmxive_toolkit import get_logger
from src.data.download import main as download_main
from src.data.featurize import main as featurize_main
from src.data.validate import main as validate_main
from src.models.split import main as split_main

log = get_logger(__name__)

def run() -> None:
    """
    Execute the end‑to‑end pipeline.

    All sub‑steps raise on failure; the orchestrator propagates the
    exception so that the test suite can detect errors.  When every
    step completes, a concise success message is printed.
    """
    log.info("Starting pipeline")

    # 1. Data acquisition (download or fallback)
    download_main()

    # 2. Featurisation
    # The CLI wrapper for featurisation expects the input and output paths
    # as positional arguments.  We reuse the default locations that the
    # wrapper forwards to the implementation in ``src.data.featurize``.
    featurize_main()

    # 3. Validation (row‑count checks, power‑analysis warning, checksum)
    validate_main()

    # 4. Train‑test split (deterministic 80 % / 20 % split)
    split_main()

    # Pipeline completed successfully.
    print("Pipeline completed successfully")
    log.info("Pipeline completed successfully")

def main() -> None:
    """
    CLI entry point used by ``python -m src.pipeline.run``.
    """
    try:
        run()
    except Exception as exc:
        log.error(f"Pipeline failed: {exc}")
        # Propagate the exception – the test harness expects a non‑zero
        # exit code on failure.
        raise

if __name__ == "__main__":
    # When executed as a script we exit with a non‑zero code on failure.
    try:
        main()
    except Exception:
        sys.exit(1)
