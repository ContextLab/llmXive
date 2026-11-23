"""
Model Evaluation Script
-----------------------

This module provides functionality to evaluate trained regression models
(Random Forest and Gradient Boosting) on the processed dataset, compute
R² scores, and perform pairwise statistical comparison using a paired
t‑test. The results are written to ``data/results/model_comparison.json``.

The script is intended to be executed directly::

    python -m code.models.evaluate

or via the ``main`` function imported elsewhere.

It relies on the following project conventions:

* Processed feature matrix and target are stored in
  ``data/processed/processed_dataset.csv``. The CSV must contain a column
  named ``target`` (the name is read from ``data/results/target_decision.json``
  if present, falling back to ``target``).

* Trained model files are pickled and live under ``data/models/`` with
  filenames ending in ``_model.pkl`` (e.g. ``rf_model.pkl``).

* The output JSON follows the schema expected by downstream contract
  tests (see ``contracts/model_comparison.schema.yaml``).

The implementation purposefully avoids any synthetic data generation;
it raises clear exceptions if required inputs are missing, ensuring
that the pipeline fails loudly in the absence of real data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import pandas as pd
from scipy import stats
from sklearn.metrics import r2_score

from utils.logger import get_pipeline_logger, log_error, log_info

LOGGER = get_pipeline_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def load_target_name() -> str:
    """
    Load the target column name from ``data/results/target_decision.json``.
    If the file does not exist or does not contain a ``target`` key,
    fall back to the default column name ``target``.
    """
    target_decision_path = Path("data/results/target_decision.json")
    if target_decision_path.is_file():
        try:
            with target_decision_path.open("r", encoding="utf-8") as f:
                decision = json.load(f)
            if isinstance(decision, dict) and "target" in decision:
                return decision["target"]
        except Exception as exc:  # pragma: no cover
            log_error(f"Failed to read target decision file: {exc}")
    # Default fallback
    return "target"


def load_processed_dataset() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the processed dataset CSV and split into features (X) and target (y).

    Expected location: ``data/processed/processed_dataset.csv``.
    The target column name is obtained via :func:`load_target_name`.
    """
    dataset_path = Path("data/processed/processed_dataset.csv")
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Processed dataset not found at {dataset_path}. "
            "Ensure that the data preprocessing pipeline has been run."
        )
    df = pd.read_csv(dataset_path)
    target_col = load_target_name()
    if target_col not in df.columns:
        raise KeyError(
            f"Target column '{target_col}' not found in processed dataset."
        )
    y = df[target_col]
    X = df.drop(columns=[target_col])
    return X, y


def discover_model_files() -> List[Path]:
    """
    Return a list of all pickled model files under ``data/models`` that end
    with ``_model.pkl``.
    """
    models_dir = Path("data/models")
    if not models_dir.is_dir():
        raise FileNotFoundError(
            f"Models directory not found at {models_dir}. "
            "Run the model training tasks first."
        )
    model_files = sorted(models_dir.glob("*_model.pkl"))
    if not model_files:
        raise FileNotFoundError(
            f"No model files matching '*_model.pkl' found in {models_dir}."
        )
    return model_files


def load_model(model_path: Path):
    """
    Load a scikit‑learn model from a pickle file using ``joblib.load``.
    """
    try:
        model = joblib.load(model_path)
        return model
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to load model from {model_path}: {exc}") from exc


def evaluate_models() -> Dict:
    """
    Evaluate each discovered model on the processed test set, compute R²,
    and perform pairwise paired t‑tests between model predictions.

    Returns
    -------
    dict
        Dictionary with the following structure::

            {
                "models": {
                    "<model_name>": {"r2": <float>, "predictions_path": "<path>"},
                    ...
                },
                "pairwise_ttest": {
                    "<model_a>_vs_<model_b>": {
                        "t_stat": <float>,
                        "p_value": <float>
                    },
                    ...
                }
            }
    """
    X, y = load_processed_dataset()
    model_files = discover_model_files()

    results = {"models": {}, "pairwise_ttest": {}}
    predictions: Dict[str, pd.Series] = {}

    for model_path in model_files:
        model_name = model_path.stem.replace("_model", "")
        log_info(f"Evaluating model '{model_name}' from {model_path}")
        model = load_model(model_path)

        # Predict
        try:
            y_pred = model.predict(X)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                f"Model '{model_name}' failed to predict: {exc}"
            ) from exc

        # Store predictions for later paired tests
        predictions[model_name] = pd.Series(y_pred, index=y.index)

        # Compute R²
        r2 = r2_score(y, y_pred)
        results["models"][model_name] = {"r2": r2}
        log_info(f"Model '{model_name}' R²: {r2:.4f}")

    # Pairwise paired t‑test
    model_names = list(predictions.keys())
    for i in range(len(model_names)):
        for j in range(i + 1, len(model_names)):
            a = model_names[i]
            b = model_names[j]
            diff = predictions[a] - predictions[b]
            t_stat, p_val = stats.ttest_rel(predictions[a], predictions[b])
            key = f"{a}_vs_{b}"
            results["pairwise_ttest"][key] = {
                "t_stat": t_stat,
                "p_value": p_val,
            }
            log_info(
                f"Paired t‑test {a} vs {b}: t={t_stat:.4f}, p={p_val:.4g}"
            )

    return results


def write_report(report: Dict, output_path: Path):
    """
    Write the evaluation report as pretty‑printed JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    log_info(f"Model comparison report written to {output_path}")


def main():
    """
    Entry point for the script. Executes the evaluation pipeline and
    writes ``data/results/model_comparison.json``.
    """
    try:
        report = evaluate_models()
        output_file = Path("data/results/model_comparison.json")
        write_report(report, output_file)
    except Exception as exc:  # pragma: no cover
        log_error(f"Model evaluation failed: {exc}")
        raise


if __name__ == "__main__":
    # When executed as a script ``python -m code.models.evaluate``.
    main()