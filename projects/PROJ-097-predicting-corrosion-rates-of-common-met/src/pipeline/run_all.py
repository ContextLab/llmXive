"""Orchestrator for the corrosion‑rate prediction pipeline.

The orchestrator coordinates ingestion, feature engineering, VIF
diagnostics, split generation, and model training.  All steps must
succeed for the pipeline to be considered successful.
"""

from __future__ import annotations

import sys
from typing import List

from llmxive_toolkit import get_logger

# Import sub‑module entry points.
from src.pipeline.ingest import main as ingest_main
from src.pipeline.features import main as features_main
from src.pipeline.vif import main as vif_main
from src.pipeline.split import main as split_main
from src.pipeline.train import main as train_main

log = get_logger(__name__)

_STEPS: List[tuple[str, callable]] = [
    ("ingest", ingest_main),
    ("features", features_main),
    ("vif", vif_main),
    ("split", split_main),
    ("train", train_main),
]

def main(argv: List[str] | None = None) -> int:
    """Run the full pipeline end‑to‑end.

    Returns ``0`` on success; otherwise returns the first non‑zero
    exit code encountered.
    """
    for name, step_fn in _STEPS:
        log.info("Running pipeline step: %s", name)
        rc = step_fn([])
        if rc != 0:
            log.error("Step %s failed with exit code %d", name, rc)
            return rc
    log.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())