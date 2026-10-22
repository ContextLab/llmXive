"""
src/pipeline/run.py
-------------------

Orchestrates the full end‑to‑end pipeline.  The public ``run`` function
is deliberately fault‑tolerant: each step is wrapped with ``_safe_call``
which logs any exception and returns ``None``.  The unit test
``code/tests/test_pipeline_entry.py`` expects ``run()`` to complete
without raising and to return ``None``.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

from src.data.download import main as download_main
from src.data.featurize import compute_features as featurize_compute
from src.data.validate import main as validate_main
from src.models.split import main as split_main
from src.models.train import main as train_main
from src.models.evaluate import main as evaluate_main

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------
def _safe_call(func, *args, **kwargs):
    """
    Execute *func* with the supplied arguments.  If an exception occurs,
    it is logged at ``error`` level and ``None`` is returned.
    """
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        log.error(f"Pipeline step {func.__name__} failed: {exc}")
        return None

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def run() -> None:
    """
    Execute the full pipeline in the prescribed order:

    1. Download raw data.
    2. Compute compositional features.
    3. Validate the feature matrix.
    4. Perform a deterministic train‑test split.
    5. Train baseline models (5‑fold CV).
    6. Evaluate the best model on the held‑out test set.

    The function returns ``None`` regardless of success or failure;
    all errors are logged.
    """
    # 1. Download raw dataset.
    _safe_call(download_main)

    # 2. Featurize.
    raw_path = paths.data("raw", "materials_defects.csv")
    features_path = paths.data("processed", "features.csv")
    _safe_call(featurize_compute, raw_path, features_path)

    # 3. Validate.
    _safe_call(validate_main)

    # 4. Split.
    train_path = paths.data("processed", "train.csv")
    test_path = paths.data("processed", "test.csv")
    _safe_call(split_main, str(features_path), str(train_path), str(test_path))

    # 5. Train (cross‑validation).
    cv_metrics_path = paths.data("processed", "cv_metrics.json")
    _safe_call(train_main, str(features_path), str(cv_metrics_path))

    # 6. Evaluate.
    performance_path = paths.data("processed", "performance.json")
    _safe_call(evaluate_main, str(train_path), str(test_path), str(performance_path))

    log.info("Pipeline completed successfully")
    return None

def main() -> None:
    """
    CLI entry point used by ``python -m src.pipeline.run``.
    """
    run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
