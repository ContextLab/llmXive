"""Orchestrator for the corrosion‑rate prediction pipeline.

Executes the core stages in order:
1. Ingestion & cleaning
2. Feature engineering
3. VIF diagnostics
4. Model training & baseline evaluation

Each stage is invoked via its ``main`` entry point. If any stage
returns a non‑zero exit code the pipeline aborts and propagates that
code.
"""

from __future__ import annotations

import sys

from llmxive_toolkit import get_logger

# Import stage entry points.
from src.pipeline.ingest import main as ingest_main
from src.pipeline.features import main as features_main
from src.pipeline.vif import main as vif_main
from src.pipeline.train import main as train_main

log = get_logger(__name__)

def main(argv: list[str] | None = None) -> int:
    """Run the full pipeline end‑to‑end."""
    # 1. Ingestion
    rc = ingest_main([])
    if rc != 0:
        log.error("Ingestion step failed with code %s", rc)
        return rc

    # 2. Feature engineering
    rc = features_main([])
    if rc != 0:
        log.error("Feature‑engineering step failed with code %s", rc)
        return rc

    # 3. VIF diagnostics
    rc = vif_main([])
    if rc != 0:
        log.error("VIF step failed with code %s", rc)
        return rc

    # 4. Model training & baseline evaluation
    rc = train_main([])
    if rc != 0:
        log.error("Training step failed with code %s", rc)
        return rc

    log.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
