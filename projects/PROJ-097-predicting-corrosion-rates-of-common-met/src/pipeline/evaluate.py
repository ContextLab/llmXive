"""Evaluation wrapper for the corrosion‑rate pipeline (T004).

At the moment the heavy‑lifting is performed in ``train.py``; this module
simply re‑uses the same routine so that a separate ``evaluate`` step exists
for future extensions.  It writes the same ``first_run_metrics.json`` file
(overwrites if present) to satisfy the declared artifact.
"""

from __future__ import annotations

import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Re‑use the training routine – the metrics are identical for this simple
# implementation.
from .train import train_and_evaluate

def main(argv: list[str] | None = None) -> int:
    metrics = train_and_evaluate()
    out_path = paths.results("first_run_metrics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    log.info("Evaluation metrics written to %s", out_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
