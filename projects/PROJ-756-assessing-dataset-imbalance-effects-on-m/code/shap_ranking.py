"""
T038: Rank top features for skewed and balanced models, calculate mean rank shift,
and write results to results/shap_analysis/rank_shift.csv.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shap_compute import compute_shap_values  # Not strictly needed if loading .npy, but good for context

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_shap_values(filepath: Path) -> np.ndarray:
    """Load SHAP values from .npy file."""
    if not filepath.exists():
        raise FileNotFoundError(f"SHAP values file not found: {filepath}")
    return np.load(filepath)

def get_feature_names_from_schema(schema_path: Path) -> list:
    """Load feature names from the descriptor schema JSON."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Descriptor schema file not found: {schema_path}")
    
    import json
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Expected structure based on T007b: {"columns": ["feat1", "feat2", ...]}
    if 'columns' in schema:
        return schema['columns']
    else:
        # Fallback: try to infer from first key if it's a dict of features
        keys = list(schema.keys())
        if keys and isinstance(schema[keys[0]], dict) and 'features' in schema[keys[0]]:
            return schema[keys[0]]['features']
        raise ValueError("Could not extract feature names from schema. Expected 'columns' key.")

def calculate_mean_rank_shift(ranked_features: list, rank_dict: dict) -> float:
    """
    Calculate mean rank shift for a list of features.
    Ties are broken by average rank (handled by pandas rank method).
    """
    shifts = []
    for feat in ranked_features:
        if feat in rank_dict:
            shifts.append(rank_dict[feat])
        else:
            # Feature not in top N, treat as rank = N+1 or similar? 
            # For this task, we only care about features in the top list.
            shifts.append(0) 
    return np.mean(shifts)

def main():
    logger.info("Starting T038: SHAP Rank Shift Analysis")
    
    # Paths
    shap_dir = PROJECT_ROOT / "results" / "shap_analysis"
    shap_skewed_path = shap_dir / "shap_skewed.npy"
    shap_balanced_path = shap_dir / "shap_balanced.npy"
    schema_path = PROJECT_ROOT / "data" / "processed" / "descriptor_schema.json"
    output_path = shap_dir / "rank_shift.csv"

    # Ensure output directory exists
    shap_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load SHAP values
    logger.info(f"Loading SHAP values from {shap_skewed_path}")
    shap_skewed = load_shap_values(shap_skewed_path)
    logger.info(f"Loading SHAP values from {shap_balanced_path}")
    shap_balanced = load_shap_values(shap_balanced_path)

    # 2. Load feature names
    logger.info(f"Loading feature names from {schema_path}")
    feature_names = get_feature_names_from_schema(schema_path)
    n_features = len(feature_names)
    
    if shap_skewed.shape[1] != n_features:
        logger.warning(f"Feature count mismatch: SHAP has {shap_skewed.shape[1]}, Schema has {n_features}. Using SHAP columns.")
        n_features = shap_skewed.shape[1]
        feature_names = [f"feature_{i}" for i in range(n_features)]

    # 3. Calculate Mean Absolute SHAP Values (Feature Importance)
    # Mean |SHAP| across all samples
    importance_skewed = np.mean(np.abs(shap_skewed), axis=0)
    importance_balanced = np.mean(np.abs(shap_balanced), axis=0)

    # 4. Rank Features
    # Higher importance -> Lower rank number (1 is best)
    # Use 'average' method for ties as requested
    ranks_skewed = pd.Series(importance_skewed).rank(ascending=False, method='average')
    ranks_balanced = pd.Series(importance_balanced).rank(ascending=False, method='average')

    # 5. Calculate Rank Shift
    rank_shift = ranks_skewed - ranks_balanced

    # 6. Prepare DataFrame
    # Sort by rank_shift magnitude or just list all? 
    # Task says "Rank top features... calculate mean rank shift... and write rank_shift.csv"
    # Usually implies listing all features or top N. Let's list all for completeness, 
    # sorted by absolute shift descending to highlight changes.
    df = pd.DataFrame({
        'feature': feature_names,
        'rank_skewed': ranks_skewed.values,
        'rank_balanced': ranks_balanced.values,
        'rank_shift': rank_shift.values
    })

    # Sort by absolute rank shift descending to see most affected features first
    df['abs_rank_shift'] = df['rank_shift'].abs()
    df = df.sort_values(by='abs_rank_shift', ascending=False).drop(columns=['abs_rank_shift'])

    # 7. Calculate Mean Rank Shift (overall)
    mean_shift = df['rank_shift'].mean()
    logger.info(f"Overall Mean Rank Shift: {mean_shift:.4f}")

    # 8. Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Rank shift results saved to {output_path}")

    return df

if __name__ == "__main__":
    main()
