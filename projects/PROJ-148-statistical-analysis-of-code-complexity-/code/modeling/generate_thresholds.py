"""
generate_thresholds.py

This script derives practical threshold values for each complexity metric based on
the trained bug‑prediction model.  It loads the test dataset and the persisted model,
computes the predicted bug probability for every test instance, selects the subset
of instances with a predicted probability greater than or equal to 0.5, and then
calculates a representative threshold for each metric (the median value among the
selected instances).  The resulting thresholds are written to
``data/model/thresholds.csv`` with two columns: ``metric`` and ``threshold``.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Tuple, Union

import numpy as np
import pandas as pd

# Import helpers from the existing modelling evaluation module.
# These functions are part of the public API defined in the project specification.
from modeling.evaluate import load_test_data, load_model


def _ensure_dataframe(
    data: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.Series]]
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Normalise the output of ``load_test_data`` to a tuple ``(X, y)``.

    The ``load_test_data`` function may return either:
    * a single ``DataFrame`` that already contains the target column
      (named ``bug_label``), or
    * a tuple ``(X, y)`` where ``X`` is a ``DataFrame`` of features and ``y`` is a
      ``Series`` of labels.

    This helper abstracts away that difference so that the rest of the script can
    operate on a consistent ``(X, y)`` pair.
    """
    if isinstance(data, pd.DataFrame):
        if "bug_label" in data.columns:
            y = data["bug_label"]
            X = data.drop(columns=["bug_label"])
            return X, y
        # No explicit target column – treat the whole frame as features.
        return data, pd.Series(dtype=int)  # empty placeholder
    if isinstance(data, tuple) and len(data) == 2:
        X, y = data
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Features part of the tuple must be a pandas DataFrame")
        if not isinstance(y, (pd.Series, pd.DataFrame)):
            raise TypeError("Labels part of the tuple must be a pandas Series or DataFrame")
        if isinstance(y, pd.DataFrame):
            # If y is a DataFrame, flatten to a Series (assume single column)
            y = y.squeeze()
        return X, y
    raise TypeError(
        "load_test_data must return a DataFrame or a (DataFrame, Series) tuple"
    )


def _predict_probabilities(model, X: pd.DataFrame) -> np.ndarray:
    """
    Return the predicted probability of the positive class for each row in ``X``.

    The model may expose either ``predict_proba`` (standard for scikit‑learn
    classifiers) or ``decision_function``.  In the latter case we convert the raw
    scores to probabilities using the logistic (sigmoid) function.
    """
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
    elif hasattr(model, "decision_function"):
        raw = model.decision_function(X)
        probs = 1 / (1 + np.exp(-raw))
    else:
        raise AttributeError(
            "Model does not provide predict_proba or decision_function"
        )
    return probs


def generate_thresholds() -> None:
    """
    Compute and persist metric thresholds.

    The algorithm is:
    1. Load the test set and the trained model.
    2. Compute predicted bug probabilities.
    3. Keep rows where the probability is >= 0.5.
    4. For each metric column, compute the median value among the retained rows.
    5. Write a CSV file ``data/model/thresholds.csv`` with columns ``metric`` and
       ``threshold``.
    """
    # ------------------------------------------------------------------ #
    # 1. Load data and model
    # ------------------------------------------------------------------ #
    test_data = load_test_data()
    X_test, _ = _ensure_dataframe(test_data)

    model = load_model()

    # ------------------------------------------------------------------ #
    # 2. Predict probabilities
    # ------------------------------------------------------------------ #
    probs = _predict_probabilities(model, X_test)

    # Attach probabilities to a copy of the feature frame for easier filtering.
    df_with_probs = X_test.copy()
    df_with_probs["pred_prob"] = probs

    # ------------------------------------------------------------------ #
    # 3. Select high‑risk instances (probability >= 0.5)
    # ------------------------------------------------------------------ #
    high_risk = df_with_probs[df_with_probs["pred_prob"] >= 0.5]

    if high_risk.empty:
        raise RuntimeError(
            "No test instances have a predicted bug probability >= 0.5. "
            "Threshold generation aborted."
        )

    # ------------------------------------------------------------------ #
    # 4. Derive per‑metric thresholds (median of the high‑risk subset)
    # ------------------------------------------------------------------ #
    metric_columns = [col for col in X_test.columns if col != "pred_prob"]
    thresholds = {
        metric: high_risk[metric].median()
        for metric in metric_columns
    }

    thresholds_df = pd.DataFrame(
        list(thresholds.items()), columns=["metric", "threshold"]
    )

    # ------------------------------------------------------------------ #
    # 5. Persist the thresholds CSV
    # ------------------------------------------------------------------ #
    output_path = pathlib.Path("data/model/thresholds.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    thresholds_df.to_csv(output_path, index=False)

    print(f"Thresholds written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    generate_thresholds()
