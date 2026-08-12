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
from utils.io import load_dataframe_safely

logger = get_logger(__name__)

def load_feature_names(input_path: Path) -> List[str]:
    """
    Loads feature names from the dataset header.
    """
    df = pd.read_csv(input_path, nrows=0)
    return list(df.columns)

def load_models(models_dir: Path) -> Dict[str, Any]:
    """
    Loads pre-trained models from a directory.
    """
    models = {}
    for model_file in models_dir.glob("model_*.pkl"):
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
            name = model_file.stem.replace("model_", "")
            models[name] = model
    return models

def load_feature_ranking(ranking_path: Path) -> List[Dict[str, Any]]:
    """
    Loads feature ranking from a JSON file.
    """
    with open(ranking_path, 'r') as f:
        return json.load(f)

def generate_pdp(
    model: Any,
    X: pd.DataFrame,
    features: List[str],
    output_path: Path
) -> None:
    """
    Generates Partial Dependence Plots for given features.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    PartialDependenceDisplay.from_estimator(
        model, X, features, ax=ax
    )
    plt.title("Partial Dependence Plot")
    plt.savefig(output_path)
    plt.close()
    logger.info(f"PDP saved to {output_path}")

def main() -> None:
    """
    Main entry point for the plots script.
    """
    paths = load_paths()
    models_dir = paths['evaluation']
    data_path = paths['computed_descriptors']
    ranking_path = paths['feature_ranking']
    figures_dir = paths['figures']
    
    # Ensure figures directory exists
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Load models
    models = load_models(models_dir)
    if 'rf' not in models:
        logger.error("Random Forest model not found.")
        sys.exit(1)
    
    # Load data
    df = load_data(data_path)
    if df is None:
        logger.error("Failed to load data.")
        sys.exit(1)
    
    # Load feature ranking
    ranking = load_feature_ranking(ranking_path)
    top_features = [item['feature'] for item in ranking[:3]]
    
    # Generate PDPs
    feature_cols = [
        "mean_electronegativity", "variance_electronegativity",
        "mean_radius", "variance_radius",
        "mean_valence", "variance_valence",
        "mean_melting_point", "variance_melting_point",
        "mean_ionization_energy", "variance_ionization_energy"
    ]
    
    for i, feature in enumerate(top_features):
        if feature in feature_cols:
            output_path = figures_dir / f"pdp_{feature}.png"
            generate_pdp(models['rf'], df[feature_cols], [feature], output_path)
    
    logger.info("Plot generation complete.")

if __name__ == "__main__":
    from utils.logging import setup_logging
    setup_logging()
    main()
