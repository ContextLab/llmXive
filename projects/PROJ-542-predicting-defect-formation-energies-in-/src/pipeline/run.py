"""
src/pipeline/run.py
-------------------

This module provides the public entry point for the project's pipeline.
It orchestrates the full end‑to‑end workflow required by the quick‑start
guide: download, checksum generation, featurisation, validation,
deterministic train/test split, model training (5‑fold GroupKFold CV),
and final evaluation.  All steps are invoked programmatically using the
``main`` functions exposed by the respective sub‑modules, so the pipeline
can be executed with ``python -m src.pipeline.run`` and the test suite
can import the module and call ``run()`` directly.

The function returns ``None`` and never raises; any unexpected error is
logged and re‑raised as a ``RuntimeError`` to keep the contract simple.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Import the entry‑point functions from the sub‑modules.
from src.data.download import main as download_main
from src.utils.checksum_all import main as checksum_main
from src.data.featurize import compute_features
from src.data.validate import main as validate_main
from src.models.split import main as split_main
from src.models.train import main as train_main
from src.models.evaluate import main as evaluate_main

log = get_logger(__name__)

def run() -> None:
    """
    Execute the complete pipeline.

    The steps are performed in the order required by the quick‑start
    documentation.  All intermediate artefacts are written to the
    ``data/`` folder using the ``paths`` helper, which creates any missing
    directories automatically.
    """
    try:
        # 1️⃣ Download the raw defect dataset (or use the fallback CSV).
        log.info("Running data download step")
        download_main()

        # 2️⃣ Generate SHA‑256 checksums for raw and processed artefacts.
        log.info("Generating checksums")
        checksum_main()

        # 3️⃣ Featurise the raw data.
        log.info("Computing compositional features")
        raw_path = paths.data("raw", "materials_defects.csv")
        features_path = paths.data("processed", "features.csv")
        compute_features(raw_path, features_path)

        # 4️⃣ Validate the feature matrix (size, power analysis, etc.).
        log.info("Running dataset validation")
        validate_main()

        # 5️⃣ Deterministic train/test split.
        log.info("Splitting dataset into train and test")
        train_path = paths.data("processed", "train.csv")
        test_path = paths.data("processed", "test.csv")
        split_main(str(features_path), str(train_path), str(test_path))

        # 6️⃣ 5‑fold GroupKFold cross‑validation on the training split.
        log.info("Training models with cross‑validation")
        cv_metrics_path = paths.data("processed", "cv_metrics.json")
        train_main(str(train_path), str(cv_metrics_path))

        # 7️⃣ Final evaluation on the held‑out test set.
        log.info("Evaluating the selected model on the test set")
        performance_path = paths.data("processed", "performance.json")
        evaluate_main(str(train_path), str(test_path), str(performance_path))

        # 8️⃣ Success message required by the quick‑start integration test.
        print("Pipeline completed successfully")
        log.info("Pipeline run completed successfully")
    except Exception as exc:
        log.error(f"Pipeline execution failed: {exc}")
        raise RuntimeError("Pipeline execution failed") from exc

def main() -> None:
    """
    CLI entry point used when the module is executed with
    ``python -m src.pipeline.run``.
    """
    run()

if __name__ == "__main__":
    main()
