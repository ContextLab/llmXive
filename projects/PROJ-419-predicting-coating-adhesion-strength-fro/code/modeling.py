import os
import sys
import logging
import numpy as np
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, make_scorer
from sklearn.preprocessing import StandardScaler
import shap
from scipy.stats import spearmanr

# Import from utils if needed, though mostly standard lib and sklearn here
# from utils import check_memory_limit, RuntimeMonitor

logger = logging.getLogger(__name__)

# --- Data Loading ---
def load_processed_data(filepath: str = "data/processed/coating_adhesion_dataset.csv") -> pd.DataFrame:
    """Load the processed dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    return pd.read_csv(filepath)

# --- Model Training ---
def train_gradient_boosting(X: np.ndarray, y: np.ndarray, cv_folds: int = 5) -> Tuple[GradientBoostingRegressor, Dict]:
    """Train a Gradient Boosting Regressor with nested CV."""
    logger.info("Training Gradient Boosting Regressor...")
    
    # Simple hyperparameter grid for speed
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5],
        'learning_rate': [0.05, 0.1]
    }
    
    base_model = GradientBoostingRegressor(random_state=42)
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        base_model, param_grid, cv=inner_cv, scoring='r2', n_jobs=-1
    )
    
    # Outer CV
    outer_cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    scores = cross_val_score(grid_search, X, y, cv=outer_cv, scoring='r2')
    
    # Fit on full data with best params
    grid_search.fit(X, y)
    best_model = grid_search.best_estimator_
    
    results = {
        'mean_r2': float(np.mean(scores)),
        'std_r2': float(np.std(scores)),
        'best_params': grid_search.best_params_,
        'model': best_model
    }
    
    logger.info(f"Gradient Boosting R2: {results['mean_r2']:.4f} (+/- {results['std_r2']:.4f})")
    return best_model, results

def train_random_forest(X: np.ndarray, y: np.ndarray, cv_folds: int = 5) -> Tuple[RandomForestRegressor, Dict]:
    """Train a Random Forest Regressor with nested CV."""
    logger.info("Training Random Forest Regressor...")
    
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5]
    }
    
    base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        base_model, param_grid, cv=inner_cv, scoring='r2', n_jobs=-1
    )
    
    outer_cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    scores = cross_val_score(grid_search, X, y, cv=outer_cv, scoring='r2')
    
    grid_search.fit(X, y)
    best_model = grid_search.best_estimator_
    
    results = {
        'mean_r2': float(np.mean(scores)),
        'std_r2': float(np.std(scores)),
        'best_params': grid_search.best_params_,
        'model': best_model
    }
    
    logger.info(f"Random Forest R2: {results['mean_r2']:.4f} (+/- {results['std_r2']:.4f})")
    return best_model, results

# --- SHAP Analysis (T036 Implementation) ---
def compute_shap_values(model, X: np.ndarray, feature_names: List[str], top_k: int = 10) -> Tuple[pd.DataFrame, Dict]:
    """
    Compute SHAP values for top features.
    
    Args:
        model: Trained sklearn model
        X: Feature matrix
        feature_names: List of feature names corresponding to X columns
        top_k: Number of top features to report
        
    Returns:
        Tuple of (DataFrame of top SHAP summary, Dict of full results)
    """
    logger.info(f"Computing SHAP values for top {top_k} features...")
    
    # Initialize SHAP explainer
    # Use TreeExplainer for tree-based models for speed and accuracy
    if hasattr(model, 'feature_importances_'):
        explainer = shap.TreeExplainer(model)
    else:
        # Fallback for non-tree models (slower)
        explainer = shap.KernelExplainer(model.predict, X[:100]) # Sample for kernel
    
    shap_values = explainer.shap_values(X)
    
    # Handle output shape for regression (usually 1D array of values)
    if isinstance(shap_values, list):
        shap_values = shap_values[0] # Some models return list of arrays
        
    # Create a DataFrame for easier analysis
    shap_df = pd.DataFrame(shap_values, columns=feature_names)
    
    # Calculate mean absolute SHAP values for ranking
    mean_abs_shap = shap_df.abs().mean()
    top_features = mean_abs_shap.nlargest(top_k).index.tolist()
    
    # Create summary dataframe
    summary_data = {
        'feature': top_features,
        'mean_abs_shap': mean_abs_shap[top_features].values,
        'rank': range(1, len(top_features) + 1)
    }
    summary_df = pd.DataFrame(summary_data)
    
    # Save full SHAP values to disk for later use (optional but good practice)
    # We save the top_k summary as requested by the task description
    output_path = "data/processed/shap_top_features.csv"
    summary_df.to_csv(output_path, index=False)
    logger.info(f"SHAP top features saved to {output_path}")
    
    results = {
        'top_features': top_features,
        'mean_abs_shap_values': mean_abs_shap[top_features].to_dict(),
        'summary_df': summary_df,
        'full_shap_values': shap_values # Keep in memory or save separately if large
    }
    
    return summary_df, results

# --- Permutation Importance (T037 Placeholder Logic) ---
def compute_permutation_importance(model, X: np.ndarray, y: np.ndarray, feature_names: List[str], top_k: int = 10) -> Tuple[pd.DataFrame, Dict]:
    """Compute permutation importance."""
    logger.info("Computing permutation importance...")
    from sklearn.inspection import permutation_importance
    
    result = permutation_importance(model, X, y, n_repeats=10, random_state=42, n_jobs=-1)
    perm_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': result.importances_mean
    }).sort_values('importance', ascending=False)
    
    top_perm = perm_importance.head(top_k)
    output_path = "data/processed/permutation_importance.csv"
    top_perm.to_csv(output_path, index=False)
    
    return top_perm, {'summary': top_perm, 'full': perm_importance}

# --- Feature Ranking & Correlation (T038, T039) ---
def rank_features(shap_summary: pd.DataFrame, perm_summary: pd.DataFrame) -> pd.DataFrame:
    """Rank features distinguishing compositional vs surface categories."""
    # Merge rankings
    merged = pd.merge(
        shap_summary[['feature', 'rank']].rename(columns={'rank': 'shap_rank'}),
        perm_summary[['feature', 'importance']].rename(columns={'importance': 'perm_score'}),
        on='feature',
        how='outer'
    )
    return merged

def calculate_spearman_correlation(shap_rankings: List[float], perm_rankings: List[float]) -> float:
    """Calculate Spearman correlation between SHAP and permutation rankings."""
    if len(shap_rankings) != len(perm_rankings):
        raise ValueError("Rankings must be of equal length")
    corr, _ = spearmanr(shap_rankings, perm_rankings)
    return float(corr)

def distinguish_feature_categories(df: pd.DataFrame, feature_name: str) -> str:
    """Distinguish feature categories (Compositional vs Surface)."""
    # Heuristic based on naming conventions if not explicitly tagged
    name_lower = feature_name.lower()
    if any(x in name_lower for x in ['atomic', 'radius', 'crosslink', 'composition', 'element']):
        return 'Compositional'
    elif any(x in name_lower for x in ['roughness', 'rms', 'skew', 'kurt', 'surface', 'metrology']):
        return 'Surface'
    else:
        return 'Unknown'

# --- Pipeline Orchestration ---
def run_modeling_pipeline(data_path: str = "data/processed/coating_adhesion_dataset.csv") -> Dict[str, Any]:
    """Run the full modeling pipeline including SHAP analysis."""
    logger.info("Starting modeling pipeline...")
    
    # Load Data
    df = load_processed_data(data_path)
    
    # Assume target is 'adhesion_strength' and features are everything else
    # In a real scenario, we'd use the preprocessed columns from T029/T030
    target_col = 'adhesion_strength'
    if target_col not in df.columns:
        # Fallback if column name differs
        target_col = df.select_dtypes(include=[np.number]).columns[-1]
        
    X = df.drop(columns=[target_col]).select_dtypes(include=[np.number])
    y = df[target_col]
    feature_names = X.columns.tolist()
    
    X = X.values
    y = y.values
    
    # Train Models
    gb_model, gb_results = train_gradient_boosting(X, y)
    rf_model, rf_results = train_random_forest(X, y)
    
    # Compute SHAP (T036)
    shap_summary, shap_results = compute_shap_values(
        gb_model, X, feature_names, top_k=10
    )
    
    # Compute Permutation Importance (T037)
    perm_summary, perm_results = compute_permutation_importance(
        gb_model, X, y, feature_names, top_k=10
    )
    
    # Correlation (T039)
    shap_ranks = shap_summary['rank'].tolist()
    # Map perm summary to same order as shap summary for correlation
    perm_ranks = []
    for feat in shap_summary['feature']:
        row = perm_summary[perm_summary['feature'] == feat]
        if not row.empty:
            # Rank in perm summary (1 is best)
            rank = perm_summary[perm_summary['feature'] == feat].index[0] + 1
            perm_ranks.append(rank)
        else:
            perm_ranks.append(len(feature_names) + 1)
    
    spearman_corr = calculate_spearman_correlation(shap_ranks, perm_ranks)
    
    # Distinguish Categories (T038)
    shap_summary['category'] = shap_summary['feature'].apply(lambda x: distinguish_feature_categories(df, x))
    
    final_report = {
        'gradient_boosting': gb_results,
        'random_forest': rf_results,
        'shap_top_features': shap_summary.to_dict(orient='records'),
        'spearman_correlation': spearman_corr,
        'feature_categories': shap_summary[['feature', 'category']].to_dict(orient='records')
    }
    
    # Save final report
    report_path = "state/modeling_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    
    logger.info(f"Modeling pipeline complete. Report saved to {report_path}")
    return final_report

def main():
    """Main entry point for modeling module."""
    logging.basicConfig(level=logging.INFO)
    try:
        run_modeling_pipeline()
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()