import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def load_trained_model(model_path: str) -> RandomForestRegressor:
    """Load the trained Random Forest model from disk."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def extract_feature_importance(model: RandomForestRegressor, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance scores from the trained model."""
    importances = model.feature_importances_
    return {name: float(imp) for name, imp in zip(feature_names, importances)}

def save_importance_results(results: Dict[str, Any], output_path: str) -> None:
    """Save feature importance results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Feature importance results saved to {output_path}")

def run_permutation_importance(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray, 
                               feature_names: List[str], n_repeats: int = 10, 
                               random_state: int = 42) -> Dict[str, float]:
    """Run permutation importance on the model."""
    result = permutation_importance(model, X, y, n_repeats=n_repeats, 
                                    random_state=random_state, n_jobs=-1)
    importance_scores = {}
    for name, score in zip(feature_names, result.importances_mean):
        importance_scores[name] = float(score)
    return importance_scores

def run_importance_analysis(model_path: str, data_path: str, output_path: str) -> Dict[str, Any]:
    """Run full importance analysis including model extraction and permutation importance."""
    config = get_config()
    model = load_trained_model(model_path)
    
    # Load data
    df = pd.read_csv(data_path)
    # Assuming ILR transformed columns are present
    ilr_cols = [col for col in df.columns if col.startswith('ilr_')]
    X = df[ilr_cols].values
    y = df['poissons_ratio'].values
    
    model_importance = extract_feature_importance(model, ilr_cols)
    perm_importance = run_permutation_importance(model, X, y, ilr_cols)
    
    results = {
        'model_importance': model_importance,
        'permutation_importance': perm_importance,
        'feature_names': ilr_cols
    }
    
    save_importance_results(results, output_path)
    return results

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for given features."""
    vif_data = {}
    for col in feature_cols:
        if col in df.columns:
            vif = variance_inflation_factor(df[feature_cols].values, feature_cols.index(col))
            vif_data[col] = float(vif)
        else:
            logger.warning(f"Column {col} not found in dataframe for VIF calculation")
    return vif_data

def save_vif_results(vif_results: Dict[str, float], output_path: str) -> None:
    """Save VIF results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(vif_results, f, indent=2)
    logger.info(f"VIF results saved to {output_path}")

def rank_and_compare_importance(importance_results: Dict[str, Any]) -> List[Tuple[str, float, float]]:
    """Rank features by importance and compare model vs permutation importance."""
    model_imp = importance_results['model_importance']
    perm_imp = importance_results['permutation_importance']
    
    ranked = []
    for feature in model_imp.keys():
        ranked.append((feature, model_imp[feature], perm_imp.get(feature, 0.0)))
    
    # Sort by model importance descending
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked

def save_ranking_results(ranked: List[Tuple[str, float, float]], output_path: str) -> None:
    """Save ranked importance results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [{'feature': f, 'model_importance': m, 'permutation_importance': p} for f, m, p in ranked]
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Ranked importance results saved to {output_path}")

def main():
    """Main entry point for running the analysis pipeline."""
    config = get_config()
    model_path = config.models_dir / 'rf_model.pkl'
    data_path = config.data_dir / 'processed' / 'filtered_alloys.csv'
    
    if not data_path.exists():
        raise FileNotFoundError(f"Required data file not found: {data_path}")
    
    if not model_path.exists():
        raise FileNotFoundError(f"Required model file not found: {model_path}")
    
    # Run importance analysis
    importance_path = config.data_dir / 'outputs' / 'feature_importance.json'
    importance_results = run_importance_analysis(str(model_path), str(data_path), str(importance_path))
    
    # Calculate VIF
    df = pd.read_csv(data_path)
    raw_features = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    vif_results = calculate_vif(df, raw_features)
    vif_path = config.data_dir / 'outputs' / 'vif_results.json'
    save_vif_results(vif_results, str(vif_path))
    
    # Rank and compare
    ranked = rank_and_compare_importance(importance_results)
    ranking_path = config.data_dir / 'outputs' / 'importance_ranking.json'
    save_ranking_results(ranked, str(ranking_path))
    
    logger.info("Analysis pipeline completed successfully")
    print(f"Feature importance saved to: {importance_path}")
    print(f"VIF results saved to: {vif_path}")
    print(f"Ranked results saved to: {ranking_path}")

if __name__ == "__main__":
    main()