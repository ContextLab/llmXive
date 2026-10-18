from __future__ import annotations

import sys

from src.pipeline.ingest import main as ingest_main
from src.pipeline.features import main as features_main
from src.pipeline.vif import main as vif_main
from src.pipeline.train import main as train_main
from src.pipeline.evaluate import main as evaluate_main

def main(argv: list[str] | None = None) -> int:
    """Run the full pipeline end‑to‑end."""
    # 1. Ingest & clean raw data
    rc = ingest_main([])
    if rc != 0:
        return rc

    # 2. Engineer features
    rc = features_main([])
    if rc != 0:
        return rc

    # 3. Compute VIF diagnostics (base predictors only)
    rc = vif_main([])
    if rc != 0:
        return rc

    # 4. Train Full model and baseline, write first‑run metrics
    rc = train_main([])
    if rc != 0:
        return rc

    # 5. Evaluate (currently mirrors training metrics)
    rc = evaluate_main([])
    return rc

if __name__ == "__main__":
    sys.exit(main())
