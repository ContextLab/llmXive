import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.inspection import PartialDependenceDisplay

from config import load_paths
from utils.logging import get_logger

logger = get_logger(__name__)

def load_feature_names(data_path: Path) -> List[str]:
    """Load feature names from dataset.
    
    Args:
        data_path: Path to CSV file.
        
    Returns:
        List of feature names.
    """
    df = pd.read_csv(data_path)
    return [c for c in df.columns if c not in ["composition", "formation_energy"]]

def load_models(model_path: Path) -> Dict[str, Any]:
    """Load trained models.
    
    Args:
        model_path: Path to model files.
        
    Returns:
        Dictionary of models.
    """
    models = {}
    rf_path = model_path / "model_rf.pkl"
    if rf_path.exists():
        with open(rf_path, "rb") as f:
            models["rf"] = pickle.load(f)
    return models

def load_feature_ranking(ranking_path: Path) -> List[tuple]:
    """Load feature ranking from JSON.
    
    Args:
        ranking_path: Path to ranking JSON.
        
    Returns:
        List of (feature, importance) tuples.
    """
    with open(ranking_path, "r") as f:
        data = json.load(f)
    return data.get("feature_ranking", [])

def generate_pdp(
    model: Any,
    X: pd.DataFrame,
    features: List[str],
    output_path: Path
) -> None:
    """Generate Partial Dependence Plots.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        features: Features to plot.
        output_path: Output directory.
    """
    fig, axes = plt.subplots(1, len(features), figsize=(5 * len(features), 5))
    if len(features) == 1:
        axes = [axes]
    
    for ax, feat in zip(axes, features):
        disp = PartialDependenceDisplay.from_estimator(
            model, X, [feat], ax=ax
        )
        ax.set_title(feat)
    
    plt.tight_layout()
    plt.savefig(output_path / "pdp.png", dpi=150)
    plt.close()

def main() -> None:
    """Main entry point for plotting."""
    paths = load_paths()
    
    # Load data and model
    data_path = paths["data_processed"] / "computed_descriptors.csv"
    model_path = paths["data_evaluation"]
    ranking_path = paths["data_evaluation"] / "permutation_importance.json"
    
    models = load_models(model_path)
    if "rf" not in models:
        raise RuntimeError("Random Forest model not found")
    
    feature_names = load_feature_names(data_path)
    df = pd.read_csv(data_path)
    X = df[feature_names]
    
    # Load top features
    ranking = load_feature_ranking(ranking_path)
    top_features = [f[0] for f in ranking[:5]]
    
    # Generate PDP
    output_dir = paths["data_evaluation"]
    generate_pdp(models["rf"], X, top_features, output_dir)
    
    logger.info(f"Plots saved to {output_dir}")

if __name__ == "__main__":
    main()
