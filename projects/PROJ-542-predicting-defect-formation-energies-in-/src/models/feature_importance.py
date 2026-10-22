"""
src/models/feature_importance.py
--------------------------------

Implements the feature‑importance extraction step for the pipeline.

This module:
  1. Loads the cross‑validation metrics JSON (``data/processed/performance.json``)
     to determine which model (Random Forest or Gradient Boosting) performed best
     (lowest mean RMSE).
  2. Deserialises the selected model from the ``models/`` directory.
  3. Extracts the ``feature_importances_`` attribute, normalises it to sum to 1,
     and orders the features by descending importance.
  4. Updates ``performance.json`` with a ``feature_importances`` array
     (each entry ``{\"feature\": <name>, \"importance\": <float>}``).
  5. Writes a SHA‑256 checksum for the updated JSON.
  6. Generates a bar‑chart figure (``figures/feature_importance.png``) that
     visualises the ranked importances.

The module is deliberately side‑effect‑free apart from the file writes
described above and can be invoked via the CLI wrapper in
``code/models/feature_importance.py`` or directly with ``python -m
src.models.feature_importance``.
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_performance(perf_path: Path) -> dict:
    """Load the performance JSON produced by the evaluation step."""
    if not perf_path.is_file():
        raise FileNotFoundError(f"Performance file not found at {perf_path}")
    with perf_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _select_best_model(cv_metrics: dict) -> str:
    """
    Choose the model identifier with the lowest mean RMSE.

    The ``cv_metrics`` dict follows the schema produced by
    ``src.models.train`` and looks like:
        {
            "RandomForest": {"rmse_mean": ..., ...},
            "GradientBoosting": {"rmse_mean": ..., ...}
        }
    Returns the model name as used for the pickle file
    (``RandomForest`` → ``rf_cv.pkl``, ``GradientBoosting`` → ``gb_cv.pkl``).
    """
    if not cv_metrics:
        raise ValueError("cv_metrics dictionary is empty")
    # Prefer the model with the smallest rmse_mean
    best = min(cv_metrics.items(), key=lambda kv: kv[1].get("rmse_mean", np.inf))
    model_name = best[0]
    log.info(f"Best model according to CV RMSE: {model_name}")
    return model_name

def _model_path_for_name(model_name: str) -> Path:
    """Map a model identifier to its pickle file."""
    mapping = {
        "RandomForest": Path("models/rf_cv.pkl"),
        "GradientBoosting": Path("models/gb_cv.pkl"),
    }
    if model_name not in mapping:
        raise ValueError(f"Unrecognised model name '{model_name}'")
    return mapping[model_name]

def _load_model(model_path: Path):
    """Deserialize a scikit‑learn model from disk."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    return joblib.load(model_path)

def _extract_and_normalise_importances(model, feature_names: list[str]) -> list[tuple[str, float]]:
    """
    Return a list of ``(feature_name, importance)`` tuples sorted
    descending, with importances normalised to sum to 1.
    """
    if not hasattr(model, "feature_importances_"):
        raise AttributeError("Model does not expose 'feature_importances_'")
    raw = np.array(model.feature_importances_, dtype=float)
    if raw.size != len(feature_names):
        raise ValueError(
            f"Feature‑importance vector length ({raw.size}) does not match number of feature columns ({len(feature_names)})"
        )
    total = raw.sum()
    if total == 0:
        raise ValueError("All feature importances are zero; cannot normalise")
    normed = raw / total
    paired = list(zip(feature_names, normed))
    paired.sort(key=lambda kv: kv[1], reverse=True)
    return paired

def _update_performance_json(perf_path: Path, importances: list[tuple[str, float]]) -> None:
    """Insert the ``feature_importances`` array into the performance JSON."""
    perf = _load_performance(perf_path)
    perf["feature_importances"] = [
        {"feature": name, "importance": float(imp)} for name, imp in importances
    ]
    # Write back (pretty‑printed for readability)
    with perf_path.open("w", encoding="utf-8") as f:
        json.dump(perf, f, indent=2)
    log.info(f"Updated performance JSON with {len(importances)} feature importances")

def _plot_feature_importances(importances: list[tuple[str, float]], out_path: Path) -> None:
    """Create a horizontal bar chart of feature importances."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    names, values = zip(*importances)  # unpack
    y_pos = np.arange(len(names))

    plt.figure(figsize=(10, max(4, len(names) * 0.4)))
    plt.barh(y_pos, values, align="center")
    plt.yticks(y_pos, names)
    plt.xlabel("Normalized Importance")
    plt.title("Feature Importance Ranking")
    plt.gca().invert_yaxis()  # highest at top
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    log.info(f"Feature‑importance figure saved to {out_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper used by ``python -m src.models.feature_importance``.

    No arguments are required – the function operates on the canonical
    artifact locations defined by the pipeline contract.
    """
    # Resolve canonical paths via llmxive_toolkit
    perf_path = paths.data("processed", "performance.json")
    features_path = paths.data("processed", "features.csv")
    fig_path = paths.figures("feature_importance.png")
    checksum_dir = paths.data("checksums")

    # ------------------------------------------------------------------
    # 1. Load performance JSON and decide which model to use.
    # ------------------------------------------------------------------
    perf = _load_performance(perf_path)
    cv_metrics = perf.get("cv_metrics")
    if not cv_metrics:
        raise KeyError("performance.json missing 'cv_metrics' section")
    best_model_name = _select_best_model(cv_metrics)

    # ------------------------------------------------------------------
    # 2. Load the selected model.
    # ------------------------------------------------------------------
    model_path = _model_path_for_name(best_model_name)
    model = _load_model(model_path)

    # ------------------------------------------------------------------
    # 3. Determine feature column order from the features CSV.
    # ------------------------------------------------------------------
    if not Path(features_path).is_file():
        raise FileNotFoundError(f"Features CSV not found at {features_path}")
    import pandas as pd

    df_features = pd.read_csv(features_path)
    # Exclude target and composition columns – the remaining columns are the descriptors.
    descriptor_cols = [c for c in df_features.columns if c not in {"formation_energy", "composition"}]
    if not descriptor_cols:
        raise ValueError("No descriptor columns detected in features CSV")

    # ------------------------------------------------------------------
    # 4. Extract, normalise and sort importances.
    # ------------------------------------------------------------------
    importances = _extract_and_normalise_importances(model, descriptor_cols)

    # ------------------------------------------------------------------
    # 5. Update performance JSON.
    # ------------------------------------------------------------------
    _update_performance_json(perf_path, importances)

    # ------------------------------------------------------------------
    # 6. Write checksum for the updated JSON.
    # ------------------------------------------------------------------
    checksum_dir.mkdir(parents=True, exist_ok=True)
    write_checksum(perf_path, checksum_dir)

    # ------------------------------------------------------------------
    # 7. Plot the ranking.
    # ------------------------------------------------------------------
    _plot_feature_importances(importances, fig_path)

    log.info("Feature‑importance step completed successfully.")

if __name__ == "__main__":
    main()
