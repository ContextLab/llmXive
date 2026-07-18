import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from sklearn.inspection import permutation_importance
from scipy.stats import pearsonr
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd

from config import load_paths
from utils.logging import get_logger

logger = get_logger(__name__)

def load_models(models_path: str) -> Tuple[Any, Any]:
    """Load trained models from the pickle file."""
    with open(models_path, 'rb') as f:
        models = pickle.load(f)
    return models['rf'], models['gb']

def load_feature_names(data_path: str) -> List[str]:
    """Load feature names from the processed dataset."""
    df = pd.read_csv(data_path)
    # Exclude target and non-feature columns if any (assuming 'formation_energy' is target)
    feature_cols = [col for col in df.columns if col != 'formation_energy']
    return feature_cols

def extract_rf_importances(model: Any, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importances from the Random Forest model."""
    importances = model.feature_importances_
    return {name: float(imp) for name, imp in zip(feature_names, importances)}

def calculate_permutation_importance(model: Any, X: Any, y: Any, feature_names: List[str], n_repeats: int = 10, random_state: int = 42) -> Dict[str, float]:
    """Calculate permutation importance for the model."""
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, n_jobs=-1)
    return {name: float(imp) for name, imp in zip(feature_names, result.importances_mean)}

def validate_correlation(rf_importances: Dict[str, float], perm_importances: Dict[str, float]) -> float:
    """Calculate correlation between RF and Permutation importances."""
    common_features = set(rf_importances.keys()) & set(perm_importances.keys())
    if not common_features:
        logger.warning("No common features found for correlation calculation.")
        return 0.0
    
    rf_vals = [rf_importances[f] for f in common_features]
    perm_vals = [perm_importances[f] for f in common_features]
    
    r, _ = pearsonr(rf_vals, perm_vals)
    return float(r)

def rank_features(rf_importances: Dict[str, float], perm_importances: Dict[str, float], top_n: int = 10) -> List[Dict[str, Any]]:
    """Rank features based on RF importance and include permutation importance."""
    # Create a combined dataframe for ranking
    features = list(rf_importances.keys())
    data = {
        'feature': features,
        'rf_importance': [rf_importances[f] for f in features],
        'perm_importance': [perm_importances.get(f, 0.0) for f in features]
    }
    df = pd.DataFrame(data)
    
    # Sort by RF importance descending
    df_sorted = df.sort_values(by='rf_importance', ascending=False)
    
    # Select top N
    top_features = df_sorted.head(top_n).to_dict(orient='records')
    
    # Format output
    ranked_list = []
    for i, row in enumerate(top_features):
        ranked_list.append({
            'rank': i + 1,
            'feature': row['feature'],
            'rf_importance': row['rf_importance'],
            'perm_importance': row['perm_importance']
        })
    
    return ranked_list

def calculate_vif(X: pd.DataFrame, feature_names: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    # Add constant for intercept
    X_with_const = X.copy()
    X_with_const['const'] = 1.0
    
    vif_data = {}
    for i, col in enumerate(feature_names):
        if col in X_with_const.columns:
            vif = variance_inflation_factor(X_with_const.values, i+1) # +1 because of const column
            vif_data[col] = float(vif)
        
    return vif_data

def main():
    """Main entry point for feature importance analysis."""
    paths = load_paths()
    models_path = paths['models_output']
    data_path = paths['processed_descriptors']
    output_dir = paths['evaluation_dir']
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load models
    logger.info(f"Loading models from {models_path}")
    rf_model, gb_model = load_models(models_path)
    
    # Load data and features
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    feature_cols = [col for col in df.columns if col != 'formation_energy']
    X = df[feature_cols]
    y = df['formation_energy']
    
    # Extract RF importances
    logger.info("Extracting RF importances...")
    rf_importances = extract_rf_importances(rf_model, feature_cols)
    
    # Calculate permutation importances
    logger.info("Calculating permutation importances...")
    perm_importances = calculate_permutation_importance(rf_model, X, y, feature_cols)
    
    # Validate correlation
    logger.info("Validating correlation between methods...")
    correlation = validate_correlation(rf_importances, perm_importances)
    logger.info(f"Correlation (r) between RF and Permutation importance: {correlation:.4f}")
    
    # Rank features
    logger.info("Ranking features...")
    ranked_features = rank_features(rf_importances, perm_importances, top_n=10)
    
    # Save permutation importance details
    perm_output_path = os.path.join(output_dir, 'permutation_importance.json')
    with open(perm_output_path, 'w') as f:
        json.dump({
            'correlation_r': correlation,
            'permutation_scores': perm_importances,
            'rf_scores': rf_importances
        }, f, indent=2)
    logger.info(f"Saved permutation importance to {perm_output_path}")
    
    # Save feature ranking
    ranking_output_path = os.path.join(output_dir, 'feature_ranking.json')
    with open(ranking_output_path, 'w') as f:
        json.dump({
            'top_features': ranked_features,
            'total_features': len(feature_cols),
            'correlation_r': correlation
        }, f, indent=2)
    logger.info(f"Saved feature ranking to {ranking_output_path}")
    
    # Calculate VIF (Diagnostic)
    logger.info("Calculating VIF scores...")
    vif_scores = calculate_vif(X, feature_cols)
    vif_output_path = os.path.join(output_dir, 'vif_scores.json')
    with open(vif_output_path, 'w') as f:
        json.dump(vif_scores, f, indent=2)
    logger.info(f"Saved VIF scores to {vif_output_path}")
    
    # Check for high VIF
    high_vif = {k: v for k, v in vif_scores.items() if v > 10}
    if high_vif:
        logger.warning(f"High VIF detected for features: {list(high_vif.keys())}")
    else:
        logger.info("No features with VIF > 10 detected.")

if __name__ == "__main__":
    main()
