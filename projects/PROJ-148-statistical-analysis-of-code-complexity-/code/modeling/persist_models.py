"""
Persist trained model artifacts and evaluation metrics to disk.

This script is part of the US2 pipeline. It invokes the
``run_training_pipeline`` function from ``modeling.pipeline`` which
is responsible for training the primary (L1‑logistic regression) and
alternative (Random Forest) models and returning a dictionary that
contains the trained model objects together with any evaluation
metrics.

The script serialises the models with ``joblib`` and writes the
metrics as JSON.  By default the artifacts are stored under
``data/model`` but a custom output directory can be supplied via the
``--output-dir`` command‑line argument – this is useful for the test
suite which writes to a temporary location.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import joblib

# Import the training pipeline entry point.
# The project’s import layout expects ``code`` to be on ``sys.path``.
from modeling.pipeline import run_training_pipeline

def _persist_model(model: Any, path: Path) -> None:
    """Serialise a model object to ``path`` using joblib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)

def _persist_metrics(metrics: Dict[str, Any], path: Path) -> None:
    """Write evaluation metrics as pretty‑printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)

def main(output_dir: str = "data/model") -> None:
    """
    Run the training pipeline and persist its outputs.

    Parameters
    ----------
    output_dir: str
        Directory where ``primary.pkl``, ``alternative.pkl`` and
        ``evaluation_metrics.json`` will be written.
    """
    # Execute the full training pipeline.
    pipeline_output = run_training_pipeline()

    # Expected keys – the pipeline implementation guarantees their presence.
    primary_model = pipeline_output.get("primary_model")
    alternative_model = pipeline_output.get("alternative_model")
    metrics = pipeline_output.get("metrics", {})

    out_path = Path(output_dir)

    if primary_model is not None:
        _persist_model(primary_model, out_path / "primary.pkl")
    else:
        raise RuntimeError("Primary model was not returned by the training pipeline.")

    if alternative_model is not None:
        _persist_model(alternative_model, out_path / "alternative.pkl")
    else:
        raise RuntimeError("Alternative model was not returned by the training pipeline.")

    _persist_metrics(metrics, out_path / "evaluation_metrics.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Persist trained models and evaluation metrics."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/model",
        help="Directory to store model artifacts (default: data/model).",
    )
    args = parser.parse_args()
    main(output_dir=args.output_dir)