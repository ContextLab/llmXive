"""
Permutation test for the best model.

This script loads the best trained model (as recorded in
``models/best_model.json``), evaluates it on the test split, and then
performs exactly 1,000 shuffles of the target variable to obtain an
empirical p‑value for the observed R² score.  The resulting p‑value is
written to ``results/permutation_p_value.txt`` as a plain text number.

The script follows the conventions used throughout the project:
* Paths are created via ``llmxive_toolkit.paths`` which also ensures the
  parent directories exist.
* Logging is performed with the project's logger.
* All random operations use a fixed seed (42) for reproducibility.
* If the test split is missing or empty, the cleaned dataset is used as a
  fallback (mirroring the behaviour of ``code/evaluate.py``).
"""
import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from llmxive_toolkit import paths, get_logger

LOG = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_best_model_info() -> dict:
    """
    Load ``models/best_model.json`` and return its contents.

    Expected keys (at minimum):
        * ``model_path`` – path to the pickle file of the best model
          (relative to the project root).  If the key is missing, the
          function attempts to infer the model file from ``model_type``.
    """
    best_path = Path("models", "best_model.json")
    if not best_path.is_file():
        raise FileNotFoundError(f"Best‑model descriptor not found at {best_path}")
    with best_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data


def _infer_model_path(best_info: dict) -> Path:
    """
    Determine the pickle file that stores the best model.

    Preference is given to the explicit ``model_path`` entry.  If it is
    absent, we locate a model file whose inferred type matches
    ``best_model_type``.
    """
    if "model_path" in best_info:
        return Path(best_info["model_path"])
    # Fallback: search for a pickle whose name contains the model type.
    model_type = best_info.get("best_model_type", "").lower()
    candidates = list(Path("models").glob("*.pkl"))
    for cand in candidates:
        if model_type in cand.stem.lower():
            return cand
    raise FileNotFoundError(
        "Could not infer the best model file – please ensure "
        "'model_path' is present in models/best_model.json"
    )


def _load_model(model_path: Path):
    """
    Load a scikit‑learn model from a pickle file.
    """
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with model_path.open("rb") as fh:
        model = pickle.load(fh)
    return model


def _load_test_dataframe() -> pd.DataFrame:
    """
    Load the test split.  If it does not exist or is empty, fall back to
    the cleaned dataset (the same data used during training).  This mirrors
    the behaviour of ``code/evaluate.py``.
    """
    test_path = Path("data", "split", "test.csv")
    if test_path.is_file():
        df = pd.read_csv(test_path)
        if not df.empty:
            LOG.info(f"Loaded test split from {test_path} (rows={len(df)})")
            return df
    # Fallback to the cleaned data
    cleaned_path = Path("data", "cleaned", "cleaned.csv")
    if not cleaned_path.is_file():
        raise FileNotFoundError(
            f"Neither test split nor cleaned data could be found "
            f"(tried {test_path} and {cleaned_path})"
        )
    df = pd.read_csv(cleaned_path)
    LOG.warning(
        f"Test split empty or missing – falling back to cleaned data "
        f"({cleaned_path}, rows={len(df)})"
    )
    return df


def _separate_features_target(df: pd.DataFrame):
    """
    Split a DataFrame into features ``X`` and target ``y``.
    The target column is assumed to be ``adhesion_strength_mj_m2``.
    """
    target_col = "adhesion_strength_mj_m2"
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in DataFrame")
    y = df[target_col].to_numpy()
    X = df.drop(columns=[target_col])
    return X, y


# ----------------------------------------------------------------------
# Main permutation‑test routine
# ----------------------------------------------------------------------


def main() -> None:
    LOG.info("Starting permutation test (1,000 shuffles)")

    # 1. Load best model information and the model itself
    best_info = _load_best_model_info()
    model_path = _infer_model_path(best_info)
    LOG.info(f"Loading best model from {model_path}")
    model = _load_model(model_path)

    # 2. Load test data and obtain features / target
    df_test = _load_test_dataframe()
    X_test, y_test = _separate_features_target(df_test)

    # 3. Compute the observed R² on the (unshuffled) test set
    y_pred = model.predict(X_test)
    observed_r2 = r2_score(y_test, y_pred)
    LOG.info(f"Observed R² on test set: {observed_r2:.6f}")

    # 4. Generate the null distribution by permuting the target
    n_shuffles = 1000
    rng = np.random.default_rng(42)  # deterministic shuffling
    null_r2s = np.empty(n_shuffles, dtype=float)

    for i in range(n_shuffles):
        y_perm = rng.permutation(y_test)
        null_r2 = r2_score(y_perm, y_pred)
        null_r2s[i] = null_r2
        if (i + 1) % 200 == 0:
            LOG.debug(f"Completed {i + 1}/{n_shuffles} shuffles")

    # 5. Compute the empirical p‑value
    # Use the common “+1 / (n+1)” adjustment to avoid a p‑value of zero.
    count_ge = np.sum(null_r2s >= observed_r2)
    p_value = (count_ge + 1) / (n_shuffles + 1)
    LOG.info(f"Permutation test p‑value: {p_value:.6f}")

    # 6. Write the p‑value to the required location
    out_path = paths.results("permutation_p_value.txt")
    out_path.write_text(f"{p_value:.6f}\n", encoding="utf-8")
    LOG.info(f"P‑value written to {out_path}")

    # Optional: store the p‑value back into the best‑model JSON for downstream
    # steps that may wish to read it from a single source.
    best_info["permutation_p_value"] = p_value
    best_path = Path("models", "best_model.json")
    best_path.write_text(json.dumps(best_info, indent=2), encoding="utf-8")
    LOG.debug(f"Updated {best_path} with permutation p‑value")

    LOG.info("Permutation test completed successfully")


if __name__ == "__main__":
    main()
