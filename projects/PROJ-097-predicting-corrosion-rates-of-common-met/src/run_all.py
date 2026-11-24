"""Wrapper module to expose the pipeline entry point as ``src.run_all``.

The original pipeline orchestrator lives in ``src.pipeline.run_all``.
Some run‑book scripts (e.g., ``code/run_pipeline.sh``) invoke
``python -m src.run_all``; this wrapper forwards the call to the real
implementation, ensuring the command succeeds without altering the
existing pipeline logic.
"""

from __future__ import annotations

import sys

from src.pipeline.ingest import main as ingest_main
from src.pipeline.features import main as features_main
from src.pipeline.vif import main as vif_main

def main(argv: list[str] | None = None) -> int:
    """Execute the full pipeline in the required order.

    Returns ``0`` on success, non‑zero otherwise.
    """
    # Ingestion step – creates raw CSV, provenance, and cleaned dataset.
    if ingest_main([]) != 0:
        return 1

    # Feature‑engineering step – builds interaction matrix.
    if features_main([]) != 0:
        return 1

    # VIF diagnostics – compute multicollinearity for base predictors.
    if vif_main([]) != 0:
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
