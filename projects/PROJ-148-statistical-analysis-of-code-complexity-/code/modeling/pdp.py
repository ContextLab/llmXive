"""Partial Dependence Plot (PDP) generation for the top three important metrics.

This script loads the primary trained model and the test dataset, retrieves the
feature importance scores, selects the three most important metrics, and generates
partial dependence plots for each of them. The resulting PNG files are written to
``data/model/`` with filenames ``pdp_<feature>.png``.

The script can be executed directly:

    python code/modeling/pdp.py

It relies on the existing project API:
  * :func:`modeling.evaluate.load_model`
  * :func:`modeling.evaluate.load_test_data`
  * :func:`modeling.importance.get_importance`

The required third‑party packages (scikit‑learn, matplotlib) are already listed in
``requirements.txt``.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.inspection import PartialDependenceDisplay

# Project‑specific imports – these names are defined in the existing API surface.
from modeling.evaluate import load_model, load_test_data
from modeling.importance import get_importance

def ensure_dir(path: Path) -> None:
    """Create ``path`` if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)

def generate_partial_dependence_plots(
    model,
    X,
    features: list[str],
    output_dir: Path,
) -> None:
    """Generate and save a PDP for each feature in ``features``."""
    ensure_dir(output_dir)

    for feature in features:
        # ``PartialDependenceDisplay`` handles both single and multiple features.
        display = PartialDependenceDisplay.from_estimator(
            estimator=model,
            X=X,
            features=[feature],
            kind="average",
        )
        # The display creates its own figure; we simply save it.
        fig = display.figure_
        fig_path = output_dir / f"pdp_{feature}.png"
        fig.savefig(fig_path, bbox_inches="tight")
        plt.close(fig)  # Release memory.

def main() -> None:
    """Entry point for the PDP generation script."""
    # Load the primary model and the test split.
    model = load_model()  # Expected to return a fitted sklearn estimator.
    X_test, _ = load_test_data()  # We only need the features for PDPs.

    # Retrieve feature importance scores (e.g., coefficients or Gini importances).
    importance_dict = get_importance()
    if not importance_dict:
        raise RuntimeError("Feature importance dictionary is empty.")

    # Sort features by descending importance and pick the top three.
    top_features = sorted(
        importance_dict,
        key=importance_dict.get,
        reverse=True,
    )[:3]

    if not top_features:
        raise RuntimeError("No features available for PDP generation.")

    output_directory = Path("data/model")
    generate_partial_dependence_plots(
        model=model,
        X=X_test,
        features=top_features,
        output_dir=output_directory,
    )
    print(f"PDPs generated for features: {', '.join(top_features)}")
    print(f"Saved to directory: {output_directory.resolve()}")

if __name__ == "__main__":
    main()