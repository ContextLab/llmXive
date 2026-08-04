"""
Imbalance analysis module.
Calculates Target Imbalance Score (Gini) and Compositional Imbalance Score.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.stats import gini

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"

INPUT_FILE = PROCESSED_DIR / "descriptors.csv"
OUTPUT_FILE = PROCESSED_DIR / "imbalance_metrics.json"

def load_data() -> pd.DataFrame:
    """Loads the processed descriptors."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Descriptors file not found: {INPUT_FILE}. Run code/descriptors.py first.")
    return pd.read_csv(INPUT_FILE)

def calculate_gini(values: np.ndarray) -> float:
    """Calculates the Gini coefficient for a 1D array of values."""
    if len(values) == 0:
        return 0.0
    # Gini calculation: 2 * sum(i * x_i) / (n * sum(x)) - (n+1)/n
    # Using scipy.stats.gini if available, else manual
    try:
        return float(gini(values))
    except Exception:
        # Fallback manual calculation
        sorted_vals = np.sort(values)
        n = len(sorted_vals)
        index = np.arange(1, n + 1)
        return float((2 * np.sum(index * sorted_vals)) / (n * np.sum(sorted_vals)) - (n + 1) / n)

def calculate_target_imbalance_score(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates the Gini coefficient of the target values.
    Assumes the last numeric column is the target.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Skip descriptor columns if they are named 'mean_...', 'min_...' etc.
    # Assuming the target is named 'target' or is the last column
    target_col = None
    if 'target' in numeric_cols:
        target_col = 'target'
    elif 'property_value' in numeric_cols:
        target_col = 'property_value'
    else:
        target_col = numeric_cols[-1]

    values = df[target_col].dropna().values
    if len(values) < 100:
        logger.warning(f"Target values count ({len(values)}) < 100. Skipping imbalance calculation.")
        return {"score": 0.0, "samples": len(values), "skipped": True}

    score = calculate_gini(values)
    return {"score": score, "samples": len(values), "skipped": False}

def calculate_compositional_imbalance_score(df: pd.DataFrame) -> float:
    """
    Calculates the Compositional Imbalance Score using Gini of K-Means cluster distances.
    k=50, Euclidean distance.
    """
    # Select descriptor columns (exclude formula, target, etc.)
    # Assuming descriptor columns start with 'mean_', 'min_', etc. or are all numeric except target
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    target_col = 'target' if 'target' in numeric_cols else (numeric_cols[-1] if numeric_cols else None)
    feature_cols = [c for c in numeric_cols if c != target_col]

    if not feature_cols:
        logger.warning("No feature columns found for compositional imbalance.")
        return 0.0

    X = df[feature_cols].dropna().values
    if len(X) < 50:
        logger.warning("Not enough samples for K-Means clustering.")
        return 0.0

    # K-Means clustering
    k = min(50, len(X))
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Calculate distances to cluster centers
    distances = np.array([np.linalg.norm(X[i] - kmeans.cluster_centers_[labels[i]]) for i in range(len(X))])
    
    # Gini of distances
    return calculate_gini(distances)

def analyze_all_properties(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes imbalance for the dataset."""
    target_score = calculate_target_imbalance_score(df)
    comp_score = calculate_compositional_imbalance_score(df)
    
    return {
        "target_imbalance_score": target_score,
        "compositional_imbalance_score": comp_score
    }

def save_results(results: Dict[str, Any]):
    """Saves results to JSON."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Imbalance metrics saved to {OUTPUT_FILE}")

def main():
    """Main entry point for imbalance analysis."""
    logger.info("Starting imbalance analysis...")
    df = load_data()
    results = analyze_all_properties(df)
    save_results(results)
    logger.info("Imbalance analysis completed.")

if __name__ == "__main__":
    main()
