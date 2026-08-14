import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.inspection import PartialDependenceDisplay
from sklearn.ensemble import RandomForestRegressor

from config import load_paths

logger = logging.getLogger(__name__)


def load_feature_names(input_path: Path) -> List[str]:
    """Load feature names from the processed dataset."""
    df = pd.read_csv(input_path)
    exclude = [
        "formula",
        "formula_pretty",
        "formation_energy_per_atom",
        "dominant_element",
    ]
    return [c for c in df.columns if c not in exclude]


def load_models(rf_path: Path) -> RandomForestRegressor:
    """Load the Random Forest model."""
    with open(rf_path, "rb") as f:
        return pickle.load(f)


def load_feature_ranking(rank_path: Path) -> List[Dict[str, Any]]:
    """Load feature ranking from JSON."""
    with open(rank_path, "r") as f:
        return json.load(f)


def generate_pdp(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    features: List[str],
    output_dir: Path,
) -> None:
    """Generate Partial Dependence Plots for top features."""
    fig, axes = plt.subplots(1, len(features), figsize=(5 * len(features), 4))
    if len(features) == 1:
        axes = [axes]

    for i, feature in enumerate(features):
        PartialDependenceDisplay.from_estimator(
            model, X, features=[feature], ax=axes[i]
        )
        axes[i].set_title(feature)

    plt.tight_layout()
    plot_path = output_dir / "pdp_top_features.png"
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved PDP plot to {plot_path}")


def main() -> None:
    """Main entry point for plot generation."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    # Load model and data
    rf_path = paths["data_evaluation"] / "model_rf.pkl"
    model = load_models(rf_path)

    input_path = paths["data_processed"] / "computed_descriptors.csv"
    df = pd.read_csv(input_path)

    feature_names = load_feature_names(input_path)
    X = df[feature_names]

    # Load ranking
    rank_path = paths["data_evaluation"] / "feature_ranking.json"
    ranking = load_feature_ranking(rank_path)
    top_features = [item["feature"] for item in ranking[:5]]

    # Generate PDP
    generate_pdp(model, X, top_features, paths["data_evaluation"])

    # ALE and non-linearity check (simplified for now)
    ale_metrics = {}
    for feat in top_features:
        # Simple quadratic fit to detect non-linearity
        vals = X[feat].values
        y_vals = model.predict(X)
        # Fit linear
        coeffs_lin = np.polyfit(vals, y_vals, 1)
        pred_lin = np.polyval(coeffs_lin, vals)
        r2_lin = 1 - np.sum((y_vals - pred_lin) ** 2) / np.sum(
            (y_vals - np.mean(y_vals)) ** 2
        )

        # Fit quadratic
        coeffs_quad = np.polyfit(vals, y_vals, 2)
        pred_quad = np.polyval(coeffs_quad, vals)
        r2_quad = 1 - np.sum((y_vals - pred_quad) ** 2) / np.sum(
            (y_vals - np.mean(y_vals)) ** 2
        )

        non_lin_score = abs(r2_quad - r2_lin)
        ale_metrics[feat] = {
            "non_linearity_score": float(non_lin_score),
            "non_linearity_verified": non_lin_score > 0.5,
        }

    # Save ALE metrics
    ale_path = paths["data_evaluation"] / "ale_metrics.json"
    with open(ale_path, "w") as f:
        json.dump(ale_metrics, f, indent=2)

    logger.info("Plot generation complete")


if __name__ == "__main__":
    main()
