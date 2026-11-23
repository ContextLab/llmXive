"""Orchestrates the full pipeline end‑to‑end.

This entry point runs the required stages in the correct order:
1. Data ingestion & cleaning
2. Feature engineering
3. Group‑aware splitting
4. VIF diagnostics
5. Model training (Full & Null) and baseline comparison
6. Interaction‑gain permutation test (produces ``interaction_gain_permutation_test.json``)
7. Conditional permutation‑importance (produces ``interaction_permutation_importance.json``)
8. SHAP interaction analysis (produces figures and rankings)
9. Hyper‑parameter stability analysis
10. Summary report generation

Each stage is executed via its ``main`` function; the first non‑zero
exit code aborts the pipeline.
"""

from __future__ import annotations

import sys
from typing import List

from llmxive_toolkit import get_logger

# Import the stage entry points.
from src.pipeline.ingest import main as ingest_main
from src.pipeline.features import main as features_main
from src.pipeline.split import main as split_main
from src.pipeline.vif import main as vif_main
from src.pipeline.train import main as train_main
from src.pipeline.evaluate import main as evaluate_main

log = get_logger(__name__)

def _run_stage(name: str, func, args: List[str] | None = None) -> int:
    """Execute a pipeline stage and log its outcome."""
    args = args or []
    log.info("Running stage: %s", name)
    try:
        rc = func(args)
    except Exception as exc:  # pragma: no cover – unexpected failure
        log.exception("Stage %s raised an exception: %s", name, exc)
        return 1
    if rc != 0:
        log.error("Stage %s exited with code %s", name, rc)
    else:
        log.info("Stage %s completed successfully", name)
    return rc

def main(argv: List[str] | None = None) -> int:
    """Execute the full pipeline in order."""
    # The ``argv`` argument is ignored; each sub‑module parses its own CLI.
    stages = [
        ("ingest", ingest_main),
        ("features", features_main),
        ("split", split_main),
        ("vif", vif_main),
        ("train", train_main),
        ("evaluate", evaluate_main),
    ]

    for name, func in stages:
        rc = _run_stage(name, func)
        if rc != 0:
            return rc
    return 0

if __name__ == "__main__":
    sys.exit(main())